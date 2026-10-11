# AI assistant

**Status:** draft, design agreed in discussion, nothing implemented. To be converted into the service, library and
architecture pages once built.

## Goal

A chat, openable from a floating button on every page, through which a user operates the app in natural language. The
chat is scoped to the currently selected venue.

The set of operations is a deliberate perimeter. Today it is the reservation domain only:

- add a reservation;
- update a reservation status;
- query reservations (free seats on a date, when a customer last booked, and similar);
- add a service closing or an extra opening.

Out of scope: authorization writes (adding a user to a venue), authorization checks, venue writes (closing a venue).
Staff shifts, menu and order management are expected later.

Hard requirements:

- Every call runs on behalf of the user (OBO). The assistant never has more rights than the user.
- Every write, update or delete needs an explicit confirmation in the frontend.
- No RAG for now.

## Decisions

| Topic | Decision | Reason |
|---|---|---|
| Agent runtime | A library, `ristops-lib-agent`, configured by its host | The dependency direction is enforced by packaging; any service or job can embed it; no chat concept can leak in |
| Service | `be-chat`, which owns chats and configures an agent from the library | Chat storage and orchestration are one domain; the agent is a dependency, not a peer |
| Agent contract | Stateless: messages and context in, a stream of typed events out. No database | The agent can run with no chat at all: a batch job, a test, another front end |
| Agent configuration | YAML for prompt, model, limits and tools | Prompts, models and the tool perimeter are versioned files, reviewed together and changed without touching code |
| Tool exposure | HTTP tools: existing REST endpoints called directly by the agent | Simplest option: no new deployable, no change to domain services, authorization unchanged |
| Tool definition | Generated from the domain service's committed OpenAPI schema, with an allowlist and per-tool adjustments in the YAML | The REST API already carries filters, descriptions and schemas; hand-written tools would duplicate the contract |
| Tool names | Namespaced by domain, e.g. `reservation.create` | Cheap now, avoids a rename when domains multiply |
| Parallel tool calls | Disabled; the prompt asks the model to work on one task at a time | A model message carries at most one call, so pausing on a write never leaves other calls of the same message without a result |
| Response format | Free text, streamed; control signals are typed events | Streams word by word; the confirmation travels as an event, not inside the text |
| Transport | `POST` returning Server-Sent Events, proxied by the BFF | Industry standard for chats; reuses cookie session and HTTP middleware |
| Chat storage | PostgreSQL, JSONB message content | Messages are relational (chat, order, cascade); volume is small; tooling exists |
| LLM layer | LiteLLM with a hand-written tool loop | Provider agnostic, no pay-per-token lock-in; full control of suspend and resume |
| Auth | Pass-through of the user JWT first, token exchange later | Authorization stays enforced by the existing services |
| Agents | One agent: a single tool loop | The loop already plans across several model calls; no routing until a second domain exists |

Rejected or deferred, with the reason:

- **An MCP endpoint inside each domain service.** It couples domain services to the AI feature (a tool decorator on
  routes, an MCP dependency, integrating FastMCP with FastAPI), and the descriptions and perimeter seen by the model are
  agent concerns, not domain ones.
- **An MCP server per domain, deployed separately from the domain service.** It gives the agent-facing API a dedicated
  owner, at the cost of one deployable per domain. Deferred: the tool configuration has the same shape either way, so
  it can move into such a server when a second consumer or a stricter ownership boundary needs it.
- **A single MCP gateway for all domains.** One deployable touched by every domain, and MCP only pays off with several
  consumers.
- **Hand-written tools.** They duplicate the REST contract and drift from it. A question the model cannot answer is
  fixed in the REST API first, which serves the UI too.
- **Websockets.** Bidirectional, but the session middleware stack is `BaseHTTPMiddleware` and does not run for websocket
  scopes, auth happens once at connect, and nothing in the requirements needs server push or mid-turn steering.
- **GraphQL subscriptions.** They fit "notify me when X changes", not a request that streams one answer. They would also
  bring websockets back. They remain a candidate for live boards (orders), as a separate feature.
- **A dedicated chat edge service with a session library.** Only justified with websockets; with SSE the BFF can proxy.
- **A separate `be-agent` service.** It would add a deployable and a second streaming hop for no current caller. The
  library gives the same decoupling, and a service can wrap it later if a network caller needs one.
- **An `agent` domain inside the chat service.** The boundary would rest on an import-lint rule instead of on package
  dependencies.
