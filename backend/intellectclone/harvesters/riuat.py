"""
RIUATHarvester — Repositorio Institucional UAT (DSpace).

Estrategia:
  1. OAI-PMH (verb=ListRecords, metadataPrefix=oai_dc) — primario.
  2. Si OAI retorna 503 o XML inválido → fallback: scraping HTML de handles DSpace.

Caso especial tesis: dc:creator = estudiante, dc:contributor = directores.
Rate limit: 0.5 rps. Se auto-registra al importar.
"""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.normalizer import normalizar_doi, normalizar_titulo
from intellectclone.harvesters.runner import registrar_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_BASE_URL_DEFAULT = "https://riuat.uat.edu.mx"
_OAI_ENDPOINT_DEFAULT = "/oai/request"
_HANDLE_PREFIX_DEFAULT = "123456789"

_NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

_TIPO_RIUAT: dict[str, str] = {
    "article": TipoPaper.articulo.value,
    "artículo": TipoPaper.articulo.value,
    "articulo": TipoPaper.articulo.value,
    "journal article": TipoPaper.articulo.value,
    "tesis de maestría": TipoPaper.tesis_maestria.value,
    "tesis maestría": TipoPaper.tesis_maestria.value,
    "tesis de maestria": TipoPaper.tesis_maestria.value,
    "master thesis": TipoPaper.tesis_maestria.value,
    "tesis de doctorado": TipoPaper.tesis_doctorado.value,
    "tesis doctoral": TipoPaper.tesis_doctorado.value,
    "doctoral thesis": TipoPaper.tesis_doctorado.value,
    "tesis de licenciatura": TipoPaper.tesis_licenciatura.value,
    "tesis licenciatura": TipoPaper.tesis_licenciatura.value,
    "libro": TipoPaper.libro.value,
    "book": TipoPaper.libro.value,
    "capítulo de libro": TipoPaper.capitulo.value,
    "capitulo de libro": TipoPaper.capitulo.value,
    "book chapter": TipoPaper.capitulo.value,
    "conference paper": TipoPaper.memoria_congreso.value,
    "ponencia": TipoPaper.memoria_congreso.value,
    "reporte técnico": TipoPaper.reporte_tecnico.value,
    "reporte tecnico": TipoPaper.reporte_tecnico.value,
    "technical report": TipoPaper.reporte_tecnico.value,
    "preprint": TipoPaper.preprint.value,
}

_TIPOS_TESIS = {
    TipoPaper.tesis_maestria.value,
    TipoPaper.tesis_doctorado.value,
    TipoPaper.tesis_licenciatura.value,
}

_RE_AÑO = re.compile(r"\b(19|20)\d{2}\b")
_RE_DOI = re.compile(r"10\.\d{4,}/\S+")


class _OAINoDisponible(Exception):  # noqa: N818
    """OAI-PMH no disponible (503, XML inválido, error crítico)."""


def _mapear_tipo_riuat(tipo_texto: str) -> str:
    return _TIPO_RIUAT.get(tipo_texto.lower().strip(), TipoPaper.otro.value)


def _es_tesis(tipo: str) -> bool:
    return tipo in _TIPOS_TESIS


def _extraer_handle(identifier: str) -> str | None:
    """Extrae 'NNNN/N' de una URL o URN de handle DSpace."""
    m = re.search(r"(\d+/\d+)$", identifier.strip())
    return m.group(1) if m else None


def _extraer_doi_de_identifiers(identifiers: list[str]) -> str | None:
    """Busca y normaliza DOI en una lista de dc:identifier."""
    for ident in identifiers:
        m = _RE_DOI.search(ident)
        if m:
            return normalizar_doi(m.group(0).rstrip(".,;)>\"'"))
    return None


def _año_de_fecha(fecha: str) -> int | None:
    m = _RE_AÑO.search(fecha)
    return int(m.group(0)) if m else None


def parsear_oai_record(record_el: ET.Element) -> dict[str, Any] | None:
    """
    Parsea un elemento <record> OAI-PMH con metadatos Dublin Core.
    Devuelve None si el registro está marcado como deleted o sin metadata.
    """
    header = record_el.find("oai:header", _NS)
    if header is None:
        return None
    if header.get("status") == "deleted":
        return None

    identifier_el = header.find("oai:identifier", _NS)
    oai_identifier = (
        identifier_el.text.strip() if identifier_el is not None and identifier_el.text else ""
    )

    metadata = record_el.find("oai:metadata", _NS)
    if metadata is None:
        return None
    dc = metadata.find("oai_dc:dc", _NS)
    if dc is None:
        return None

    def _get(tag: str) -> str | None:
        el = dc.find(f"dc:{tag}", _NS)
        return el.text.strip() if el is not None and el.text else None

    def _get_all(tag: str) -> list[str]:
        return [
            el.text.strip() for el in dc.findall(f"dc:{tag}", _NS) if el.text and el.text.strip()
        ]

    titulo = _get("title") or ""
    creators = _get_all("creator")
    contributors = _get_all("contributor")
    descriptions = _get_all("description")
    dates = _get_all("date")
    tipos = _get_all("type")
    identifiers = _get_all("identifier")
    language = _get("language")

    tipo_texto = tipos[0] if tipos else ""
    tipo = _mapear_tipo_riuat(tipo_texto)
    es_tesis = _es_tesis(tipo)

    handle: str | None = None
    for ident in identifiers:
        if "handle" in ident:
            handle = _extraer_handle(ident)
            if handle:
                break

    doi = _extraer_doi_de_identifiers(identifiers)

    fecha = dates[0] if dates else None
    año = _año_de_fecha(fecha) if fecha else None
    abstract = descriptions[0] if descriptions else None

    return {
        "oai_identifier": oai_identifier,
        "handle_riuat": handle,
        "titulo": titulo,
        "titulo_normalizado": normalizar_titulo(titulo) if titulo else None,
        "autores_texto": "; ".join(creators) if creators else None,
        "directores_texto": "; ".join(contributors) if es_tesis and contributors else None,
        "abstract_texto": abstract,
        "año": año,
        "fecha_publicacion": fecha,
        "idioma": language,
        "tipo": tipo,
        "es_tesis": es_tesis,
        "doi": doi,
        "fuente_origen": TipoFuente.riuat.value,
    }


