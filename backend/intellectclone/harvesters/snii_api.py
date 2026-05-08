"""
Cosecha SNII-UAT vía API JSON pública.

produccioncientifica.uat.edu.mx expone dos endpoints no autenticados:
  POST /buscador.aspx/Filtrado              → 474 investigadores con nivel SNII
  POST /dependencias.aspx/FiltradoDependencias → 25 dependencias

Los endpoints CampusCA (cuerpos académicos) requieren autenticación (401)
y se cosechan por el SNIIUATHarvester con Playwright cuando se tiene login.

Mapeo de niveles SNII al enum interno:
  Candidato / SNCA → candidato
  SNII 1           → nivel_1
  SNII 2           → nivel_2
  SNII 3           → nivel_3
  Emérito          → emerito
"""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from typing import TYPE_CHECKING, Any

import httpx
import structlog

from intellectclone.models.enums import NivelSnii

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_BASE_URL = "https://produccioncientifica.uat.edu.mx"
_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

_NIVEL_MAP: dict[str, str] = {
    "candidato": NivelSnii.candidato.value,
    "snca": NivelSnii.candidato.value,
    "snii 1": NivelSnii.nivel_1.value,
    "nivel i": NivelSnii.nivel_1.value,
    "snii 2": NivelSnii.nivel_2.value,
    "nivel ii": NivelSnii.nivel_2.value,
    "snii 3": NivelSnii.nivel_3.value,
    "nivel iii": NivelSnii.nivel_3.value,
    "emérito": NivelSnii.emerito.value,
    "emerito": NivelSnii.emerito.value,
}

_TIPO_DEPENDENCIA: list[tuple[str, str]] = [
    ("facultad", "facultad"),
    ("unidad académica", "unidad_academica"),
    ("unidad academica", "unidad_academica"),
    ("centro de", "centro"),
    ("instituto", "instituto"),
    ("división", "division"),
    ("division", "division"),
    ("escuela", "escuela"),
]


