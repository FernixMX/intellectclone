#!/usr/bin/env bash
# =============================================================================
# IntellectClone — Script de deploy en VPS IONOS
#
# Uso:
#   1. Subir .env.production al servidor antes de correr este script:
#      scp .env.production root@212.227.239.140:/opt/intellectclone/
#   2. En el servidor como root:
#      bash deploy.sh
#
# El script clona el repo si no existe o hace git pull si ya está clonado,
# construye las imágenes, levanta los contenedores y corre migraciones.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuración — ajustar si cambia la ubicación o el repo
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/FernixMX/intellectclone.git"
APP_DIR="/opt/intellectclone"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"

# ---------------------------------------------------------------------------
# Colores para output
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
fail() { echo -e "${RED}[error]${NC} $*"; exit 1; }

# ---------------------------------------------------------------------------
# Verificaciones previas
# ---------------------------------------------------------------------------
command -v docker  > /dev/null 2>&1 || fail "Docker no está instalado"
command -v git     > /dev/null 2>&1 || fail "Git no está instalado"

# ---------------------------------------------------------------------------
# Clonar o actualizar el repositorio
# ---------------------------------------------------------------------------
if [ -d "${APP_DIR}/.git" ]; then
    log "Repositorio encontrado en ${APP_DIR} — actualizando..."
    git -C "${APP_DIR}" pull origin main
else
    log "Clonando repositorio en ${APP_DIR}..."
    git clone "${REPO_URL}" "${APP_DIR}"
fi

# ---------------------------------------------------------------------------
# Verificar que .env.production existe
# ---------------------------------------------------------------------------
if [ ! -f "${APP_DIR}/${ENV_FILE}" ]; then
    fail "No se encontró ${APP_DIR}/${ENV_FILE}. Sube el archivo antes de continuar:
  scp .env.production root@212.227.239.140:${APP_DIR}/"
fi

log "Archivo ${ENV_FILE} encontrado."

# ---------------------------------------------------------------------------
# Verificar que CHANGE_ no quedaron sin reemplazar en .env.production
# ---------------------------------------------------------------------------
if grep -q "CHANGE_" "${APP_DIR}/${ENV_FILE}"; then
    fail "El archivo ${ENV_FILE} contiene valores sin completar (CHANGE_*). Edítalo antes de continuar."
fi

# ---------------------------------------------------------------------------
# Construir imágenes y levantar contenedores
# ---------------------------------------------------------------------------
log "Construyendo imagen frontend con NEXT_PUBLIC_API_URL inyectado..."
docker build \
    -t intellectclone-frontend \
    --build-arg NEXT_PUBLIC_API_URL=https://elegant-keller.212-227-239-140.plesk.page/ \
    --no-cache \
    -f "${APP_DIR}/frontend/Dockerfile" \
    "${APP_DIR}/frontend/"

log "Construyendo imagen backend..."
docker compose -f "${APP_DIR}/${COMPOSE_FILE}" --env-file "${APP_DIR}/${ENV_FILE}" build --no-cache backend

log "Levantando contenedores..."
docker compose -f "${APP_DIR}/${COMPOSE_FILE}" --env-file "${APP_DIR}/${ENV_FILE}" up -d

# ---------------------------------------------------------------------------
# Esperar a que el backend esté listo (healthcheck interno de postgres)
# ---------------------------------------------------------------------------
log "Esperando que postgres esté listo..."
ATTEMPTS=0
MAX_ATTEMPTS=30
until docker compose -f "${APP_DIR}/${COMPOSE_FILE}" exec -T postgres pg_isready -U intellectclone > /dev/null 2>&1; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "${ATTEMPTS}" -ge "${MAX_ATTEMPTS}" ]; then
        fail "Postgres no respondió después de ${MAX_ATTEMPTS} intentos. Revisa los logs:
  docker compose -f ${APP_DIR}/${COMPOSE_FILE} logs postgres"
    fi
    warn "Postgres no listo, intento ${ATTEMPTS}/${MAX_ATTEMPTS}..."
    sleep 3
done

log "Postgres listo."

# ---------------------------------------------------------------------------
# Ejecutar migraciones Alembic
# ---------------------------------------------------------------------------
log "Ejecutando migraciones Alembic..."
docker compose -f "${APP_DIR}/${COMPOSE_FILE}" exec -T backend uv run alembic upgrade head

log "Migraciones aplicadas."

# ---------------------------------------------------------------------------
# Reporte de estado final
# ---------------------------------------------------------------------------
log "Estado de los contenedores:"
docker compose -f "${APP_DIR}/${COMPOSE_FILE}" ps

log "==========================================================="
log "Deploy completado."
log "  Frontend:  http://212.227.239.140:3001"
log "  Backend:   http://212.227.239.140:8001"
log "  API docs:  http://212.227.239.140:8001/docs"
log "  Dominio:   https://elegant-keller.212-227-239-140.plesk.page"
log "==========================================================="
log "Si es el primer deploy, verifica que Nginx/Plesk esté configurado."
log "Logs: docker compose -f ${APP_DIR}/${COMPOSE_FILE} logs -f"