def parsear_html_handle(soup: BeautifulSoup, handle_id: str) -> dict[str, Any] | None:
    """
    Parsea la página DSpace de un handle individual (formato itemDisplayTable).
    Devuelve None si no contiene un item válido.
    """
    tabla = soup.find("table", class_="itemDisplayTable")
    if not tabla:
        return None

    campos: dict[str, list[str]] = {}
    for row in tabla.find_all("tr"):
        label_td = row.find("td", class_="metadataFieldLabel")
        value_td = row.find("td", class_="metadataFieldValue")
        if label_td is None or value_td is None:
            continue
        label = label_td.get_text(strip=True).rstrip(":").lower()
        valor = value_td.get_text(strip=True)
        if label and valor:
            campos.setdefault(label, []).append(valor)

    def _campo(*claves: str) -> str | None:
        for c in claves:
            vals = campos.get(c)
            if vals:
                return vals[0]
        return None

    def _campo_lista(*claves: str) -> list[str]:
        for c in claves:
            vals = campos.get(c)
            if vals:
                return vals
        return []

    titulo = _campo("dc.title", "title") or ""
    if not titulo:
        return None

    creators = _campo_lista("dc.contributor.author", "author")
    contributors = _campo_lista("dc.contributor.advisor", "advisor")
    tipo_texto = _campo("dc.type", "type") or ""
    fecha = _campo("dc.date.issued", "dc.date", "date")
    abstract = _campo("dc.description.abstract", "dc.description")
    language = _campo("dc.language.iso", "dc.language")
    identifiers_raw = campos.get("dc.identifier.uri") or []

    tipo = _mapear_tipo_riuat(tipo_texto)
    es_tesis = _es_tesis(tipo)
    año = _año_de_fecha(fecha) if fecha else None

    doi: str | None = None
    for ident in identifiers_raw:
        m = _RE_DOI.search(ident)
        if m:
            doi = normalizar_doi(m.group(0).rstrip(".,;)>\"'"))
            break

    return {
        "handle_riuat": handle_id,
        "titulo": titulo,
        "titulo_normalizado": normalizar_titulo(titulo),
        "autores_texto": "; ".join(creators) if creators else None,
        "directores_texto": "; ".join(contributors) if es_tesis and contributors else None,
        "abstract_texto": abstract,
        "año": año,
        "fecha_publicacion": fecha,
        "idioma": language,
        "tipo": tipo,
        "es_tesis": es_tesis,
        "doi": doi,
        "fuente_origen": TipoFuente.riuat.value,
    }


