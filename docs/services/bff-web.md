# bff-web

Backend-for-frontend for the web client. Exposes a GraphQL API and handles session-based
authentication, acting as the single entry point for the browser.

> Source: [ristops-bff-web](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-bff-web/README.md)

## Session-based authentication

The BFF exists partly to keep JWTs out of the browser. Rather than sending tokens to the client
and relying on client-side storage (which is exposed to XSS), tokens are stored server-side in
a Redis session keyed by a cookie. The browser only ever holds a session cookie.

On each request, `SessionAuthNMiddleware` loads the session, validates the stored access token,
and handles refresh transparently:

- If the token is valid and expires in more than 60 seconds: proceed
- If the token expires within 60 seconds: refresh it proactively before the request continues
- If the token is expired or the refresh fails: clear the session and return 401

Sessions have a rolling expiry of 1 hour — any authenticated request resets the timer.

## GraphQL schema composition

The schema is composed from per-domain `Query` and `Mutation` types using
`strawberry.tools.merge_types`. Each domain registers its own types without touching a central
schema file, so adding a new domain does not require modifying existing code.

Three schema extensions run on every operation:

| Extension | Purpose |
|-----------|---------|
| `ResolverLoggingExtension` | Logs resolver execution with timing |
| `ErrorHandlingExtension` | Maps internal exceptions to GraphQL errors |
| `ContextExtension` | Populates `APP_CONTEXT` with the GraphQL operation name |

## Frontend type generation

The merged schema is exposed at module level in `ristops_bff_web.graphql.schema` so it can be
exported as SDL without starting the application. The `graphql-bff export-schema` CLI command
prints the schema or writes it directly to a file.

Whenever resolvers or models change, export the updated schema from `ristops-backend/`:

```bash
ristops graphql-bff export-schema -f <output-path> --overwrite
```

See the frontend documentation for how to consume the generated SDL and regenerate TypeScript
types.
