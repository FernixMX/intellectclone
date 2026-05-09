"""
CrossrefEnricher — resolución puntual de DOIs vía Crossref REST API.

Dado un DOI en parametros["doi"], retorna los metadatos completos del trabajo.
Usa el polite pool de Crossref (mailto en User-Agent) para mejor rate limit.
Rate limit: 2 rps (conservador; polite pool permite hasta 50 rps).
Se auto-registra al importar.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.normalizer import normalizar_doi, normalizar_titulo
from intellectclone.harvesters.runner import registrar_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_BASE_URL_DEFAULT = "https://api.crossref.org"

_TIPO_CROSSREF: dict[str, str] = {
    "journal-article": TipoPaper.articulo.value,
    "article": TipoPaper.articulo.value,
    "book": TipoPaper.libro.value,
    "book-chapter": TipoPaper.capitulo.value,
    "proceedings-article": TipoPaper.memoria_congreso.value,
    "proceedings": TipoPaper.memoria_congreso.value,
    "report": TipoPaper.reporte_tecnico.value,
    "report-series": TipoPaper.reporte_tecnico.value,
    "dissertation": TipoPaper.tesis_doctorado.value,
    "posted-content": TipoPaper.preprint.value,
}


def _mapear_tipo_crossref(tipo_texto: str) -> str:
    return _TIPO_CROSSREF.get(tipo_texto.lower().strip(), TipoPaper.otro.value)


def _extraer_año_crossref(published: dict[str, Any] | None) -> int | None:
    if published is None:
        return None
    date_parts = published.get("date-parts")
    if date_parts and date_parts[0]:
        try:
            return int(date_parts[0][0])
        except (IndexError, TypeError, ValueError):
            return None
    return None


def _formatear_autores(authors: list[dict[str, Any]]) -> str | None:
    if not authors:
        return None
    partes: list[str] = []
    for a in authors:
        family = str(a.get("family") or "").strip()
        given = str(a.get("given") or "").strip()
        if family and given:
            partes.append(f"{family}, {given}")
        elif family:
            partes.append(family)
        elif given:
            partes.append(given)
    return "; ".join(partes) if partes else None


def parsear_crossref_work(message: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parsea el campo 'message' de una respuesta Crossref /works/{doi}.
    Devuelve None si no hay título.
    """
    titles: list[str] = message.get("title") or []
    titulo: str = str(titles[0]).strip() if titles else ""
    if not titulo:
        return None

    doi_raw: str = str(message.get("DOI") or "").strip()
    doi = normalizar_doi(doi_raw) if doi_raw else None

    tipo_texto: str = str(message.get("type") or "").strip()
    authors: list[dict[str, Any]] = message.get("author") or []
    published = (
        message.get("published")
        or message.get("published-print")
        or message.get("published-online")
    )
    año = _extraer_año_crossref(published)

    container: list[str] = message.get("container-title") or []
    revista: str | None = str(container[0]).strip() if container else None

    issn_list: list[str] = message.get("ISSN") or []
    issn: str | None = issn_list[0] if issn_list else None

    editorial: str | None = str(message.get("publisher") or "").strip() or None

    return {
        "doi": doi,
        "titulo": titulo,
        "titulo_normalizado": normalizar_titulo(titulo),
        "autores_texto": _formatear_autores(authors),
        "año": año,
        "tipo": _mapear_tipo_crossref(tipo_texto),
        "revista": revista,
        "issn": issn,
        "editorial": editorial,
        "fuente_origen": TipoFuente.crossref.value,
    }


