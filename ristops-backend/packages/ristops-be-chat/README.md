# ristops-be-chat

Chat service for the AI assistant. Owns conversations (chats, messages, pending actions),
builds an agent from `ristops-lib-agent`, runs each turn and streams its events to the BFF.

Status: bootstrapped, not implemented yet. See the
[AI assistant design](https://pcrt1697.github.io/ristops/#/design/ai-assistant).

[Full documentation](https://pcrt1697.github.io/ristops/#/services/be-chat)

## Dependencies

`ristops-lib-core`, `ristops-lib-otel`, `ristops-lib-be`, `ristops-lib-sql`, `ristops-lib-agent`
