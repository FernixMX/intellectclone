"""
Dependencias FastAPI compartidas entre routers.
"""

from __future__ import annotations

from fastapi import Header, HTTPException

from intellectclone.config import get_settings


def verificar_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """
    Verifica el header X-Admin-Key contra ADMIN_SECRET_KEY.
    Si ADMIN_SECRET_KEY no está configurada, permite todo (modo desarrollo).
    """
    settings = get_settings()
    if not settings.admin_secret_key:
        return
    if x_admin_key != settings.admin_secret_key:
        raise HTTPException(status_code=403, detail="Clave de administrador inválida")
