"""
Repositorios de datos de IntellectClone.
"""

from intellectclone.db.repositorios.base import RepositorioBase
from intellectclone.db.repositorios.cuerpo_academico import RepositorioCuerpoAcademico
from intellectclone.db.repositorios.dependencia import RepositorioDependencia
from intellectclone.db.repositorios.persona import RepositorioPersona

__all__ = [
    "RepositorioBase",
    "RepositorioCuerpoAcademico",
    "RepositorioDependencia",
    "RepositorioPersona",
]
