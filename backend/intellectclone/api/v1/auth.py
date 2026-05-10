"""
POST /api/v1/auth/login — devuelve un JWT de administrador.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel

from intellectclone.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)  # type: ignore[misc]
async def login(body: LoginRequest) -> TokenResponse:
    """Valida la contraseña de admin y devuelve un JWT con sub='admin'."""
    settings = get_settings()
    if not body.password:
        raise HTTPException(status_code=400, detail="Contraseña requerida")
    if settings.admin_secret_key and body.password != settings.admin_secret_key:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    payload: dict[str, Any] = {
        "sub": "admin",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=24),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return TokenResponse(access_token=token)
