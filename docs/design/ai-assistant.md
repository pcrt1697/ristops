# AI assistant

**Status:** draft, design agreed in discussion on 2026-10-09, nothing implemented. To be converted into the service and
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
| Tool exposure | MCP endpoint on each domain service | Decoupling: the service owns tool mapping and schemas; standard protocol |
| Tool marking | A decorator on the route opts it in | Nothing is exposed by default; the perimeter is explicit |
| Tool names | Namespaced by domain, e.g. `reservation.create` | Cheap now, avoids a rename when domains multiply |
| Transport | `POST` returning Server-Sent Events, proxied by the BFF | Industry standard for chats; reuses cookie session and HTTP middleware |
| Chat storage | PostgreSQL, JSONB message content | Messages are relational (chat, order, cascade); volume is small; tooling exists |
| LLM layer | LiteLLM with a hand-written tool loop | Provider agnostic, no pay-per-token lock-in; full control of suspend and resume |
| Auth | Pass-through of the user JWT first, token exchange later | Authorization stays enforced by the existing services |
| Agents | One agent, defined as data | No routing or orchestration until a second domain exists |

Rejected, with the reason:

- **Websockets.** Bidirectional, but the session middleware stack is `BaseHTTPMiddleware` and does not run for websocket
  scopes, auth happens once at connect, and nothing in the requirements needs server push or mid-turn steering.
- **GraphQL subscriptions.** They fit "notify me when X changes", not a request that streams one answer. They would also
  bring websockets back. They remain a candidate for live boards (orders), as a separate feature.
- **A dedicated chat edge service with a session library.** Only justified with websockets; with SSE the BFF can proxy.
- **MongoDB.** No benefit over JSONB at this scale, and a new database means a new library and operational story.
- **LangChain or LangGraph.** Its checkpointer would duplicate the chat store and conflicts with a stateless agent. To
  be reconsidered if multi-agent routing becomes real.
- **A classifier in front of specialized models.** Nothing to route with one domain. Revisit with a second domain.
- **Generating tools from every router automatically.** Too many tools degrades selection accuracy and widens the
  prompt-injection surface.

## Architecture

```text
browser ──POST /chat/turns (SSE)──► bff-web ──POST /turns + JWT (SSE)──► be-agent ──MCP + JWT──► be-reservation
   │                                   │                                    │                  be-venue, ...
   └──GraphQL (list, rename, delete)───┴──────────► be-chat ◄───────────────┘
```

### bff-web

- Keeps GraphQL for everything that is not a live turn: list, rename and delete chats, load history.
- Adds one REST endpoint for a turn. It reads the session, takes the JWT, opens a streaming request to `be-agent` and
  returns what arrives without buffering or interpreting it.
- Closes the upstream request when the browser disconnects, so the turn is cancelled.

### be-chat

A standard domain service on PostgreSQL, built like `be-venue`.

- `chat`: id, user id, venue id, title, timestamps. Index on user id and update time.
- `message`: chat id, sequence, role, content as JSONB in the OpenAI message format used by LiteLLM, token usage.
- `pending_action`: chat id, tool, frozen arguments, summary, status. Durable chat state, so a reload does not lose it.

### be-agent

Stateless between segments of a turn. It owns no data of its own.

- Loads history from `be-chat`, runs the LLM loop through LiteLLM, appends messages back to `be-chat`.
- Holds the tool registry, filled from the MCP endpoints of the domain services.
- Is the only place where the confirmation rule is enforced.
- An agent is data: a system prompt, a tool filter and a model. There is one for now.

### Domain services

- A decorator on a route marks it as an AI tool and carries the description and the read or write kind.
- A helper in `ristops-lib-be` builds an MCP server from the decorated routes only and mounts it at `/mcp`.
- `tools/call` dispatches into the same application in process, so the middleware stack, `JwtAuthNMiddleware` and
  `@policy` apply as for any request. There is one code path for REST and MCP.
- The kind maps to the MCP `readOnlyHint` and `destructiveHint` annotations. A route that is not a `GET` is a write
  unless it is explicitly marked as read.