class RIUATHarvester(BaseHarvester):
    """
    Harvester del Repositorio Institucional UAT (DSpace).
    Primario: OAI-PMH. Fallback: scraping HTML de handles.
    """

    nombre = "RIUAT"
    fuente_tipo = TipoFuente.riuat.value
    rate_limit_requests_por_segundo = 0.5

    _base_url: str = _BASE_URL_DEFAULT
    _oai_endpoint: str = _OAI_ENDPOINT_DEFAULT
    _handle_prefix: str = _HANDLE_PREFIX_DEFAULT
    _handle_inicio: int = 1
    _handle_fin: int = 1000
    _timeout: float = 30.0
    _preferir_oai: bool = True
    _headers: dict[str, str] = {}

    def configurar(self, config: dict[str, Any]) -> None:
        self._base_url = config.get("base_url", _BASE_URL_DEFAULT).rstrip("/")
        self._oai_endpoint = config.get("oai_endpoint", _OAI_ENDPOINT_DEFAULT)
        self._handle_prefix = config.get("handle_prefix", _HANDLE_PREFIX_DEFAULT)
        self._handle_inicio = int(config.get("handle_inicio", 1))
        self._handle_fin = int(config.get("handle_fin", 1000))
        self._timeout = float(config.get("timeout_segundos", 30))
        self._preferir_oai = bool(config.get("preferir_oai", True))
        ua = config.get("user_agent", "IntellectClone/1.0 (uso institucional UAT)")
        self._headers = {"User-Agent": ua}

    def health_check(self) -> bool:
        try:
            resp = httpx.get(
                f"{self._base_url}{self._oai_endpoint}",
                params={"verb": "Identify"},
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
        log = logger.bind(cosecha_id=cosecha_id, modo=modo, fuente=self.fuente_tipo)

        if self._preferir_oai:
            try:
                log.info("riuat.oai_inicio")
                async for resultado in self._cosechar_oai(cosecha_id, parametros):
                    yield resultado
                return
            except _OAINoDisponible as exc:
                log.warning("riuat.oai_fallback", razon=str(exc))

        log.info("riuat.html_inicio")
        async for resultado in self._cosechar_html(cosecha_id, parametros):
            yield resultado

    async def _cosechar_oai(
        self,
        cosecha_id: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        log = logger.bind(cosecha_id=cosecha_id)
        intervalo = 1.0 / self.rate_limit_requests_por_segundo
        oai_url = f"{self._base_url}{self._oai_endpoint}"
        total = 0

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            params: dict[str, str] = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
            if "set" in parametros:
                params["set"] = str(parametros["set"])

            while True:
                await asyncio.sleep(intervalo)
                resp = await client.get(oai_url, params=params)

                if resp.status_code == 503:
                    raise _OAINoDisponible("OAI-PMH retornó 503")

                resp.raise_for_status()

                try:
                    root = ET.fromstring(resp.text)
                except ET.ParseError as exc:
                    raise _OAINoDisponible(f"XML inválido: {exc}") from exc

                # Verificar error OAI
                error_el = root.find("oai:error", _NS)
                if error_el is not None:
                    code = error_el.get("code", "")
                    if code == "noRecordsMatch":
                        break
                    raise _OAINoDisponible(f"Error OAI code={code}: {error_el.text}")

                list_records = root.find("oai:ListRecords", _NS)
                if list_records is None:
                    break

                for record_el in list_records.findall("oai:record", _NS):
                    datos = parsear_oai_record(record_el)
                    if datos is None:
                        continue
                    parsed = self.parsear_registro(datos)
                    yield ResultadoCosecha(
                        datos=parsed,
                        fuente_id=parsed.get("handle_riuat") or parsed.get("oai_identifier") or "",
                    )
                    total += 1

                token_el = list_records.find("oai:resumptionToken", _NS)
                token = (token_el.text or "").strip() if token_el is not None else ""
                if not token:
                    break

                log.debug("riuat.oai_pagina", total=total, token=token[:20])
                params = {"verb": "ListRecords", "resumptionToken": token}

        log.info("riuat.oai_fin", total=total)

    async def _cosechar_html(
        self,
        cosecha_id: str,
        parametros: dict[str, Any],
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        log = logger.bind(cosecha_id=cosecha_id)
        intervalo = 1.0 / self.rate_limit_requests_por_segundo
        total_visitados = 0
        encontrados = 0

        handle_inicio = int(parametros.get("handle_inicio", self._handle_inicio))
        handle_fin = int(parametros.get("handle_fin", self._handle_fin))

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            for n in range(handle_inicio, handle_fin + 1):
                handle_id = f"{self._handle_prefix}/{n}"
                await asyncio.sleep(intervalo)

                try:
                    resp = await client.get(f"{self._base_url}/handle/{handle_id}")
                except Exception as exc:
                    log.warning("riuat.html_error_red", handle_id=handle_id, error=str(exc))
                    continue

                total_visitados += 1

                if resp.status_code == 404:
                    continue
                if resp.status_code != 200:
                    log.warning(
                        "riuat.html_status_inesperado",
                        handle_id=handle_id,
                        status=resp.status_code,
                    )
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                datos = parsear_html_handle(soup, handle_id)
                if datos is None:
                    continue

                parsed = self.parsear_registro(datos)
                yield ResultadoCosecha(
                    datos=parsed,
                    fuente_id=parsed.get("handle_riuat") or handle_id,
                )
                encontrados += 1

        log.info("riuat.html_fin", visitados=total_visitados, encontrados=encontrados)

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Convierte metadatos Dublin Core al formato canónico del sistema."""
        return {
            "handle_riuat": raw_data.get("handle_riuat"),
            "oai_identifier": raw_data.get("oai_identifier"),
            "doi": raw_data.get("doi"),
            "titulo": raw_data.get("titulo", ""),
            "titulo_normalizado": raw_data.get("titulo_normalizado"),
            "autores_texto": raw_data.get("autores_texto"),
            "directores_texto": raw_data.get("directores_texto"),
            "abstract_texto": raw_data.get("abstract_texto"),
            "año": raw_data.get("año"),
            "fecha_publicacion": raw_data.get("fecha_publicacion"),
            "idioma": raw_data.get("idioma"),
            "tipo": raw_data.get("tipo", TipoPaper.otro.value),
            "es_tesis": raw_data.get("es_tesis", False),
            "fuente_origen": TipoFuente.riuat.value,
        }


registrar_harvester(TipoFuente.riuat.value, RIUATHarvester)
