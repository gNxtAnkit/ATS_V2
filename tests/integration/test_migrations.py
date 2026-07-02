import os
import subprocess
import sys

import pytest

from gnxthire_testing.database import database_tests_enabled


pytestmark = pytest.mark.skipif(
    not database_tests_enabled(),
    reason="Set GNXTHIRE_RUN_DB_TESTS=1 and provide DATABASE_URL to run database migration tests.",
)


def test_alembic_upgrade_current_and_validate() -> None:
    environment = os.environ.copy()
    environment.setdefault("GNXTHIRE_ENV", "test")

    for command in [
        [sys.executable, "scripts/db.py", "downgrade", "base"],
        [sys.executable, "scripts/db.py", "upgrade"],
        [sys.executable, "scripts/db.py", "current"],
        [sys.executable, "scripts/db.py", "validate"],
    ]:
        completed_process = subprocess.run(command, check=False, env=environment)
        assert completed_process.returncode == 0
