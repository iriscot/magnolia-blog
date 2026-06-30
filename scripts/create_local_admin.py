#!/usr/bin/env python
"""Create or repair a local Django superuser from environment variables."""

from __future__ import annotations

import os
import sys


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Magnolia.settings")

    import django

    django.setup()

    from django.contrib.auth import get_user_model

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()

    if not username or not password:
        print("Local admin was not created: DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD is empty.")
        return 0

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email, "is_staff": True, "is_superuser": True},
    )

    changed = False
    if not user.is_staff or not user.is_superuser:
        user.is_staff = True
        user.is_superuser = True
        changed = True
    if email and user.email != email:
        user.email = email
        changed = True

    reset_password = env_bool("LOCAL_RESET_ADMIN_PASSWORD", default=False)
    if created or reset_password or not user.has_usable_password():
        user.set_password(password)
        changed = True

    if changed:
        user.save()

    status = "created" if created else "ready"
    print(f"Local admin {status}: {username}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
