"""
OpenAlexHarvester — fuente primaria de papers para IntellectClone.

Cobre tres modos: completa, incremental, persona_individual.
Paginación por cursor (200 works/página). Polite pool con email.
Se auto-registra al importar el módulo.
"""

from __future__ import annotations

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

_BASE_URL = "https://api.openalex.org"
_ROR_UAT_DEFAULT = "https://ror.org/04hhneb29"
_PER_PAGE = 200

_OPENALEX_TIPO: dict[str, str] = {
    "journal-article": TipoPaper.articulo.value,
    "article": TipoPaper.articulo.value,
    "book-chapter": TipoPaper.capitulo.value,
    "book": TipoPaper.libro.value,
    "dissertation": TipoPaper.tesis_doctorado.value,
    "proceedings-article": TipoPaper.memoria_congreso.value,
    "report": TipoPaper.reporte_tecnico.value,
    "preprint": TipoPaper.preprint.value,
}


def reconstruir_abstract(inverted_index: dict[str, list[int]]) -> str:
    """
    Reconstruye el abstract desde el inverted index de OpenAlex.

    Formato de entrada: {"palabra": [pos1, pos2, ...], ...}
    Devuelve cadena vacía si el índice está vacío o es inválido.
    """
    if not inverted_index:
        return ""
    posiciones: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            posiciones[pos] = word
    return " ".join(posiciones[i] for i in sorted(posiciones))


def _mapear_tipo(openalex_type: str) -> str:
    return _OPENALEX_TIPO.get(openalex_type.lower(), TipoPaper.otro.value)


def _extraer_openalex_id(url: str) -> str:
    return url.split("/")[-1] if url else ""


def _ror_sin_prefijo(ror_url: str) -> str:
    return ror_url.replace("https://ror.org/", "").strip("/")


