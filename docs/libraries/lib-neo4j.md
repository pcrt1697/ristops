# ristops-lib-neo4j

Neo4j async driver, transaction management, and a file-based migration engine.

> Source: [ristops-lib-neo4j](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-neo4j/README.md)

## Transaction management

This module addresses the same concern as `ristops-lib-sql` but for Neo4j: managing explicit
transaction lifecycle so that route handlers and service functions only deal with business logic.
`AsyncNeo4jTransactionProvider` owns the driver and opens transactions on demand. Transactions
are stored in a `ContextVar`, giving each request its own isolated transaction.

Two decorators cover the two entry points:

| Decorator | Use case | What it does |
|-----------|----------|-------------|
| `@with_neo4j_db` | CLI commands | Configures the driver before the command; closes it on exit |
| `@neo4j_transactional` | Route handlers, services | Opens a transaction; reuses the existing one if already open |

`@neo4j_transactional` uses the same join-if-exists semantics as `@sql_transactional` — nested
calls are safe and the outermost call controls commit and rollback.

```python
@neo4j_transactional
async def find_user(user_id: str) -> UserNode | None:
    tx = get_neo4j_transaction()
    result = await tx.run("MATCH (u:User {id: $id}) RETURN u", id=user_id)
    ...
```

## Migration engine

This module addresses the need to evolve the Neo4j schema and seed data in a controlled,
idempotent, and auditable way. `run_migrations` scans a directory for `.cypher` files, filters
out those already applied, and runs the remaining ones in order. Each applied migration is
recorded as a `Migration` node in the graph, linked to the previous one via a `NEXT` relationship,
forming a chain that makes the history queryable.

Migrations are split into two types — `schema` and `data` — to make the intent of each file
explicit. Each file can contain multiple statements separated by `;`.

Migration files follow the naming convention:

```text
<id>.<schema|data>.<name>.cypher
```

The `migrations_dir` is passed as a `Traversable` by the caller, so the engine is decoupled
from any specific package layout:

```python
from importlib.resources import files

await run_migrations(
    neo4j_transaction_provider,
    files("my_package.database").joinpath("migrations"),
)
```
