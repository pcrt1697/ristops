# ristops-lib-redis

Redis client and stream consumer.

> Source: [ristops-lib-redis](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-redis/README.md)

## Stream consumer

This module addresses reliable, at-least-once message processing over Redis Streams. Rather than
a simple pub/sub model, it uses consumer groups so that messages are not lost if a consumer
crashes mid-processing. Each iteration of the consumer loop:

1. Reclaims messages stuck in-flight from crashed workers via `XAUTOCLAIM`
2. Reads new messages via `XREADGROUP`
3. For each message: resets `APP_CONTEXT`, restores `correlation_id` from the payload, calls
   the handler, and acknowledges via `XACK` only on success

Errors are caught per-message so a single failure does not stop the loop. Processing within a
consumer is sequential, which keeps the ordering guarantee of Redis Streams intact.

`CompositeRedisConsumer` manages multiple consumers as a single unit, starting and stopping
them together:

```python
consumer = RedisStreamConsumer.create_composite(
    redis_client,
    (UserConsumerSettings.get(), on_user_event),
    (ResourceConsumerSettings.get(), on_resource_event),
)
await consumer.start()
```

## Trace and correlation ID propagation

At the start of each message, the consumer calls `APP_CONTEXT.reset()` to clear any leftover
state from the previous iteration. It then extracts a W3C `traceparent` from the message payload
— set by the producer via `BaseEvent` (`ristops-lib-be`) — and opens its processing span inside
that trace context, so the consumer-side span belongs to the *same* trace as the request that
published the message rather than starting a disconnected one. `correlation_id` (the trace ID) is
restored into `APP_CONTEXT` the same way, so it is available in the consumer's log lines with no
manual wiring in handler code. Both are absent from the payload, and this is a no-op, when the
producing service had telemetry disabled.

## Types

```python
StreamPayload = dict[str, Any]
MessageProcessor = Callable[[str, StreamPayload], Awaitable[None]]
```
