"""
SNIIUATHarvester — Sistema Nacional de Investigadores, página UAT.

Cosecha datos de cuerpos académicos y membresía SNII desde
produccioncientifica.uat.edu.mx usando Playwright headless.

Dos modos:
  - campus_ca: CampusCA.aspx — cuerpos académicos por campus
  - buscador_snii: Buscador.aspx — investigadores con nivel SNII
  - completo: ambos modos en secuencia

Rate limit: 3 segundos entre navegaciones. Se auto-registra al importar.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.runner import registrar_harvester
from intellectclone.harvesters.tipos import ResultadoCosecha
from intellectclone.models.enums import NivelSnii, TipoFuente

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_BASE_URL_DEFAULT = "https://produccioncientifica.uat.edu.mx"
_URL_CAMPUS_CA = "/CampusCA.aspx"
_URL_BUSCADOR = "/Buscador.aspx"

_SEL_CAMPUS = "#ContentPlaceHolder1_ddlCampus"
_SEL_DEPENDENCIA = "#ContentPlaceHolder1_ddlDependencia"
_SEL_BTN_BUSCAR = "#ContentPlaceHolder1_btnBuscar"
_TABLE_CA = "ContentPlaceHolder1_GridView1"
_TABLE_BUSCADOR = "ContentPlaceHolder1_GridViewInvestigadores"

_GRADO_CA: dict[str, str] = {
    "consolidado": "consolidado",
    "en consolidación": "en_consolidacion",
    "en consolidacion": "en_consolidacion",
    "en formación": "en_formacion",
    "en formacion": "en_formacion",
}

_NIVEL_SNII: dict[str, str] = {
    "candidato": NivelSnii.candidato.value,
    "nivel i": NivelSnii.nivel_1.value,
    "nivel 1": NivelSnii.nivel_1.value,
    "nivel ii": NivelSnii.nivel_2.value,
    "nivel 2": NivelSnii.nivel_2.value,
    "nivel iii": NivelSnii.nivel_3.value,
    "nivel 3": NivelSnii.nivel_3.value,
    "emérito": NivelSnii.emerito.value,
    "emerito": NivelSnii.emerito.value,
}


class _AntiScrapingError(Exception):  # noqa: N818
    """Sitio detectó scraping (captcha, bloqueo activo)."""


def detectar_captcha(html: str) -> bool:
    """True si la página presenta un desafío captcha."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.find(class_="g-recaptcha"):
        return True
    if soup.find(id="challenge-container"):
        return True
    return bool(soup.find("img", {"src": lambda s: bool(s and "captcha" in s.lower())}))


def detectar_tabla(html: str, table_id: str) -> bool:
    """True si la página contiene la tabla GridView con el id dado."""
    soup = BeautifulSoup(html, "html.parser")
    return bool(soup.find("table", id=table_id))


def parsear_tabla_campus_ca(html: str) -> list[dict[str, Any]]:
    """
    Parsea ContentPlaceHolder1_GridView1 de CampusCA.aspx.
    Devuelve lista de registros de cuerpos académicos.
    """
    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table", id=_TABLE_CA)
    if tabla is None:
        return []

    encabezados: list[str] = []
    registros: list[dict[str, Any]] = []

    for i, fila in enumerate(tabla.find_all("tr")):
        celdas = fila.find_all(["th", "td"])
        if not celdas:
            continue

        if i == 0:
            encabezados = [c.get_text(strip=True).lower() for c in celdas]
            continue

        if len(celdas) == 1:
            continue

        if len(celdas) < len(encabezados):
            continue

        fila_dict: dict[str, str] = {
            encabezados[j]: celdas[j].get_text(strip=True) for j in range(len(encabezados))
        }

        nombre_ca = fila_dict.get("nombre del ca", "").strip()
        if not nombre_ca:
            continue

        grado_raw = fila_dict.get("grado de consolidación", "").strip()
        grado = _GRADO_CA.get(grado_raw.lower(), grado_raw.lower() or None)

        registros.append(
            {
                "tipo_registro": "cuerpo_academico",
                "campus": fila_dict.get("campus", "").strip() or None,
                "nombre_ca": nombre_ca,
                "clave_ca": fila_dict.get("clave", "").strip() or None,
                "grado_consolidacion": grado,
                "area_conocimiento": fila_dict.get("disciplina", "").strip() or None,
                "responsable": fila_dict.get("responsable", "").strip() or None,
                "fuente_origen": TipoFuente.snii_uat.value,
            }
        )

    return registros


