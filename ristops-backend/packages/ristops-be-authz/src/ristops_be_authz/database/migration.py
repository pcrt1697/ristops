from importlib.resources import files

from ristops_lib_neo4j.engine import neo4j_transaction_provider
from ristops_lib_neo4j.migration import run_migrations


async def migrate():
    migrations_dir = files(__package__).joinpath("migrations")
    await run_migrations(neo4j_transaction_provider, migrations_dir)