class OpenAlexHarvester(BaseHarvester):
    """Harvester para la API pública de OpenAlex."""

    nombre = "OpenAlex"
    fuente_tipo = TipoFuente.openalex.value
    rate_limit_requests_por_segundo = 10.0

    # Configurados en configurar()
    _email: str = ""
    _ror_id: str = _ROR_UAT_DEFAULT
    _max_works: int = 10000
    _headers: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Interfaz BaseHarvester
    # ------------------------------------------------------------------

    def configurar(self, config: dict[str, Any]) -> None:
        self._email = config.get("polite_pool_email", "")
        self._ror_id = config.get("ror_id_uat", _ROR_UAT_DEFAULT)
        self._max_works = int(config.get("max_works_por_corrida", 10000))
        ua = config.get("user_agent", "IntellectClone/1.0")
        if self._email:
            ua = f"{ua} (mailto:{self._email})"
        self._headers = {"User-Agent": ua}

    def health_check(self) -> bool:
        ror = _ror_sin_prefijo(self._ror_id)
        try:
            resp = httpx.get(
                f"{_BASE_URL}/works",
                params={"filter": f"institutions.ror:{ror}", "per-page": 1},
                headers=self._headers,
                timeout=10.0,
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
        Generador async que emite un ResultadoCosecha por cada work de OpenAlex.

        Paginación con cursor: itera hasta agotar resultados o alcanzar max_works.
        """
        filter_str = self._construir_filtro(modo, parametros)
        cursor = "*"
        total = 0

        log = logger.bind(
            cosecha_id=cosecha_id,
            modo=modo,
            fuente=self.fuente_tipo,
        )
        log.info("openalex.cosecha_inicio", filter=filter_str)

        async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
            while True:
                params: dict[str, Any] = {
                    "filter": filter_str,
                    "per-page": _PER_PAGE,
                    "cursor": cursor,
                }

                resp = await client.get(f"{_BASE_URL}/works", params=params)
                resp.raise_for_status()

                data: dict[str, Any] = resp.json()
                works: list[dict[str, Any]] = data.get("results") or []
                meta: dict[str, Any] = data.get("meta") or {}

                log.debug("openalex.pagina", n_works=len(works), cursor=cursor)

                for work in works:
                    parsed = self.parsear_registro(work)
                    yield ResultadoCosecha(
                        datos=parsed,
                        fuente_id=parsed.get("openalex_id") or work.get("id") or "",
                    )
                    total += 1
                    if total >= self._max_works:
                        log.info("openalex.limite_alcanzado", total=total)
                        return

                next_cursor: str | None = meta.get("next_cursor")
                if not next_cursor or not works:
                    break
                cursor = next_cursor

        log.info("openalex.cosecha_fin", total=total)

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Convierte un work de OpenAlex al formato canónico del sistema."""
        openalex_id = _extraer_openalex_id(raw_data.get("id") or "")

        doi_raw: str = raw_data.get("doi") or ""
        doi = normalizar_doi(doi_raw) if doi_raw else None

        titulo: str = raw_data.get("title") or ""
        titulo_normalizado = normalizar_titulo(titulo) if titulo else None

        inv_index: dict[str, list[int]] = raw_data.get("abstract_inverted_index") or {}
        abstract_texto = reconstruir_abstract(inv_index) or None

        primary_location: dict[str, Any] = raw_data.get("primary_location") or {}
        source: dict[str, Any] = primary_location.get("source") or {}
        biblio: dict[str, Any] = raw_data.get("biblio") or {}
        oa_info: dict[str, Any] = raw_data.get("open_access") or {}

        first_page: str = biblio.get("first_page") or ""
        last_page: str = biblio.get("last_page") or ""
        if first_page and last_page:
            paginas: str | None = f"{first_page}-{last_page}"
        else:
            paginas = first_page or last_page or None

        counts_by_year: list[dict[str, Any]] = raw_data.get("counts_by_year") or []
        citas_por_año: dict[str, int] | None = {
            str(item["year"]): item["cited_by_count"] for item in counts_by_year if "year" in item
        } or None

        conceptos_raw: list[dict[str, Any]] = raw_data.get("concepts") or []
        conceptos: list[str] | None = [
            c["display_name"] for c in conceptos_raw if c.get("display_name")
        ] or None

        return {
            "openalex_id": openalex_id,
            "doi": doi,
            "titulo": titulo,
            "titulo_normalizado": titulo_normalizado,
            "abstract_texto": abstract_texto,
            "año": raw_data.get("publication_year"),
            "fecha_publicacion": raw_data.get("publication_date"),
            "idioma": raw_data.get("language"),
            "revista": source.get("display_name"),
            "issn": source.get("issn_l"),
            "editorial": source.get("host_organization"),
            "volumen": biblio.get("volume"),
            "numero": biblio.get("issue"),
            "paginas": paginas,
            "open_access": bool(oa_info.get("is_oa", False)),
            "url_pdf": primary_location.get("pdf_url"),
            "url_landing": primary_location.get("landing_page_url"),
            "total_citas": raw_data.get("cited_by_count", 0),
            "citas_por_año": citas_por_año,
            "conceptos": conceptos,
            "tipo": _mapear_tipo(raw_data.get("type") or ""),
            "fuente_origen": TipoFuente.openalex.value,
            "autorships": raw_data.get("authorships") or [],
        }

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _construir_filtro(self, modo: str, parametros: dict[str, Any]) -> str:
        ror = _ror_sin_prefijo(self._ror_id)
        if modo == "completa":
            return f"institutions.ror:{ror}"
        if modo == "incremental":
            desde = parametros.get("desde_fecha", "")
            return f"institutions.ror:{ror},from_publication_date:{desde}"
        if modo == "persona_individual":
            author_id: str = parametros.get("author_id", "")
            return f"author.id:{author_id}"
        return f"institutions.ror:{ror}"


# Auto-registro al importar
registrar_harvester(TipoFuente.openalex.value, OpenAlexHarvester)
