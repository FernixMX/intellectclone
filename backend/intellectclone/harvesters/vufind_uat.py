"""
VuFindUATHarvester — cosechador HTML para publicaciones.uat.edu.mx/vufind.

La API REST está bloqueada (403); cosecha por scraping HTML estructurado.
Rate limit 1 rps para respetar el servidor UAT.
Se auto-registra al importar el módulo.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import urljoin

import httpx
import structlog
from bs4 import BeautifulSoup, Tag

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.normalizer import normalizar_doi, normalizar_titulo
from intellectclone.harvesters.runner import registrar_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import TipoFuente, TipoPaper

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_BASE_URL_DEFAULT = "https://publicaciones.uat.edu.mx/vufind"
_RESULTADOS_POR_PAGINA = 20

_TIPO_VUFIND: dict[str, str] = {
    "artículo": TipoPaper.articulo.value,
    "articulo": TipoPaper.articulo.value,
    "article": TipoPaper.articulo.value,
    "tesis doctoral": TipoPaper.tesis_doctorado.value,
    "tesis de doctorado": TipoPaper.tesis_doctorado.value,
    "doctoral thesis": TipoPaper.tesis_doctorado.value,
    "tesis maestría": TipoPaper.tesis_maestria.value,
    "tesis de maestría": TipoPaper.tesis_maestria.value,
    "tesis de maestria": TipoPaper.tesis_maestria.value,
    "master thesis": TipoPaper.tesis_maestria.value,
    "tesis licenciatura": TipoPaper.tesis_licenciatura.value,
    "tesis de licenciatura": TipoPaper.tesis_licenciatura.value,
    "libro": TipoPaper.libro.value,
    "book": TipoPaper.libro.value,
    "capítulo": TipoPaper.capitulo.value,
    "capitulo": TipoPaper.capitulo.value,
    "chapter": TipoPaper.capitulo.value,
    "capítulo de libro": TipoPaper.capitulo.value,
    "capitulo de libro": TipoPaper.capitulo.value,
    "memoria de congreso": TipoPaper.memoria_congreso.value,
    "conference paper": TipoPaper.memoria_congreso.value,
    "reporte técnico": TipoPaper.reporte_tecnico.value,
    "reporte tecnico": TipoPaper.reporte_tecnico.value,
    "preprint": TipoPaper.preprint.value,
}


def _mapear_tipo_vufind(tipo_texto: str) -> str:
    return _TIPO_VUFIND.get(tipo_texto.lower().strip(), TipoPaper.otro.value)


def _extraer_record_id(href: str) -> str:
    """Extrae el record_id del path /vufind/Record/{id}."""
    partes = href.rstrip("/").split("/")
    return partes[-1] if partes else ""


def _extraer_doi_de_texto(texto: str) -> str | None:
    """Busca un DOI en un fragmento de texto o URL."""
    match = re.search(r"10\.\d{4,}/\S+", texto)
    return match.group(0).rstrip(".,;)>\"'") if match else None


def _extraer_año(texto: str) -> int | None:
    m = re.search(r"\b(19|20)\d{2}\b", texto)
    return int(m.group(0)) if m else None


def _extraer_año_coins(card: Tag) -> int | None:
    """Extrae año de los metadatos COinS (span.Z3988 title=rft.date=YYYY)."""
    z = card.find("span", class_="Z3988")
    if z:
        m = re.search(r"rft\.date=(\d{4})", z.get("title", ""))
        if m:
            return int(m.group(1))
    return None


def parsear_card(card: Tag, base_url: str) -> dict[str, Any]:
    """
    Extrae metadatos básicos de un elemento `<li class="result">` de VuFind.

    VuFind UAT usa <li class="result">, no <div class="result">.
    El año viene en los metadatos COinS (span.Z3988) o en <div>Published YYYY</div>.
    """
    # record_id: preferir input.hiddenId, fallback al href del enlace de portada/título
    hidden_id = card.find("input", class_="hiddenId")
    if hidden_id:
        record_id = str(hidden_id.get("value", "")).strip()
    else:
        titulo_tag = card.find("a", class_="title")
        href: str = titulo_tag.get("href", "") if titulo_tag else ""
        record_id = _extraer_record_id(href)

    url_detalle = urljoin(base_url.rstrip("/") + "/", f"Record/{record_id}") if record_id else None

    # Título: <a class="title ...">
    titulo_tag = card.find("a", class_="title")
    titulo: str = titulo_tag.get_text(strip=True) if titulo_tag else ""

    # Formato: <span class="format ...">
    formato_tag = card.find(class_="format")
    tipo_texto: str = formato_tag.get_text(strip=True) if formato_tag else ""

    # Autor: presente sólo en lista si la plantilla lo incluye
    autor_tag = card.find("span", class_=re.compile(r"summaryAuthor|author", re.I))
    autores_texto: str | None = autor_tag.get_text(strip=True) if autor_tag else None

    # Año: COinS (rft.date) → "Published YYYY" → regex en texto completo
    año: int | None = _extraer_año_coins(card)
    if año is None:
        for div in card.find_all("div"):
            texto = div.get_text(strip=True)
            if re.match(r"^Published\s+\d{4}", texto, re.I):
                año = _extraer_año(texto)
                break
    if año is None:
        año = _extraer_año(card.get_text(" "))

    return {
        "vufind_id": record_id,
        "url_detalle": url_detalle,
        "titulo": titulo,
        "titulo_normalizado": normalizar_titulo(titulo) if titulo else None,
        "autores_texto": autores_texto,
        "año": año,
        "tipo": _mapear_tipo_vufind(tipo_texto),
        "fuente_origen": TipoFuente.vufind_uat.value,
    }


def parsear_detalle(soup: BeautifulSoup, base_url: str, vufind_id: str) -> dict[str, Any]:
    """
    Extrae metadatos completos de la página de detalle de un registro VuFind.
    """
    titulo_tag = soup.find("h1", class_="record-title") or soup.find("h1")
    titulo: str = titulo_tag.get_text(strip=True) if titulo_tag else ""
    autor_tags = soup.find_all(["span", "a"], class_="author")
    autores_texto: str | None = "; ".join(t.get_text(strip=True) for t in autor_tags) or None

    año: int | None = None
    tipo_texto = ""
    doi_texto: str | None = None
    url_landing: str | None = None
    revista: str | None = None

    for dt in soup.find_all("dt"):
        label = dt.get_text(strip=True).lower().rstrip(":")
        dd = dt.find_next_sibling("dd")
        if dd is None:
            continue
        valor: str = dd.get_text(strip=True)
        if label in ("año", "año de publicación", "year", "fecha", "published"):
            año = _extraer_año(valor)
        elif label in ("tipo", "type", "formato", "format"):
            tipo_texto = valor
        elif label == "doi":
            doi_link = dd.find("a")
            doi_texto = doi_link.get("href", valor) if doi_link else valor
        elif label in ("fuente", "revista", "journal", "source", "publicado en"):
            revista = valor

    if doi_texto is None:
        doi_link_global = soup.find("a", href=re.compile(r"doi\.org", re.I))
        if doi_link_global:
            doi_texto = doi_link_global.get("href", "")

    fulltext_tag = soup.find("a", class_="fulltext-link")
    if not fulltext_tag:
        fulltext_tag = soup.find("a", string=re.compile(r"texto completo|fulltext|pdf", re.I))
    if fulltext_tag:
        url_landing = fulltext_tag.get("href")

    doi: str | None = None
    if doi_texto:
        doi_clean = _extraer_doi_de_texto(doi_texto)
        if doi_clean:
            doi = normalizar_doi(doi_clean)

    return {
        "vufind_id": vufind_id,
        "titulo": titulo,
        "titulo_normalizado": normalizar_titulo(titulo) if titulo else None,
        "autores_texto": autores_texto,
        "año": año,
        "tipo": _mapear_tipo_vufind(tipo_texto),
        "doi": doi,
        "url_landing": url_landing,
        "revista": revista,
        "fuente_origen": TipoFuente.vufind_uat.value,
    }


def _tiene_siguiente_pagina(soup: BeautifulSoup) -> bool:
    """Devuelve True si existe un enlace de página siguiente en la paginación.

    VuFind UAT usa <a class="page-next"> o texto "Next"/"Siguiente".
    """
    if soup.find("a", rel="next"):
        return True
    if soup.find("a", class_="page-next"):
        return True
    for a in soup.find_all("a"):
        texto = a.get_text(strip=True).lower()
        if texto in ("siguiente", "next", "›", "»", ">"):
            return True
    return False


class VuFindUATHarvester(BaseHarvester):
    """Harvester HTML para el catálogo VuFind de la UAT."""

    nombre = "VuFind UAT"
    fuente_tipo = TipoFuente.vufind_uat.value
    rate_limit_requests_por_segundo = 1.0

    _base_url: str = _BASE_URL_DEFAULT
    _max_paginas: int = 100
    _timeout: float = 30.0
    _headers: dict[str, str] = {}
    _fetch_detalle: bool = False

    def configurar(self, config: dict[str, Any]) -> None:
        self._base_url = config.get("base_url", _BASE_URL_DEFAULT).rstrip("/")
        self._max_paginas = int(config.get("max_paginas_por_corrida", 100))
        self._timeout = float(config.get("timeout_segundos", 30))
        self._fetch_detalle = bool(config.get("fetch_detalle", False))
        ua = config.get("user_agent", "IntellectClone/1.0 (uso institucional UAT)")
        self._headers = {"User-Agent": ua}

    def health_check(self) -> bool:
        try:
            resp = httpx.get(
                f"{self._base_url}/Search/Results",
                params={"lookfor": "", "type": "AllFields", "limit": 1, "page": 1},
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
        Generador async que itera páginas de resultados VuFind y emite un
        ResultadoCosecha por cada registro encontrado.
        """
        log = logger.bind(cosecha_id=cosecha_id, modo=modo, fuente=self.fuente_tipo)
        log.info("vufind.cosecha_inicio")

        pagina = 1
        total = 0
        intervalo = 1.0 / self.rate_limit_requests_por_segundo

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=self._timeout,
            follow_redirects=True,
        ) as client:
            while pagina <= self._max_paginas:
                await asyncio.sleep(intervalo)

                params: dict[str, Any] = {
                    "lookfor": parametros.get("lookfor", ""),
                    "type": "AllFields",
                    "limit": _RESULTADOS_POR_PAGINA,
                    "page": pagina,
                }
                resp = await client.get(f"{self._base_url}/Search/Results", params=params)
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")
                # VuFind UAT usa <li class="result">, no <div class="result">
                cards = soup.find_all("li", class_="result")
                log.debug("vufind.pagina", pagina=pagina, n_cards=len(cards))

                if not cards:
                    break

                for card in cards:
                    datos = parsear_card(card, self._base_url)
                    if not datos.get("vufind_id"):
                        continue

                    if self._fetch_detalle and datos.get("url_detalle"):
                        await asyncio.sleep(intervalo)
                        try:
                            resp_det = await client.get(datos["url_detalle"])
                            resp_det.raise_for_status()
                            soup_det = BeautifulSoup(resp_det.text, "html.parser")
                            detalle = parsear_detalle(soup_det, self._base_url, datos["vufind_id"])
                            datos.update({k: v for k, v in detalle.items() if v is not None})
                        except Exception as exc:
                            log.warning(
                                "vufind.detalle_error",
                                vufind_id=datos["vufind_id"],
                                error=str(exc),
                            )

                    parsed = self.parsear_registro(datos)
                    yield ResultadoCosecha(
                        datos=parsed,
                        fuente_id=parsed.get("vufind_id") or "",
                    )
                    total += 1

                if not _tiene_siguiente_pagina(soup):
                    break
                pagina += 1

        log.info("vufind.cosecha_fin", total=total)

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Convierte los datos extraídos al formato canónico del sistema."""
        return {
            "vufind_id": raw_data.get("vufind_id"),
            "doi": raw_data.get("doi"),
            "titulo": raw_data.get("titulo", ""),
            "titulo_normalizado": raw_data.get("titulo_normalizado"),
            "autores_texto": raw_data.get("autores_texto"),
            "año": raw_data.get("año"),
            "tipo": raw_data.get("tipo", TipoPaper.otro.value),
            "revista": raw_data.get("revista"),
            "url_landing": raw_data.get("url_landing"),
            "fuente_origen": TipoFuente.vufind_uat.value,
        }


registrar_harvester(TipoFuente.vufind_uat.value, VuFindUATHarvester)
