"""Bootstrap or reset a platform-admin credential.

Out-of-band CLI, not an HTTP route: platform-admin login has no self-registration
by design (an HTTP "become the first admin" endpoint would be a standing security
hole), so seeding the very first admin's password -- or recovering one whose
credential was lost before any other admin exists -- must happen here rather than
through the API. Refuses to run outside local/test environments unless the caller
explicitly acknowledges the bypass.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "packages" / "backend-common" / "src"))
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "identity" / "src"))

from sqlalchemy import text

from gnxthire_common.db import create_sync_engine
from gnxthire_common.errors import ValidationFailure
from gnxthire_identity.config import get_identity_settings
from gnxthire_identity.security import hash_password, validate_password_policy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="Platform admin email (created if it does not exist)")
    parser.add_argument("--password", required=True, help="New password to set")
    parser.add_argument("--display-name", default=None, help="Display name to use if the user does not exist yet")
    parser.add_argument(
        "--i-understand-this-is-not-for-production",
        action="store_true",
        help="Required outside local/test APP_ENV to confirm this auth bypass is intentional",
    )
    args = parser.parse_args()

    settings = get_identity_settings()
    if settings.app_env not in {"local", "test"} and not args.i_understand_this_is_not_for_production:
        raise SystemExit(
            "Refusing to bootstrap a platform-admin password outside local/test APP_ENV without "
            "--i-understand-this-is-not-for-production. This script bypasses normal auth flows."
        )

    email = args.email.strip().lower()
    try:
        validate_password_policy(args.password, email, settings)
    except ValidationFailure as exc:
        raise SystemExit(f"Password does not meet policy: {exc}") from exc

    password_hash = hash_password(args.password)
    engine = create_sync_engine()
    with engine.begin() as connection:
        existing = connection.execute(
            text("SELECT id FROM platform.platform_users WHERE email = :email AND deleted_at IS NULL"),
            {"email": email},
        ).one_or_none()
        if existing is None:
            display_name = args.display_name or email.split("@", 1)[0]
            connection.execute(
                text(
                    """
                    INSERT INTO platform.platform_users (email, display_name, status, password_hash, email_verified_at)
                    VALUES (:email, :display_name, 'active', :password_hash, now())
                    """
                ),
                {"email": email, "display_name": display_name, "password_hash": password_hash},
            )
            print(f"Created platform admin {email} with status=active")
        else:
            connection.execute(
                text(
                    """
                    UPDATE platform.platform_users
                    SET password_hash = :password_hash, status = 'active', updated_at = now()
                    WHERE id = :id
                    """
                ),
                {"password_hash": password_hash, "id": existing.id},
            )
            print(f"Updated password for existing platform admin {email}")


if __name__ == "__main__":
    main()
