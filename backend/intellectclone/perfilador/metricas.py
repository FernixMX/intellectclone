"""
Cálculo de métricas bibliométricas para Persona.

Calcula indice_h, indice_i10, primera_publicacion, ultima_publicacion,
total_publicaciones y total_citas a partir de coautorias y papers en BD.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SQL_ACTUALIZAR_METRICAS = """
WITH citas_rank AS (
    SELECT
        c.persona_id,
        pa.total_citas,
        ROW_NUMBER() OVER (
            PARTITION BY c.persona_id
            ORDER BY pa.total_citas DESC
        ) AS rn
    FROM coautoria c
    JOIN paper pa ON c.paper_id = pa.id
),
h_index AS (
    SELECT
        persona_id,
        MAX(CASE WHEN total_citas >= rn THEN rn ELSE 0 END) AS indice_h
    FROM citas_rank
    GROUP BY persona_id
),
i10 AS (
    SELECT c.persona_id, COUNT(*) AS indice_i10
    FROM coautoria c
    JOIN paper pa ON c.paper_id = pa.id
    WHERE pa.total_citas >= 10
    GROUP BY c.persona_id
),
fechas AS (
    SELECT
        c.persona_id,
        MIN(pa.fecha_publicacion) AS primera_publicacion,
        MAX(pa.fecha_publicacion) AS ultima_publicacion
    FROM coautoria c
    JOIN paper pa ON c.paper_id = pa.id
    WHERE pa.fecha_publicacion IS NOT NULL
    GROUP BY c.persona_id
),
conteos AS (
    SELECT
        c.persona_id,
        COUNT(*)                       AS total_publicaciones,
        COALESCE(SUM(pa.total_citas), 0) AS total_citas
    FROM coautoria c
    JOIN paper pa ON c.paper_id = pa.id
    GROUP BY c.persona_id
)
UPDATE persona p
SET
    indice_h            = COALESCE(h.indice_h, 0),
    indice_i10          = COALESCE(i.indice_i10, 0),
    primera_publicacion = f.primera_publicacion,
    ultima_publicacion  = f.ultima_publicacion,
    total_publicaciones = COALESCE(ct.total_publicaciones, 0),
    total_citas         = COALESCE(ct.total_citas, 0)
FROM
    h_index h
    LEFT JOIN i10     i  ON i.persona_id  = h.persona_id
    LEFT JOIN fechas  f  ON f.persona_id  = h.persona_id
    LEFT JOIN conteos ct ON ct.persona_id = h.persona_id
WHERE p.id = h.persona_id
"""


async def actualizar_metricas_todas(session: AsyncSession) -> int:
    """
    Recalcula métricas bibliométricas para todas las personas con coautorias.
    Devuelve el número de personas actualizadas.
    """
    result = await session.execute(text(_SQL_ACTUALIZAR_METRICAS))
    return int(result.rowcount)
