# ristops-lib-agent

Stateless agent runtime: a tool loop over an LLM (LiteLLM) with HTTP tools generated from the
OpenAPI schemas of domain services. Given a configuration, a message history, a context and the
user's token, it yields a stream of typed events. It has no database and no chat concepts, so a
service, a batch job or a test can embed it.

Status: bootstrapped, not implemented yet. See the
[AI assistant design](https://pcrt1697.github.io/ristops/#/design/ai-assistant).

[Full documentation](https://pcrt1697.github.io/ristops/#/libraries/lib-agent)

## Dependencies

`pydantic`, `pyyaml`, `litellm`
