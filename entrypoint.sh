#!/usr/bin/env bash
set -e

echo "Waiting for Postgres..."
python - <<'PY'
import os, time, socket
host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("Postgres is up.")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("Postgres not available after 60s")
PY

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput || true

# Optional: create a superuser automatically (only if env vars are set)
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_PASSWORD" && -n "$DJANGO_SUPERUSER_EMAIL" ]]; then
  echo "Ensuring superuser exists..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u = '$DJANGO_SUPERUSER_USERNAME'
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
print('Superuser check complete.')
" || true
fi

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60