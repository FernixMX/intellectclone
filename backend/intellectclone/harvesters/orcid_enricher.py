"""
ORCIDEnricher — enriquecedor de papers por ORCID iD.

Dado un ORCID en parametros["orcid"], cosecha todos los works públicos
de esa persona via ORCID Public API v3.0.
Valida formato y checksum ISO 7064 MOD 11-2. Asigna confianza_match alto
porque los works son autoasertados por el propio investigador.
Rate limit: 2 rps. Se auto-registra al importar.
"""

from __future__ import annotations

import asyncio
import re
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

_BASE_URL_DEFAULT = "https://pub.orcid.org"
_RE_ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$", re.IGNORECASE)

_TIPO_ORCID: dict[str, str] = {
    "journal-article": TipoPaper.articulo.value,
    "article": TipoPaper.articulo.value,
    "book": TipoPaper.libro.value,
    "book-chapter": TipoPaper.capitulo.value,
    "conference-paper": TipoPaper.memoria_congreso.value,
    "conference-abstract": TipoPaper.memoria_congreso.value,
    "dissertation": TipoPaper.tesis_doctorado.value,
    "dissertation-thesis": TipoPaper.tesis_doctorado.value,
    "report": TipoPaper.reporte_tecnico.value,
    "preprint": TipoPaper.preprint.value,
}

_CONFIANZA_ORCID_CON_WORKS = 0.95
_CONFIANZA_ORCID_SIN_WORKS = 0.70


def _mapear_tipo_orcid(tipo_texto: str) -> str:
    return _TIPO_ORCID.get(tipo_texto.lower().strip(), TipoPaper.otro.value)


def validar_formato_orcid(orcid: str) -> bool:
    """Valida que el ORCID tenga el formato XXXX-XXXX-XXXX-XXXX."""
    return bool(_RE_ORCID.match(orcid.strip()))


def validar_checksum_orcid(orcid: str) -> bool:
    """
    Valida el dígito de control ISO 7064 MOD 11-2 del ORCID.
    El último carácter puede ser 0-9 o X (=10).
    """
    digits = orcid.replace("-", "").upper()
    if len(digits) != 16:
        return False
    try:
        total = 0
        for char in digits[:15]:
            total = (total + int(char)) * 2
    except ValueError:
        return False
    check_value = (12 - (total % 11)) % 11
    expected = "X" if check_value == 10 else str(check_value)
    return digits[15] == expected


def validar_orcid(orcid: str) -> bool:
    """Valida formato y checksum. True = ORCID estructuralmente correcto."""
    return validar_formato_orcid(orcid) and validar_checksum_orcid(orcid)


def _extraer_doi_de_external_ids(external_ids: list[dict[str, Any]]) -> str | None:
    for eid in external_ids:
        if eid.get("external-id-type") == "doi":
            valor = eid.get("external-id-value", "")
            if valor:
                return normalizar_doi(str(valor))
    return None


def _extraer_año_orcid(pub_date: dict[str, Any] | None) -> int | None:
    if pub_date is None:
        return None
    year_obj = pub_date.get("year")
    if year_obj and year_obj.get("value"):
        try:
            return int(year_obj["value"])
        except (ValueError, TypeError):
            return None
    return None


def parsear_work_orcid(work_summary: dict[str, Any], orcid: str) -> dict[str, Any] | None:
    """
    Parsea un work-summary de la ORCID API.
    Devuelve None si no tiene título.
    """
    titulo_obj = work_summary.get("title") or {}
    titulo_inner = titulo_obj.get("title") or {}
    titulo: str = str(titulo_inner.get("value") or "").strip()
    if not titulo:
        return None

    tipo_texto: str = str(work_summary.get("type") or "").strip()
    put_code: int | None = work_summary.get("put-code")

    pub_date = work_summary.get("publication-date")
    año = _extraer_año_orcid(pub_date)

    journal_obj = work_summary.get("journal-title") or {}
    revista: str | None = str(journal_obj.get("value") or "").strip() or None

    ext_ids_wrapper = work_summary.get("external-ids") or {}
    ext_ids: list[dict[str, Any]] = ext_ids_wrapper.get("external-id") or []
    doi = _extraer_doi_de_external_ids(ext_ids)

    return {
        "orcid": orcid,
        "orcid_put_code": put_code,
        "doi": doi,
        "titulo": titulo,
        "titulo_normalizado": normalizar_titulo(titulo),
        "año": año,
        "tipo": _mapear_tipo_orcid(tipo_texto),
        "revista": revista,
        "confianza_match": _CONFIANZA_ORCID_CON_WORKS,
        "fuente_origen": TipoFuente.orcid.value,
    }


