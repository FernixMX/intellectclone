"""
Router principal de la API v1 de IntellectClone.
Agrega todos los sub-routers de cada dominio.
"""

from fastapi import APIRouter

from intellectclone.api.v1 import cuerpos_academicos, dependencias, papers, personas

router = APIRouter()

router.include_router(dependencias.router)
router.include_router(cuerpos_academicos.router)
router.include_router(personas.router)
router.include_router(papers.router)