- **Multiple agents (planner, executor, responder).** The tool loop already makes several model calls per turn, so one
  agent covers understanding the request, querying for context and answering or preparing a confirmation. Splitting by
  step adds latency, tokens and information loss. Multiple agents become useful with several domains or a large toolset.
- **Additional local tools.** The configuration leaves room for plain Python tools next to HTTP tools, but nothing needs
  them yet.
- **Structured output for the whole response.** It conflicts with streaming text and is not needed for confirmations.
  It may return later as an optional per-agent setting for non-chat callers.
- **MongoDB.** No benefit over JSONB at this scale, and a new database means a new library and operational story.
- **LangChain or LangGraph.** Its checkpointer would duplicate the chat store and conflicts with a stateless agent. To
  be reconsidered if multi-agent routing becomes real.
- **A classifier in front of specialized models.** Nothing to route with one domain. Revisit with a second domain.
- **Exposing every endpoint as a tool.** Too many tools degrades selection accuracy and widens the prompt-injection
  surface.

## Concepts

- **Message.** One item in a conversation: the user's text, an assistant tool call, a tool result, or an assistant
  answer.
- **Model call.** One request to the LLM.
- **Turn.** Everything from one user message until the agent hands control back, either with the final answer or by
  pausing for a confirmation. A turn can contain several model calls, since the model may ask for a tool, read its
  result and ask for another.
- **Segment.** The part of a turn between pauses. A write pauses the turn: the first segment ends with a confirmation
  request, and after the user answers, the second segment continues from the stored history.

For example, "how many free seats on 12 Oct at dinner?" is one turn with two model calls and four messages:

```text
user       "How many free seats on 12 Oct at dinner?"
assistant  tool_call: reservation.calendar(date=12 Oct)
tool       result: {capacity: 40, booked: 28, ...}
assistant  "12 free seats."
```

### History

An LLM has no memory between requests, so every model call carries the whole conversation: the system prompt, the tool
definitions and every earlier message, including tool calls and their results.

- `be-chat` stores messages in the OpenAI message format used by LiteLLM, and passes the full history to the agent on
  each turn. The agent adds its own system prompt and tool list.
- Cost grows with conversation length, since each call re-reads everything. Prompt caching lowers it where the provider
  supports it and the start of the prompt stays identical, so history is append-only and earlier messages are not
  rewritten.
- The agent decides what to cut when the history exceeds the model's context window, because it knows the model: it
  drops the oldest messages and truncates large tool results. Summaries, which need persistence, would go through
  `be-chat` later.

## Architecture

```text
browser ──POST /chat/turns (SSE)──► bff-web ──POST + JWT (SSE)──► be-chat ──► ristops-lib-agent ──HTTP + JWT──► be-reservation, ...
   └──GraphQL (list, rename, delete, history)──► bff-web ──REST──► be-chat
                                                                      └──► chat database
```

`ristops-lib-agent` runs inside `be-chat`'s process. It is not a service.

### bff-web

- Keeps GraphQL for everything that is not a live turn: list, rename and delete chats, load history.
- Adds one REST endpoint for a turn. It reads the session, takes the JWT, opens a streaming request to `be-chat` and
  returns what arrives without buffering or interpreting it.
- Closes the upstream request when the browser disconnects, so the turn is cancelled.

### ristops-lib-agent

A stateless runtime. Given a configuration, a history, a context and the user's token, it yields typed events.

- **Interface.** An agent is built from its configuration, and `run(messages, context, user_token, approved_call_ids)`
  returns an async stream of events. It takes plain data in and gives plain data out. It uses no database and has no
  chat concept. The context carries the values tools are bound to, such as the venue ID.
