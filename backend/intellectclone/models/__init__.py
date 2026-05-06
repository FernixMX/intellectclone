"""
Modelos ORM de IntellectClone.
Este módulo importa todos los modelos para que Alembic los detecte en autogenerate.
El orden de importación respeta las dependencias entre tablas.
"""

# Primero: enumeraciones (sin dependencias)
# Octavo: auxiliares (FK a gemelo, usuario_sistema)
from intellectclone.models.auxiliares import (
    ConfiguracionPresupuesto,
    ConsumoLlm,
    ExportToken,
    TemaTroncoComun,
    ValidacionGemelo,
)
from intellectclone.models.enums import (
    EstadoCosecha,
    EstadoDocumento,
    EstadoGemelo,
    EstadoSimulacion,
    IntensidadRespuesta,
    NivelRasgo,
    NivelSnii,
    PosturaRespuesta,
    RolUsuario,
    TipoDocumentoCorpus,
    TipoFuente,
    TipoPaper,
    TipoPersona,
)

# Sexto: gemelos (FK a persona, paper, documento_corpus)
from intellectclone.models.gemelo import Gemelo, GemeloCorpusUso

# Segundo: estructura institucional (sin FK entre sí excepto self-ref en area_conocimiento)
from intellectclone.models.institucional import AreaConocimiento, CuerpoAcademico, Dependencia

# Tercero: personas (FK a institucional)
from intellectclone.models.persona import Persona, PersonaArea, PersonaDependenciaHistorico

# Cuarto: producción académica (FK a persona)
from intellectclone.models.produccion import Coautoria, DocumentoCorpus, Paper

# Séptimo: simulaciones (FK a gemelo, persona, usuario_sistema)
from intellectclone.models.simulacion import RespuestaSimulacion, Simulacion

# Quinto: sistema (FK a persona — UsuarioSistema; cosecha referenciada desde paper)
from intellectclone.models.sistema import Auditoria, Cosecha, UsuarioSistema

__all__ = [
    # Enums
    "EstadoCosecha",
    "EstadoDocumento",
    "EstadoGemelo",
    "EstadoSimulacion",
    "IntensidadRespuesta",
    "NivelRasgo",
    "NivelSnii",
    "PosturaRespuesta",
    "RolUsuario",
    "TipoDocumentoCorpus",
    "TipoFuente",
    "TipoPaper",
    "TipoPersona",
    # Institucional
    "AreaConocimiento",
    "CuerpoAcademico",
    "Dependencia",
    # Persona
    "Persona",
    "PersonaArea",
    "PersonaDependenciaHistorico",
    # Producción
    "Coautoria",
    "DocumentoCorpus",
    "Paper",
    # Sistema
    "Auditoria",
    "Cosecha",
    "UsuarioSistema",
    # Gemelo
    "Gemelo",
    "GemeloCorpusUso",
    # Simulación
    "RespuestaSimulacion",
    "Simulacion",
    # Auxiliares
    "ConfiguracionPresupuesto",
    "ConsumoLlm",
    "ExportToken",
    "TemaTroncoComun",
    "ValidacionGemelo",
]
