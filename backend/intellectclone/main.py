"""
Punto de entrada de la aplicación FastAPI.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from intellectclone.config import get_settings

settings = get_settings()

app = FastAPI(
    title="IntellectClone",
    description="Plataforma de gemelos digitales de la comunidad académica UAT",
    version="0.1.0",
    # En producción se desactivan los docs para usuarios no admin
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["sistema"])
async def health() -> dict[str, str]:
    """Health check básico del servidor."""
    return {"status": "ok", "version": "0.1.0"}
