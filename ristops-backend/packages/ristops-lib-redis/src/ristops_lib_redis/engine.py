import asyncio
import logging
from asyncio import Lock, Task
from typing import Any, Callable, Awaitable, Protocol

from opentelemetry import metrics, trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from redis import ResponseError
from redis.asyncio import Redis

from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.tracing import get_trace_id
from ristops_lib_redis.exception import RedisClientError
from ristops_lib_redis.settings import RedisSettings

_logger = logging.getLogger(__name__)

# a trace normally dies at a queue boundary: the producer's HTTP request span ends long before a
# consumer picks the message up. BaseEvent (ristops_lib_be.events) injects a W3C traceparent into
# every event payload on publish; extracting it here and starting the consumer span inside that
# context continues the *same* trace instead of starting a new, disconnected one.
_tracer = trace.get_tracer(__name__)
_propagator = TraceContextTextMapPropagator()

# a failed message never produces an HTTP response, so it is invisible to the HTTP RED metrics
# FastAPI instrumentation emits — this counter is the only queryable "number of errors" signal for
# work that happens outside a request. A no-op instrument with no MeterProvider configured.
_meter = metrics.get_meter(__name__)
_consumer_errors = _meter.create_counter(
    "messaging.consumer.errors",
    unit="1",
    description="Stream messages that raised while processing, by stream and consumer group.",
)

StreamPayload = dict[str, Any]
RedisStream = tuple[str, StreamPayload]
MessageProcessor = Callable[[str, StreamPayload], Awaitable[None]]


class RedisClient:

    def __init__(self):
        self._redis: Redis | None = None
        self._lock = Lock()

    async def connect(self, settings: RedisSettings = None):
        async with self._lock:
            if self._redis is not None:
                raise RedisClientError("Redis client already connected")
            settings = settings or RedisSettings.get()
            self._redis = Redis.from_url(settings.url, decode_responses=True)

    async def disconnect(self):
        async with self._lock:
            if self._redis is not None:
                await self._redis.aclose()
                self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            raise RedisClientError(f"Redis client not connected")
        return self._redis


