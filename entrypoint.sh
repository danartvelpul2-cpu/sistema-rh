#!/bin/sh
# Arranque del contenedor: migraciones + datos de demo (opcional) + servidor
set -e

echo "==> Aplicando migraciones..."
python manage.py migrate --no-input

if [ "$SEED_DEMO" = "true" ]; then
  echo "==> Cargando datos de demostración (admin / admin123)..."
  python manage.py seed_demo
fi

echo "==> Iniciando servidor en http://localhost:8000 ..."
exec gunicorn rh.wsgi:application --bind 0.0.0.0:8000 --log-file -
