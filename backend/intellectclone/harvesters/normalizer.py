"""
Funciones de normalización para el pipeline de cosecha.

Todas son puras (sin efectos secundarios) para facilitar tests y reutilización.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_RE_ESPACIOS = re.compile(r"\s+")
_RE_DOI_PREFIX = re.compile(r"^https?://(?:dx\.)?doi\.org/", re.IGNORECASE)


def normalizar_nombre(nombre: str) -> str:
    """
    Convierte 'María Elena Cárdenas-Ruiz' → 'maria elena cardenas ruiz'.

    Pipeline: lowercase → strip acentos (NFKD) → guiones/puntos → colapsar espacios.
    """
    n = nombre.lower()
    n = unicodedata.normalize("NFKD", n)
    n = n.encode("ASCII", "ignore").decode("ASCII")
    n = n.replace("-", " ").replace(".", " ")
    return _RE_ESPACIOS.sub(" ", n).strip()


def normalizar_titulo(titulo: str) -> str:
    """
    Normaliza un título de paper para comparación fuzzy.

    Igual que normalizar_nombre pero también elimina caracteres no alfanuméricos
    (excluye espacios) para mejorar ratio de similitud entre fuentes distintas.
    """
    t = normalizar_nombre(titulo)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return _RE_ESPACIOS.sub(" ", t).strip()


def normalizar_doi(doi: str) -> str:
    """
    Devuelve el DOI en forma canónica: sin prefijo URL, en minúsculas.

    Ejemplos:
        'https://doi.org/10.1016/j.foo.2020' → '10.1016/j.foo.2020'
        'DOI: 10.1016/j.foo.2020'            → '10.1016/j.foo.2020'
    """
    doi = doi.strip()
    doi = _RE_DOI_PREFIX.sub("", doi)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    return doi.lower().strip()


def ratio_similitud(a: str, b: str) -> float:
    """
    Devuelve la similitud de Ratcliff/Obershelp entre dos cadenas (0.0 – 1.0).

    En producción el filtro previo usa pg_trgm en PostgreSQL; esta función
    puntúa los candidatos ya recuperados y se usa directamente en tests.
    """
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
