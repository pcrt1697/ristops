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

## Correlation ID propagation

At the start of each message, the consumer calls `APP_CONTEXT.reset()` to clear any leftover
state from the previous iteration, then restores `correlation_id` from the message payload.
This means the trace context set by the original HTTP request — which published the message — is
available in the consumer's log lines without any manual wiring in the handler code.

## Types

```python
StreamPayload = dict[str, Any]
MessageProcessor = Callable[[str, StreamPayload], Awaitable[None]]
```
