"""
Paquete harvesters de IntellectClone.

Exporta la API pública: BaseHarvester, tipos auxiliares, runner y harvesters concretos.
Importar harvesters concretos aquí activa su auto-registro en el registry.
"""

from intellectclone.harvesters.base import BaseHarvester
from intellectclone.harvesters.deduplicator import ResultadoDeduplicacion, deduplicar_paper
from intellectclone.harvesters.disambiguator import ResultadoDesambiguacion, desambiguar_autor
from intellectclone.harvesters.normalizer import (
    normalizar_doi,
    normalizar_nombre,
    normalizar_titulo,
    ratio_similitud,
)
from intellectclone.harvesters.openalex import OpenAlexHarvester, reconstruir_abstract
from intellectclone.harvesters.runner import (
    ejecutar_cosecha,
    obtener_harvester,
    registrar_harvester,
)
from intellectclone.harvesters.tipos import (
    AccionIntento,
    NivelError,
    ResultadoCosecha,
    ResultadoIntento,
)
from intellectclone.harvesters.vufind_uat import VuFindUATHarvester

__all__ = [
    "AccionIntento",
    "BaseHarvester",
    "NivelError",
    "OpenAlexHarvester",
    "VuFindUATHarvester",
    "ResultadoCosecha",
    "ResultadoDeduplicacion",
    "ResultadoDesambiguacion",
    "ResultadoIntento",
    "deduplicar_paper",
    "desambiguar_autor",
    "ejecutar_cosecha",
    "normalizar_doi",
    "normalizar_nombre",
    "normalizar_titulo",
    "obtener_harvester",
    "ratio_similitud",
    "reconstruir_abstract",
    "registrar_harvester",
]
