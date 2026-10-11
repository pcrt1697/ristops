# ristops-lib-agent

Stateless agent runtime: a tool loop over an LLM (LiteLLM) with HTTP tools generated from the
OpenAPI schemas of domain services. Given a configuration, a message history, a context and the
user's token, it yields a stream of typed events. It has no database and no chat concepts, so any
service, batch job or test can embed it.

> Source: [ristops-lib-agent](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-agent/README.md)

**Status:** bootstrapped, not implemented yet. The design is a draft in
[AI assistant design](../design/ai-assistant.md); this page will describe the library once it is
built.
