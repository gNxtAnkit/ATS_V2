from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}")
    completed_process = subprocess.run(command, cwd=REPOSITORY_ROOT, check=False)
    if completed_process.returncode != 0:
        raise SystemExit(completed_process.returncode)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Required tool is not available on PATH: {name}")


def help_command() -> None:
    print(
        "\n".join(
            [
                "Available commands:",
                "  make setup             Install local Python dev dependencies",
                "  make dev               Run the API gateway shell locally",
                "  make up/down/restart   Manage local infrastructure",
                "  make logs              Stream local infrastructure logs",
                "  make test              Run all tests",
                "  make test-unit         Run unit tests",
                "  make test-integration  Run integration tests",
                "  make lint              Run Ruff lint checks",
                "  make format            Format Python code with Ruff",
                "  make typecheck         Run Mypy",
                "  make quality           Run format check, lint, typecheck, and tests",
                "  make db-upgrade        Apply Alembic migrations",
                "  make db-downgrade      Roll back one Alembic revision",
                "  make db-current        Show current Alembic revision",
                "  make db-history        Show Alembic migration history",
                "  make db-check          Check required schema artifacts exist",
                "  make db-validate       Run schema validation queries",
                "  make db-reset-local    Rebuild the local database baseline",
                "  make clean             Remove local Python cache artifacts",
            ]
        )
    )


def setup() -> None:
    run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])


def dev() -> None:
    run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "gnxthire_api_gateway.main:app",
            "--reload",
            "--app-dir",
            "apps/api-gateway/src",
        ]
    )


def quality() -> None:
    run([sys.executable, "-m", "ruff", "format", "--check", "."])
    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "mypy"])
    run([sys.executable, "-m", "pytest"])
    run([sys.executable, "scripts/db.py", "check"])


def clean() -> None:
    for pattern in ["**/__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "*.egg-info"]:
        for path in REPOSITORY_ROOT.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()


def main() -> None:
    commands = {
        "help": help_command,
        "setup": setup,
        "dev": dev,
        "quality": quality,
        "clean": clean,
    }
    command_name = sys.argv[1] if len(sys.argv) > 1 else "help"
    command = commands.get(command_name)
    if command is None:
        raise SystemExit(f"Unknown command: {command_name}")
    command()


if __name__ == "__main__":
    main()
