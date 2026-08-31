#!/bin/sh
set -e

echo "Attendo che il database sia pronto..."
python << 'PYEOF'
import os, time, sys
import psycopg
import environ

env = environ.Env()
environ.Env.read_env("/app/.env") if os.path.exists("/app/.env") else None
db_config = env.db("DATABASE_URL", default="postgres://tasso:tasso@db:5432/tasso")

for attempt in range(30):
    try:
        conn = psycopg.connect(
            host=db_config["HOST"], port=db_config["PORT"],
            dbname=db_config["NAME"], user=db_config["USER"], password=db_config["PASSWORD"],
            connect_timeout=3,
        )
        conn.close()
        print("Database raggiungibile.")
        sys.exit(0)
    except Exception as e:
        print(f"Database non ancora pronto ({attempt + 1}/30): {e}")
        time.sleep(2)
print("Impossibile raggiungere il database, esco.")
sys.exit(1)
PYEOF

echo "Applico le migrazioni..."
python manage.py migrate --noinput

echo "Raccolgo i file statici..."
python manage.py collectstatic --noinput

# Crea automaticamente un superuser al primo avvio se le variabili sono impostate
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Verifico/creo il superuser iniziale..."
    python manage.py createsuperuser --noinput || true
fi

echo "Avvio: $@"
exec "$@"