def parsear_tabla_buscador(html: str) -> list[dict[str, Any]]:
    """
    Parsea ContentPlaceHolder1_GridViewInvestigadores de Buscador.aspx.
    Devuelve lista de registros de investigadores SNII.
    """
    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table", id=_TABLE_BUSCADOR)
    if tabla is None:
        return []

    encabezados: list[str] = []
    registros: list[dict[str, Any]] = []

    for i, fila in enumerate(tabla.find_all("tr")):
        celdas = fila.find_all(["th", "td"])
        if not celdas:
            continue

        if i == 0:
            encabezados = [c.get_text(strip=True).lower() for c in celdas]
            continue

        if len(celdas) == 1:
            continue

        if len(celdas) < len(encabezados):
            continue

        fila_dict: dict[str, str] = {
            encabezados[j]: celdas[j].get_text(strip=True) for j in range(len(encabezados))
        }

        nombre = fila_dict.get("nombre del investigador", "").strip()
        if not nombre:
            continue

        nivel_raw = fila_dict.get("nivel snii", "").strip()
        nivel_snii = _NIVEL_SNII.get(nivel_raw.lower())

        vigencia_texto = fila_dict.get("vigencia", "").strip()
        vigencia: int | None = int(vigencia_texto) if vigencia_texto.isdigit() else None

        registros.append(
            {
                "tipo_registro": "investigador_snii",
                "nombre_completo": nombre,
                "campus": fila_dict.get("campus", "").strip() or None,
                "nombre_ca": fila_dict.get("cuerpo académico", "").strip() or None,
                "nivel_snii": nivel_snii,
                "vigencia_snii": vigencia,
                "fuente_origen": TipoFuente.snii_uat.value,
            }
        )

    return registros


def extraer_pagina_siguiente(html: str, pagina_actual: int) -> int | None:
    """
    Devuelve el número de la siguiente página si existe enlace de paginación,
    o None si no hay más páginas.
    """
    pagina_buscada = pagina_actual + 1
    soup = BeautifulSoup(html, "html.parser")
    for enlace in soup.find_all("a", href=True):
        href = str(enlace.get("href", ""))
        if "__doPostBack" in href and f"Page${pagina_buscada}" in href:
            return pagina_buscada
    return None


