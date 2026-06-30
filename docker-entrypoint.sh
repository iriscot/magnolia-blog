#!/bin/sh
set -eu

python manage.py migrate --noinput

if [ "${DJANGO_COLLECTSTATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

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
if created or not user.has_usable_password():
    user.set_password(password)
    changed = True
if changed:
    user.save()
PY
fi

exec "$@"