class RedisStreamConsumer:

    def __init__(
            self,
            client: RedisClient,
            config: RedisConsumerConfiguration,
            consumer_func: MessageProcessor,
    ):
        self._client = client
        self._config = config
        self._do_process_message = consumer_func
        self.__task: Task[None] | None = None

    @property
    def config(self) -> RedisConsumerConfiguration:
        return self._config

    @property
    def _task(self) -> Task[None]:
        if self.__task is None:
            raise RedisClientError("Consumer loop not started")
        return self.__task

    async def _run(self):
        """ Starts the consumer loop. """
        await self._ensure_consumer_group()
        while True:
            try:
                await self._process_stale_messages()
                stream_result = await self._read_stream()
                if not stream_result:
                    continue
                for _stream_key, messages in stream_result:
                    await self._process_messages(messages)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _logger.exception(f"Consume loop error: {e}")
                await asyncio.sleep(1)

    async def start(self) -> None:
        if self.__task is not None:
            raise RedisClientError("Consumer loop already started")
        self.__task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self.__task is None:
            return None
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def _ensure_consumer_group(self):
        try:
            await self._client.redis.xgroup_create(self._config.stream, self._config.group, id="0", mkstream=True)
        except ResponseError as e:
            if not e.args[0].startswith("BUSYGROUP"):
                raise

    async def _process_message(self, stream_id: str, data: StreamPayload) -> None:
        APP_CONTEXT.reset()
        # extracts "traceparent" from the payload if present, yielding a context that carries the
        # producer's span as parent; absent (or telemetry disabled end to end) it's an empty
        # context and the span below simply starts its own trace
        parent_context = _propagator.extract(carrier=data)
        with _tracer.start_as_current_span(
                f"redis.consume {self._config.stream}",
                context=parent_context,
                kind=SpanKind.CONSUMER,
                attributes={
                    "messaging.system": "redis",
                    "messaging.destination.name": self._config.stream,
                    "messaging.consumer.group.name": self._config.group,
                },
        ):
            correlation_id = get_trace_id() or data.get(ContextKey.CORRELATION_ID)
            if correlation_id:
                APP_CONTEXT.set(ContextKey.CORRELATION_ID, correlation_id)
            _extra = {"redis_stream_id": stream_id}
            if self._config.log_payload:
                _logger.info("Processing message: %s", data, extra=_extra)
            else:
                _logger.info("Processing message", extra=_extra)
            try:
                await self._do_process_message(stream_id, data)
            except Exception as e:
                # logged here, still inside the span, so the line carries trace_id/correlation_id
                # like every other log for this message — logging it one level up in
                # _process_messages happens after this span has already closed, losing that link.
                # The span itself is already marked ERROR by start_as_current_span's default
                # exception recording; re-raising lets _process_messages record the failure metric.
                _logger.exception(f"Error processing stream {stream_id}: {e}", extra=_extra)
                raise
            _logger.info("Successfully processed message", extra=_extra)
            await self._client.redis.xack(self._config.stream, self._config.group, stream_id)

    async def _process_messages(self, messages: list[RedisStream]):
        """ Process a batch of messages. """
        for stream_id, data in messages:
            try:
                await self._process_message(stream_id, data)
            except Exception:
                # a failure here never produces an HTTP response, so this counter is the only
                # metrics-based "number of errors" signal for it; the log line and span status
                # are already recorded inside _process_message, above
                _consumer_errors.add(1, {
                    "messaging.destination.name": self._config.stream,
                    "messaging.consumer.group.name": self._config.group,
                })

    async def _process_stale_messages(self) -> None:
        """ Reclaim and process messages stuck in-flight (other crashed workers). """
        # (next_start_id, [(id, fields), ...], [deleted_ids])
        claimed = await self._client.redis.xautoclaim(
            self._config.stream,
            self._config.group,
            self._config.name,
            min_idle_time=self._config.retry_idle_ms,
            count=self._config.batch_size,
        )
        stale_messages = claimed[1]
        await self._process_messages(stale_messages)

    async def _read_stream(self) -> tuple[str, list[RedisStream]]:
        """ Read a batch of messages. """
        return await self._client.redis.xreadgroup(
            self._config.group,
            self._config.name,
            {self._config.stream: ">"},  # reads messages not yet delivered to any consumer
            count=self._config.batch_size,
            block=self._config.wait_ms,
        )

    @classmethod
    def create_composite(
            cls,
            client: RedisClient,
            *consumers: tuple[RedisConsumerConfiguration, MessageProcessor],
    ):
        return CompositeRedisConsumer(
            *(
                RedisStreamConsumer(client, config, processor)
                for config, processor in consumers
            )
        )


class CompositeRedisConsumer:

    def __init__(self, *consumers: RedisConsumer):
        self._consumers = consumers

    async def start(self):
        for i, consumer in enumerate(self._consumers):
            try:
                await consumer.start()
            except Exception:
                _logger.exception("Failed to start consumer %s", consumer.config)
                await asyncio.gather(
                    *[c.stop() for c in self._consumers[:i]],
                    return_exceptions=True,
                )
                raise
        _logger.info("Successfully started loop for %s consumers", len(self._consumers))

    async def stop(self):
        num_stopped = 0
        for i, consumer in enumerate(self._consumers):
            try:
                await consumer.stop()
                num_stopped += 1
            except Exception:
                _logger.exception("Failed to stop consumer %s", consumer.config)
        _logger.info("Stopped %s out of %s consumers", num_stopped, len(self._consumers))


class RedisConsumer(Protocol):
    config: RedisConsumerConfiguration

    async def start(self) -> None:
        ...

    async def stop(self) -> None:
        ...


class RedisConsumerConfiguration(Protocol):
    stream: str
    group: str
    name: str
    wait_ms: int
    retry_idle_ms: int
    batch_size: int
    log_payload: bool


redis_client = RedisClient()