class ORCIDEnricher(BaseHarvester):
    """
    Enriquecedor de papers a partir de ORCID iD.
    Cosecha todos los works públicos de un investigador dado su ORCID.
    """

    nombre = "ORCID Enricher"
    fuente_tipo = TipoFuente.orcid.value
    rate_limit_requests_por_segundo = 2.0

    _base_url: str = _BASE_URL_DEFAULT
    _timeout: float = 30.0
    _headers: dict[str, str] = {}

    def configurar(self, config: dict[str, Any]) -> None:
        self._base_url = config.get("base_url", _BASE_URL_DEFAULT).rstrip("/")
        self._timeout = float(config.get("timeout_segundos", 30))
        ua = config.get("user_agent", "IntellectClone/1.0 (uso institucional UAT)")
        self._headers = {
            "User-Agent": ua,
            "Accept": "application/json",
        }

    def health_check(self) -> bool:
        try:
            resp = httpx.get(
                f"{self._base_url}/v3.0/0000-0002-1825-0097/record",
                headers=self._headers,
                timeout=10.0,
                follow_redirects=True,
            )
            return bool(resp.status_code == 200)
        except Exception:
            return False

    async def _cosechar_orcid(
        self,
        client: httpx.AsyncClient,
        orcid: str,
        intervalo: float,
        log: structlog.stdlib.BoundLogger,
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        """Fetches and yields works for a single ORCID."""
        await asyncio.sleep(intervalo)
        resp = await client.get(f"{self._base_url}/v3.0/{orcid}/works")
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
        groups: list[dict[str, Any]] = payload.get("group") or []
        for group in groups:
            summaries: list[dict[str, Any]] = group.get("work-summary") or []
            if not summaries:
                continue
            summary = summaries[0]
            datos = parsear_work_orcid(summary, orcid)
            if datos is None:
                continue
            parsed = self.parsear_registro(datos)
            yield ResultadoCosecha(
                datos=parsed,
                fuente_id=str(parsed.get("orcid_put_code") or parsed.get("doi") or orcid),
            )

    async def cosechar(
        self,
        cosecha_id: str,
        modo: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        """
        - modo normal: cosecha works de parametros["orcid"].
        - modo enrich_pendiente: itera parametros["orcids"] (lista pre-poblada por la tarea).
        """
        log = logger.bind(cosecha_id=cosecha_id, fuente=self.fuente_tipo)
        intervalo = 1.0 / self.rate_limit_requests_por_segundo

        if modo == "enrich_pendiente":
            orcids: list[str] = list(parametros.get("orcids") or [])
            log.info("orcid.batch_inicio", total=len(orcids))
            async with httpx.AsyncClient(
                headers=self._headers,
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                for orcid_item in orcids:
                    orcid_item = orcid_item.strip()
                    if not validar_orcid(orcid_item):
                        log.debug("orcid.invalido_en_batch", orcid=orcid_item)
                        continue
                    try:
                        async for resultado in self._cosechar_orcid(
                            client, orcid_item, intervalo, log
                        ):
                            yield resultado
                    except Exception as exc:
                        log.warning("orcid.error_en_batch", orcid=orcid_item, error=str(exc))
            log.info("orcid.batch_fin")
            return

        orcid: str = str(parametros.get("orcid", "")).strip()
        if not validar_orcid(orcid):
            log.warning("orcid.invalido", orcid=orcid)
            return

        log.info("orcid.cosecha_inicio", orcid=orcid)
        total = 0
        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            async for resultado in self._cosechar_orcid(client, orcid, intervalo, log):
                yield resultado
                total += 1
        log.info("orcid.cosecha_fin", orcid=orcid, total=total)

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Convierte metadatos ORCID al formato canónico del sistema."""
        return {
            "orcid": raw_data.get("orcid"),
            "orcid_put_code": raw_data.get("orcid_put_code"),
            "doi": raw_data.get("doi"),
            "titulo": raw_data.get("titulo", ""),
            "titulo_normalizado": raw_data.get("titulo_normalizado"),
            "año": raw_data.get("año"),
            "tipo": raw_data.get("tipo", TipoPaper.otro.value),
            "revista": raw_data.get("revista"),
            "confianza_match": raw_data.get("confianza_match", _CONFIANZA_ORCID_CON_WORKS),
            "fuente_origen": TipoFuente.orcid.value,
        }


registrar_harvester(TipoFuente.orcid.value, ORCIDEnricher)
