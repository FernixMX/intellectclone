#!/usr/bin/env bash
# =============================================================================
# Levanta el entorno de desarrollo local (PostgreSQL + Redis).
# Uso: ./scripts/dev_up.sh
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "→ Levantando servicios de desarrollo..."
docker compose -f "$ROOT_DIR/docker-compose.dev.yml" up -d

echo "→ Esperando que PostgreSQL esté listo..."
until docker exec intellectclone_postgres_dev pg_isready -U intellectclone -d intellectclone_dev > /dev/null 2>&1; do
  sleep 1
done

echo "✓ PostgreSQL listo"
echo "✓ Redis listo"
echo ""
echo "Servicios disponibles:"
echo "  PostgreSQL: localhost:5432 (db: intellectclone_dev, user: intellectclone)"
echo "  Redis:      localhost:6379"