### Tool discovery

`be-agent` has a list of service URLs in its settings. It calls `tools/list` on each `/mcp`, caches the result with a
TTL and refreshes on failure. A new decorated route becomes a tool without redeploying `be-agent`.

## Turn flow

1. The browser sends the message and the current venue.
2. `be-agent` loads the history, adds the system prompt (current date and venue timezone included) and calls the model.
3. For a read tool it calls the service with the user's JWT and continues.
4. For a write tool it does not execute. It stores a `pending_action`, emits `confirmation_request` with a readable
   summary and ends the stream.
5. The user confirms or rejects with another request that names the pending action. The arguments are the stored ones;
   the client never resends them.
6. On confirmation `be-agent` executes the call, feeds the result to the model and streams the rest of the turn.

Because the suspended state is in the database, the transport does not matter for correctness, and a reload resumes
cleanly. Confirmation is enforced in code, never by the prompt.

### Event stream

| Event | Meaning |
|---|---|
| `delta` | Next piece of the answer |
| `reasoning` | Reasoning text, when the model provides it |
| `tool_call` | A tool is being called, with its namespaced name |
| `confirmation_request` | A write is waiting for the user |
| `done` | The turn is complete, with token usage |
| `error` | The turn failed |

The browser cancels by aborting the request. If the browser disconnects mid-turn the turn is cancelled, and what is
already persisted stays.

## Security

- OBO by pass-through: `be-agent` forwards the user's JWT, fetched fresh from the session for each call, since the
  access token lives 15 minutes. All access is checked by the existing services.
- The pass-through token can reach every endpoint the user can, so the perimeter rests on the tool allowlist. Planned
  hardening is a token exchange at `be-authn` issuing a short-lived token with an actor claim and a limited scope, so
  that services reject it outside the perimeter and audit logs can tell the assistant from the user. The token is
  obtained through one function, which makes this a local change.
- Customer-controlled text (names, notes) reaches the model through tool results and can carry prompt injection.
  Mitigations are the allowlist and mandatory confirmation of writes.

## Limits

- Per turn: maximum tool iterations, maximum tokens, timeout, truncation of large tool results.
- Per user: rate limit and daily token budget. Redis counters for the rate limit; usage stored per message for budgets.
- Per chat: one active turn at a time; a policy for history that exceeds the context window (truncation or summary).

## Observability

OpenTelemetry spans for each model call and each tool call, with token usage and cost as attributes. The BFF to
`be-agent` hop is traced like any other HTTP call.

## Frontend

- A floating button on every page opens the chat, scoped to the current venue from the workspace shell.
- The stream is read with `fetch` and a stream reader, because the browser's `EventSource` supports only `GET`.
- A confirmation card renders the summary of the pending write with confirm and reject buttons.
- The chat list behaves like other chat products: new chat, rename, delete.

## Growth path

Nothing here is built ahead of need.

1. Namespaced tool names and agents as data are the only provisions made now.
2. Scope tools by the page the user is on when the tool count grows.
3. With a second domain, sub-agents exposed as tools of an orchestrator; events carry an agent field so the interface
   can show which agent acted.
4. Token exchange for OBO, as above.
5. Live boards (orders) through GraphQL subscriptions or another push channel, as an independent feature.

## Open points

- Who may call `tools/list`. Proposed: unauthenticated on the internal network, as it returns metadata only. The
  alternative is a service identity for `be-agent`.
- Behaviour of the stack with streaming: `BaseHTTPMiddleware` has known quirks with streamed responses and client
  disconnects, and `RequestLoggingMiddleware` logs `[AFTER]` when the response starts. To be tested early, possibly
  with pure ASGI middleware for the streaming route.
- No buffering anywhere on the path (`Cache-Control: no-cache`, proxy and compression settings).
- Which model and provider, and whether it handles tool calling reliably.
- Service names and the shape of the decorator.
- Whether cancel on disconnect should instead let the turn finish.
