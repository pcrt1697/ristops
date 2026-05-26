# ristops-lib-sql

SQLAlchemy async session management.

> Source: [ristops-lib-sql](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-sql/README.md)

## Session management

This module addresses the need to manage SQLAlchemy session lifecycle — open, commit, rollback,
close — without requiring every route handler or service function to do it manually.
`AsyncSqlSessionProvider` owns the engine and session factory and is configured once at startup.
From that point, `@sql_transactional` handles the lifecycle transparently.

Sessions are stored in a `ContextVar`, so each request has its own isolated session. The provider
commits on success and rolls back on any exception.

## Decorator pattern

Two decorators cover the two entry points into the application:

| Decorator | Use case | What it does |
|-----------|----------|-------------|
| `@with_sql_db` | CLI commands | Configures the provider before the command runs |
| `@sql_transactional` | Route handlers, services | Opens a session; reuses the existing one if already open |

`@sql_transactional` uses join-if-exists semantics: if a session is already open in the current
context the function simply joins it, so the outermost call in the stack controls commit and
rollback. This makes it safe to call `@sql_transactional` functions from within other
`@sql_transactional` functions without nesting transactions.

```python
# CLI entry point
@async_command
@with_sql_db
@sql_transactional
async def seed(_: click.Context): ...

# Service layer — safely reuses an open session if one exists
@sql_transactional
async def create_user(data: UserCreate) -> User:
    session = get_sql_session()
    ...
```
