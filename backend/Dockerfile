FROM python:3.12-slim

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Dependencias del sistema para librerías nativas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos de dependencias primero (cache de capas)
COPY pyproject.toml uv.lock* ./

# Instalar dependencias
RUN uv sync --frozen --no-install-project

# Copiar código fuente
COPY . .

# Instalar el proyecto
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "intellectclone.main:app", "--host", "0.0.0.0", "--port", "8000"]
