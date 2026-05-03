#!/usr/bin/env bash
# =============================================================================
# Detiene los servicios de desarrollo sin borrar los volúmenes.
# Uso: ./scripts/dev_down.sh
# Para borrar datos también: docker compose -f docker-compose.dev.yml down -v
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "→ Deteniendo servicios de desarrollo..."
docker compose -f "$ROOT_DIR/docker-compose.dev.yml" down

echo "✓ Servicios detenidos. Los volúmenes de datos se conservaron."
