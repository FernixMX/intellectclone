"""
Dependencias FastAPI compartidas entre routers.
"""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from intellectclone.config import get_settings

_bearer = HTTPBearer(auto_error=False)


def verificar_admin_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """
    Verifica un JWT Bearer con sub='admin'.
    Si ADMIN_SECRET_KEY no está configurada, permite todo (modo desarrollo).
    """
    settings = get_settings()
    if not settings.admin_secret_key:
        return
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Se requiere Authorization: Bearer <token>",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("sub") != "admin":
            raise HTTPException(status_code=403, detail="Token sin privilegios de admin")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token expirado o inválido") from exc