- **Configuration.** A typed object, loaded from a YAML file:
  - the system prompt, the standing instructions for the agent, with variables such as the current date and the venue
    timezone filled in at run time;
  - the model and its settings, with parallel tool calls disabled;
  - per-turn limits;
  - the tools, grouped by domain service (see [Tools](#tools)).

  Secrets such as provider API keys stay in environment settings and never in the YAML.
- **Event types are its contract.** The host depends on them, never the other way round.
- **Tool registry.** Built at startup from the tool configuration and the committed OpenAPI schemas, with LiteLLM
  driving the model.
- **Writes are deny-by-default.** A write tool is never executed during a normal turn. The agent emits a confirmation
  request and ends the stream. It executes a write only when `approved_call_ids` names that exact call in the history.
- **No chat concepts.** It knows nothing about chats, users' chat lists or message storage, and it has no database.

An illustrative configuration; the exact shape is open:

```yaml
name: reservation
model:
  name: <model id>
  temperature: 0
  parallel_tool_calls: false
limits:
  max_iterations: 8
  max_tokens: 4000
  timeout_seconds: 60
prompt: prompts/reservation.md
services:
  - namespace: reservation
    openapi: be-reservation/openapi.json
    base_url: ${RISTOPS_RESERVATION_URL}
    tools:
      - operation: get_reservations
        name: search
        bind:
          filter.venue_id: context.venue_id
        exclude_response_fields: [created_at, updated_at]
      - operation: calendar
        bind:
          venue_id: context.venue_id
      - operation: create
        bind:
          body.venue_id: context.venue_id
      - operation: actions
        name: update_status
```

### be-chat

A domain service on PostgreSQL, built like `be-venue`. It owns everything about conversations and builds its agent
from a configuration file shipped with the service.

- `chat`: id, user id, venue id, title, timestamps. Index on user id and update time.
- `message`: chat id, sequence, role, content as JSONB in the LiteLLM message format, token usage.
- `pending_action`: chat id, call id, tool, frozen arguments, summary, status.
- **Orchestration.** Loads the history, appends the user message, runs the agent, relays the events to the browser and
  persists each completed message, received as a `message` event, and any pending action.
- **Chat endpoints.** List, rename, delete and load history, reached through the BFF's GraphQL.
- **Settings.** The LLM provider keys and defaults, under their own prefix such as `RISTOPS_LLM_`.

### Tools

A tool is an existing REST endpoint of a domain service. Domain services do not change: they know nothing about the
assistant.

- **Source.** Each domain service's OpenAPI schema is generated by a command next to its run command and committed to
  the repository by a pre-commit hook. The agent reads the committed file, so an API change shows up in review as a
  schema diff.
- **Allowlist.** Only the operations listed in the configuration become tools, referenced by `operationId`. Nothing is
  exposed by default.
- **Input schema.** Path and query parameters become top-level arguments; the JSON request body becomes a single `body`
  argument, which keeps discriminated bodies intact.
- **Adjustments.** Per tool, the configuration can set the name, override the description, bind arguments to context
  values and drop response fields. A bound argument is removed from the schema the model sees and filled by the agent,
  so the model cannot act on another venue.
- **Description.** Taken from the operation's docstring and field descriptions, which are therefore written for a
  reader who does not know the code.
- **Kind.** A `GET` is a read; any other method is a write unless the configuration marks it as read.
- **Validation.** At startup the agent fails if a configured operation is missing from the schema or a bound argument
  is missing from the operation.
- **Gaps.** A question the tools cannot answer is fixed by improving the REST API, for example a customer filter on the
  reservation search, which the generated tool then picks up.

## Turn flow

1. The browser sends the message and the current venue to the BFF, which forwards it to `be-chat`.
2. `be-chat` loads the history, appends the user message and runs the agent.
3. The agent adds its system prompt (current date and venue timezone included) and calls the model. For a read tool it
   calls the service with the user's JWT and continues. Each completed message is streamed back as a `message` event and
   persisted by `be-chat`. The answer text arrives as `delta` events, word by word.
4. For a write tool the agent does not execute. It emits `confirmation_request` with the call ID, tool, arguments and a
   readable summary, and ends the stream. In one transaction `be-chat` stores the message and a `pending_action`.
5. The user confirms or rejects with another request that names the pending action. The arguments are the stored ones;
   the client never resends them.
6. On confirmation `be-chat` marks the action `executing` and runs the agent with the call ID in `approved_call_ids`.
   The agent executes that call, feeds the result to the model and streams the rest of the turn. A rejection is
   recorded as a tool result saying the user declined, and the turn continues so the model can respond.

Because the suspended state is in the database, the transport does not matter for correctness, and a reload resumes
cleanly. Confirmation is enforced in code, never by the prompt, and by the component that executes the write.

### Unknown outcomes

The write to a domain service cannot join the chat database's transaction. If the process crashes between executing a
call and recording its result, the outcome is unknown. A `pending_action` therefore moves through `pending`,
`executing`, then `done` or `failed`. An `executing` action is never retried automatically, and the user is told that
the outcome is unknown and should be checked. The pending action's ID can be sent as an idempotency key, which helps
only if the target service honours it.

### Event stream

The answer is free text and streams as it is generated. Everything that is not answer text is a typed event, so the
frontend never parses the text for control information.

| Event | Meaning |
|---|---|
| `delta` | Next piece of the answer |
| `reasoning` | Reasoning text, when the model provides it |
| `tool_call` | A tool is being called, with its namespaced name |
| `message` | A message is complete (assistant answer, tool call or tool result), with its full content in the LiteLLM format; the host persists it |
| `confirmation_request` | A write is waiting for the user |
| `done` | The turn is complete, with token usage |
| `error` | The turn failed |

`message` is meant for the host: `be-chat` persists it and does not need to relay it to the browser, which already has
the same content from `delta` and `tool_call`.

The browser cancels by aborting the request. If the browser disconnects mid-turn the turn is cancelled, and what is
already persisted stays.

## Security

- OBO by pass-through. When a request starts a segment, the BFF reads the JWT from the session, refreshing it first if
  it would expire within the turn timeout, and forwards it to `be-chat`. The agent uses that token for every tool call
  of the segment. The access token lives 15 minutes and a segment is bounded by the turn timeout, so the token stays
  valid; a confirmation starts a new segment with a new token. All access is checked by the existing services.
- The pass-through token can reach every endpoint the user can, so the perimeter rests on the tool allowlist. Planned
  hardening is a token exchange at `be-authn` issuing a short-lived token with an actor claim and a limited scope, so
  that services reject it outside the perimeter and audit logs can tell the assistant from the user. The token is
  obtained through one function, which makes this a local change.
- Customer-controlled text (names, notes) reaches the model through tool results and can carry prompt injection.
  Mitigations are the allowlist, arguments bound to the context and mandatory confirmation of writes.

## Limits

- Per turn, in the agent: maximum tool iterations, maximum tokens, timeout, truncation of large tool results.
- Per user, in `be-chat`: rate limit and daily token budget. Redis counters for the rate limit; usage stored per message
  for budgets. The check happens before the agent runs. The agent reports usage in its events; the budget logic belongs
  to the host.
- Per chat, in `be-chat`: one active turn at a time.

## Observability

OpenTelemetry spans for each model call and each tool call, with token usage and cost as attributes. The BFF to
`be-chat` hop is traced like any other HTTP call.

## Frontend

- A floating button on every page opens the chat, scoped to the current venue from the workspace shell.
- The stream is read with `fetch` and a stream reader, because the browser's `EventSource` supports only `GET`.
- A confirmation card renders the summary of the pending write with confirm and reject buttons.
- The chat list behaves like other chat products: new chat, rename, delete.

## Growth path

Nothing here is built ahead of need.

1. Namespaced tool names, agents as configuration and the library boundary are the only provisions made now.
2. Scope tools by the page the user is on when the tool count grows.
3. Measure tool-selection accuracy on a set of sample requests. If failures show confusion between domains, add agents:
   sub-agents exposed as tools of an orchestrator, one configuration each, with an agent field on events so the
   interface can show which agent acted.
4. Plain Python tools next to HTTP tools, when a caller needs one.
5. An MCP server per domain, holding that domain's tool configuration, when a second consumer or a stricter ownership
   boundary needs it. The agent then reads tools from MCP instead of from the OpenAPI schemas.
6. An optional output schema per agent, for non-chat callers that want structured results.
7. A small service wrapping the library, if a caller outside Python needs the agent over the network.
8. Token exchange for OBO, as above.
9. Live boards (orders) through GraphQL subscriptions or another push channel, as an independent feature.

## Open points

- Behaviour of the stack with streaming: `BaseHTTPMiddleware` has known quirks with streamed responses and client
  disconnects, and `RequestLoggingMiddleware` logs `[AFTER]` when the response starts. To be tested early, possibly
  with pure ASGI middleware for the streaming route.
- No buffering anywhere on the path (`Cache-Control: no-cache`, proxy and compression settings).
- The exact shape of the configuration file and how prompt variables are filled in.
- The exact shape of the agent's event schema, including how a rejection is represented.
- Which model and provider, and whether it handles tool calling reliably and honours disabled parallel tool calls.
  What the agent does when a model returns several calls anyway.
- How `be-chat` packages the committed OpenAPI schemas of the services it calls (each at
  `ristops-backend/packages/<package>/openapi.json`, regenerated by the `export-api-schemas` pre-commit hook).
- Package and service names.
- Cancel on disconnect and approved writes (deferred). If the browser disconnects while an approved write runs,
  cancelling can interrupt the step that records the call's result, which produces an unknown outcome. Proposed:
  protect "execute the approved call and persist its result" from cancellation, and cancel only the model streaming.
  The alternative is to let the whole turn finish after a disconnect.
- Resuming a turn after a reload. Only completed messages are persisted, so a reload mid-turn loses the answer in
  progress. A candidate is to run the turn as a background task that writes its events to a Redis stream, with the SSE
  endpoint reading from it and resuming from `Last-Event-ID`.
