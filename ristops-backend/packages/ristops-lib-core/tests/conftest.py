import logging

import pytest

from ristops_lib_core.context import APP_CONTEXT


@pytest.fixture
def anyio_backend() -> str:
    """Run the async tests on asyncio only."""
    return "asyncio"


@pytest.fixture(autouse=True)
def clean_app_context():
    """Start and end every test with an empty request context."""
    APP_CONTEXT.reset()
    yield
    APP_CONTEXT.reset()


@pytest.fixture
def restore_root_logger():
    """Give the test a root logger it may reconfigure, and put the original one back afterwards."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield root
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)