def normalizar_nombre(texto: str) -> str:
    """Normaliza un nombre: minúsculas, sin acentos, espacios colapsados."""
    s = unicodedata.normalize("NFKD", texto.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()


def tipo_dependencia(nombre: str) -> str:
    n = nombre.lower()
    for key, tipo in _TIPO_DEPENDENCIA:
        if key in n:
            return tipo
    return "otro"


def mapear_nivel_snii(sni_raw: str) -> str | None:
    """Convierte el texto de nivel SNII al valor del enum interno."""
    return _NIVEL_MAP.get(sni_raw.strip().lower())


def fetch_investigadores(base_url: str = _BASE_URL, timeout: float = 30.0) -> list[dict[str, Any]]:
    """Retorna los ~474 investigadores con nivel SNII registrados en la UAT."""
    r = httpx.post(
        f"{base_url}/buscador.aspx/Filtrado",
        headers={**_HEADERS, "Referer": f"{base_url}/Buscador.aspx"},
        json={},
        timeout=timeout,
    )
    r.raise_for_status()
    return list(json.loads(r.json()["d"]))


def fetch_dependencias(base_url: str = _BASE_URL, timeout: float = 30.0) -> list[dict[str, Any]]:
    """Retorna las 25 dependencias con investigadores SNII en la UAT."""
    r = httpx.post(
        f"{base_url}/dependencias.aspx/FiltradoDependencias",
        headers={**_HEADERS, "Referer": f"{base_url}/Dependencias.aspx"},
        json={},
        timeout=timeout,
    )
    r.raise_for_status()
    return list(json.loads(r.json()["d"]))


def build_dependencia_values(dep: dict[str, Any]) -> dict[str, Any]:
    """Construye el dict de columnas para upsert de Dependencia."""
    nombre = dep["nombre"].strip()
    return {
        "id": uuid.uuid4(),
        "codigo": f"SNII-{dep['id']}",
        "nombre": nombre,
        "tipo": tipo_dependencia(nombre),
        "campus": dep.get("campus", "").strip() or None,
        "activa": True,
        "metadatos": {},
    }


async def ejecutar_cosecha_snii_api(
    session: AsyncSession,
    base_url: str = _BASE_URL,
) -> dict[str, int]:
    """
    Cosecha completa vía API JSON pública de produccioncientifica.uat.edu.mx.

    Persiste dependencias (upsert by codigo) y actualiza nivel_snii +
    dependencia_id en personas que coinciden por nombre normalizado.

    Retorna resumen con claves: dependencias, personas_actualizadas, sin_match.
    """
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from intellectclone.models.institucional import Dependencia

    log = logger.bind(fuente="snii_api")

    log.info("snii_api.fetch_inicio")
    dependencias_raw = fetch_dependencias(base_url)
    investigadores_raw = fetch_investigadores(base_url)
    log.info(
        "snii_api.fetch_ok",
        dependencias=len(dependencias_raw),
        investigadores=len(investigadores_raw),
    )

    # ------------------------------------------------------------------ #
    # 1. Upsert dependencias                                               #
    # ------------------------------------------------------------------ #
    dep_codigo_map: dict[str, uuid.UUID] = {}

    for dep in dependencias_raw:
        vals = build_dependencia_values(dep)
        stmt = pg_insert(Dependencia).values(**vals)
        stmt = stmt.on_conflict_do_update(
            index_elements=["codigo"],
            set_={"nombre": stmt.excluded.nombre, "campus": stmt.excluded.campus},
        ).returning(Dependencia.id)
        row = (await session.execute(stmt)).scalar()
        if row:
            dep_codigo_map[dep["id"]] = uuid.UUID(str(row))

    await session.commit()
    log.info("snii_api.dependencias_ok", count=len(dep_codigo_map))

    # Índice nombre_normalizado → dep_uuid para matching rápido
    dep_nombre_map: dict[str, uuid.UUID] = {}
    for dep in dependencias_raw:
        if dep["id"] in dep_codigo_map:
            dep_nombre_map[normalizar_nombre(dep["nombre"])] = dep_codigo_map[dep["id"]]

    # ------------------------------------------------------------------ #
    # 2. Actualizar personas con nivel_snii y dependencia_id              #
    # ------------------------------------------------------------------ #
    actualizados = 0
    sin_match = 0

    for inv in investigadores_raw:
        nombre_norm = normalizar_nombre(inv.get("nombre", ""))
        nivel_db = mapear_nivel_snii(inv.get("sni", ""))
        campus_norm = normalizar_nombre(inv.get("campus", ""))

        dep_uuid: uuid.UUID | None = dep_nombre_map.get(campus_norm)
        if dep_uuid is None:
            row_dep = (
                await session.execute(
                    text(
                        "SELECT id FROM dependencia "
                        "WHERE similarity(lower(nombre), :q) >= 0.5 "
                        "ORDER BY similarity(lower(nombre), :q) DESC LIMIT 1"
                    ),
                    {"q": inv.get("campus", "").lower()},
                )
            ).first()
            dep_uuid = uuid.UUID(str(row_dep[0])) if row_dep else None

        # Exact match first, then trigram
        row_p = (
            await session.execute(
                text("SELECT id FROM persona WHERE nombre_normalizado = :n LIMIT 1"),
                {"n": nombre_norm},
            )
        ).first()
        if row_p is None:
            row_p = (
                await session.execute(
                    text(
                        "SELECT id FROM persona "
                        "WHERE similarity(nombre_normalizado, :n) >= 0.85 "
                        "ORDER BY similarity(nombre_normalizado, :n) DESC LIMIT 1"
                    ),
                    {"n": nombre_norm},
                )
            ).first()

        if row_p is None:
            sin_match += 1
            continue

        persona_id = uuid.UUID(str(row_p[0]))
        updates: dict[str, object] = {}
        if nivel_db:
            updates["nivel_snii"] = nivel_db
        if dep_uuid is not None:
            updates["dependencia_id"] = dep_uuid

        if updates:
            set_parts = ", ".join(f"{k} = :{k}" for k in updates)
            await session.execute(
                text(f"UPDATE persona SET {set_parts} WHERE id = :id"),
                {**updates, "id": str(persona_id)},
            )
            actualizados += 1

    await session.commit()
    log.info("snii_api.personas_ok", actualizados=actualizados, sin_match=sin_match)

    return {
        "dependencias": len(dep_codigo_map),
        "personas_actualizadas": actualizados,
        "sin_match": sin_match,
    }
