import os

import pytest

if os.getenv("RUN_DB_TESTS") == "1":
    if not os.getenv("TEST_DATABASE_URL"):
        raise pytest.UsageError("RUN_DB_TESTS=1 requires an explicit disposable TEST_DATABASE_URL")
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
else:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://test:unused@localhost:5432/architect_test"