class CrossrefEnricher(BaseHarvester):
    """
    Enriquecedor puntual de DOIs via Crossref REST API.
    Ideal para resolver metadatos de papers con DOI dudoso o incompleto.
    """

    nombre = "Crossref Enricher"
    fuente_tipo = TipoFuente.crossref.value
    rate_limit_requests_por_segundo = 2.0

    _base_url: str = _BASE_URL_DEFAULT
    _timeout: float = 30.0
    _headers: dict[str, str] = {}
    _mailto: str = ""

    def configurar(self, config: dict[str, Any]) -> None:
        self._base_url = config.get("base_url", _BASE_URL_DEFAULT).rstrip("/")
        self._timeout = float(config.get("timeout_segundos", 30))
        self._mailto = config.get("mailto", "")
        ua_base = config.get("user_agent", "IntellectClone/1.0 (uso institucional UAT)")
        ua = f"{ua_base}; mailto:{self._mailto}" if self._mailto else ua_base
        self._headers = {"User-Agent": ua}

    def health_check(self) -> bool:
        try:
            resp = httpx.get(
                f"{self._base_url}/works/10.1126/science.169.3946.635",
                headers=self._headers,
                timeout=10.0,
                follow_redirects=True,
            )
            return bool(resp.status_code == 200)
        except Exception:
            return False

    async def cosechar(
        self,
        cosecha_id: str,
        modo: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        """
        - modo normal: resuelve el DOI en parametros["doi"].
        - modo enrich_pendiente: itera parametros["dois"] (lista pre-poblada por la tarea).
        """
        log = logger.bind(cosecha_id=cosecha_id, fuente=self.fuente_tipo)
        intervalo = 1.0 / self.rate_limit_requests_por_segundo

        if modo == "enrich_pendiente":
            dois: list[str] = list(parametros.get("dois") or [])
            log.info("crossref.batch_inicio", total=len(dois))
            async with httpx.AsyncClient(
                headers=self._headers,
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                for doi_raw in dois:
                    doi_raw = doi_raw.strip()
                    if not doi_raw:
                        continue
                    doi = normalizar_doi(doi_raw)
                    await asyncio.sleep(intervalo)
                    try:
                        resp = await client.get(f"{self._base_url}/works/{doi}")
                        if resp.status_code == 404:
                            log.debug("crossref.doi_no_encontrado", doi=doi)
                            continue
                        resp.raise_for_status()
                        message: dict[str, Any] = resp.json().get("message") or {}
                        datos = parsear_crossref_work(message)
                        if datos is None:
                            continue
                        parsed = self.parsear_registro(datos)
                        yield ResultadoCosecha(
                            datos=parsed,
                            fuente_id=parsed.get("doi") or doi,
                        )
                    except Exception as exc:
                        log.warning("crossref.error_doi", doi=doi, error=str(exc))
            log.info("crossref.batch_fin")
            return

        doi_raw = str(parametros.get("doi", "")).strip()
        if not doi_raw:
            log.warning("crossref.doi_vacio")
            return

        doi = normalizar_doi(doi_raw)
        log.info("crossref.resolucion_inicio", doi=doi)

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            await asyncio.sleep(intervalo)
            resp = await client.get(f"{self._base_url}/works/{doi}")

            if resp.status_code == 404:
                log.warning("crossref.doi_no_encontrado", doi=doi)
                return

            resp.raise_for_status()
            payload: dict[str, Any] = resp.json()
            message = payload.get("message") or {}
            datos = parsear_crossref_work(message)

            if datos is None:
                log.warning("crossref.sin_titulo", doi=doi)
                return

            parsed = self.parsear_registro(datos)
            yield ResultadoCosecha(
                datos=parsed,
                fuente_id=parsed.get("doi") or doi,
            )

        log.info("crossref.resolucion_fin", doi=doi)

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Convierte metadatos Crossref al formato canónico del sistema."""
        return {
            "doi": raw_data.get("doi"),
            "titulo": raw_data.get("titulo", ""),
            "titulo_normalizado": raw_data.get("titulo_normalizado"),
            "autores_texto": raw_data.get("autores_texto"),
            "año": raw_data.get("año"),
            "tipo": raw_data.get("tipo", TipoPaper.otro.value),
            "revista": raw_data.get("revista"),
            "issn": raw_data.get("issn"),
            "editorial": raw_data.get("editorial"),
            "fuente_origen": TipoFuente.crossref.value,
        }


registrar_harvester(TipoFuente.crossref.value, CrossrefEnricher)