class SNIIUATHarvester(BaseHarvester):
    """
    Harvester de produccioncientifica.uat.edu.mx.
    Usa Playwright headless para manejar ASP.NET WebForms con AJAX.
    """

    nombre = "SNII-UAT"
    fuente_tipo = TipoFuente.snii_uat.value
    rate_limit_requests_por_segundo = 1.0 / 3.0

    _base_url: str = _BASE_URL_DEFAULT
    _timeout_ms: int = 30_000

    def configurar(self, config: dict[str, Any]) -> None:
        self._base_url = config.get("base_url", _BASE_URL_DEFAULT).rstrip("/")
        self._timeout_ms = int(config.get("timeout_ms", 30_000))

    def health_check(self) -> bool:
        try:
            resp = httpx.get(
                f"{self._base_url}{_URL_CAMPUS_CA}",
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

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                if modo in ("campus_ca", "completo"):
                    log.info("snii_uat.campus_ca_inicio")
                    async for resultado in self._cosechar_campus_ca(browser, cosecha_id):
                        yield resultado

                if modo in ("buscador_snii", "completo"):
                    log.info("snii_uat.buscador_inicio")
                    async for resultado in self._cosechar_buscador(browser, cosecha_id):
                        yield resultado
            finally:
                await browser.close()

    async def _cosechar_campus_ca(
        self,
        browser: Any,
        cosecha_id: str,
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        log = logger.bind(cosecha_id=cosecha_id, tabla="campus_ca")
        intervalo = 1.0 / self.rate_limit_requests_por_segundo
        total = 0

        page = await browser.new_page()
        try:
            await page.goto(
                f"{self._base_url}{_URL_CAMPUS_CA}",
                timeout=self._timeout_ms,
                wait_until="networkidle",
            )
            html_inicial = await page.content()

            if detectar_captcha(html_inicial):
                raise _AntiScrapingError("Captcha detectado en CampusCA.aspx")

            opciones: list[dict[str, str]] = await page.eval_on_selector_all(
                f"{_SEL_CAMPUS} option",
                "opts => opts.map(o => ({value: o.value, text: o.innerText.trim()}))",
            )

            for opcion in opciones:
                valor = opcion.get("value", "").strip()
                if not valor:
                    continue

                await asyncio.sleep(intervalo)
                await page.select_option(_SEL_CAMPUS, valor)
                await page.click(_SEL_BTN_BUSCAR)
                await page.wait_for_load_state("networkidle", timeout=self._timeout_ms)

                pagina = 1
                while True:
                    html = await page.content()

                    if detectar_captcha(html):
                        raise _AntiScrapingError(f"Captcha detectado al filtrar campus={valor!r}")

                    if not detectar_tabla(html, _TABLE_CA):
                        log.info(
                            "snii_uat.campus_ca_sin_tabla",
                            campus=opcion.get("text"),
                        )
                        break

                    for reg in parsear_tabla_campus_ca(html):
                        parsed = self.parsear_registro(reg)
                        yield ResultadoCosecha(
                            datos=parsed,
                            fuente_id=parsed.get("clave_ca") or parsed.get("nombre_ca") or "",
                        )
                        total += 1

                    siguiente = extraer_pagina_siguiente(html, pagina)
                    if siguiente is None:
                        break

                    await asyncio.sleep(intervalo)
                    clicked: bool = await page.evaluate(
                        f"() => {{ const links = document.querySelectorAll('a');"
                        f" for (const l of links) {{"
                        f" if (l.href && l.href.includes('Page${siguiente}'))"
                        f" {{ l.click(); return true; }} }} return false; }}"
                    )
                    if not clicked:
                        break
                    await page.wait_for_load_state("networkidle", timeout=self._timeout_ms)
                    pagina = siguiente

        finally:
            await page.close()

        log.info("snii_uat.campus_ca_fin", total=total)

    async def _cosechar_buscador(
        self,
        browser: Any,
        cosecha_id: str,
    ) -> AsyncGenerator[ResultadoCosecha, None]:
        log = logger.bind(cosecha_id=cosecha_id, tabla="buscador_snii")
        intervalo = 1.0 / self.rate_limit_requests_por_segundo
        total = 0

        page = await browser.new_page()
        try:
            await page.goto(
                f"{self._base_url}{_URL_BUSCADOR}",
                timeout=self._timeout_ms,
                wait_until="networkidle",
            )
            html_inicial = await page.content()

            if detectar_captcha(html_inicial):
                raise _AntiScrapingError("Captcha detectado en Buscador.aspx")

            opciones: list[dict[str, str]] = await page.eval_on_selector_all(
                f"{_SEL_DEPENDENCIA} option",
                "opts => opts.map(o => ({value: o.value, text: o.innerText.trim()}))",
            )

            for opcion in opciones:
                valor = opcion.get("value", "").strip()
                if not valor:
                    continue

                await asyncio.sleep(intervalo)
                await page.select_option(_SEL_DEPENDENCIA, valor)
                await page.click(_SEL_BTN_BUSCAR)
                await page.wait_for_load_state("networkidle", timeout=self._timeout_ms)

                pagina = 1
                while True:
                    html = await page.content()

                    if detectar_captcha(html):
                        raise _AntiScrapingError(
                            f"Captcha detectado al filtrar dependencia={valor!r}"
                        )

                    if not detectar_tabla(html, _TABLE_BUSCADOR):
                        log.info(
                            "snii_uat.buscador_sin_tabla",
                            dependencia=opcion.get("text"),
                        )
                        break

                    for reg in parsear_tabla_buscador(html):
                        parsed = self.parsear_registro(reg)
                        yield ResultadoCosecha(
                            datos=parsed,
                            fuente_id=parsed.get("nombre_completo") or "",
                        )
                        total += 1

                    siguiente = extraer_pagina_siguiente(html, pagina)
                    if siguiente is None:
                        break

                    await asyncio.sleep(intervalo)
                    clicked = await page.evaluate(
                        f"() => {{ const links = document.querySelectorAll('a');"
                        f" for (const l of links) {{"
                        f" if (l.href && l.href.includes('Page${siguiente}'))"
                        f" {{ l.click(); return true; }} }} return false; }}"
                    )
                    if not clicked:
                        break
                    await page.wait_for_load_state("networkidle", timeout=self._timeout_ms)
                    pagina = siguiente

        finally:
            await page.close()

        log.info("snii_uat.buscador_fin", total=total)

    def parsear_registro(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Pasa el registro ya normalizado al formato canónico."""
        return dict(raw_data)


registrar_harvester(TipoFuente.snii_uat.value, SNIIUATHarvester)
