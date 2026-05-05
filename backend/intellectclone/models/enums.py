"""
Enumeraciones del dominio IntellectClone.
Corresponden 1:1 con los tipos CREATE TYPE del esquema PostgreSQL.
"""

import enum


class TipoPersona(str, enum.Enum):
    investigador = "investigador"
    docente = "docente"
    estudiante = "estudiante"
    directivo = "directivo"
    administrativo = "administrativo"
    externo = "externo"


class EstadoGemelo(str, enum.Enum):
    sin_corpus = "sin_corpus"
    en_proceso = "en_proceso"
    borrador = "borrador"
    validado = "validado"
    publicado = "publicado"
    archivado = "archivado"
    baja_solicitada = "baja_solicitada"
    error = "error"


class NivelRasgo(str, enum.Enum):
    muy_bajo = "muy_bajo"
    bajo = "bajo"
    medio = "medio"
    alto = "alto"
    muy_alto = "muy_alto"


class NivelSnii(str, enum.Enum):
    candidato = "candidato"
    nivel_1 = "nivel_1"
    nivel_2 = "nivel_2"
    nivel_3 = "nivel_3"
    emerito = "emerito"


class TipoPaper(str, enum.Enum):
    articulo = "articulo"
    capitulo = "capitulo"
    libro = "libro"
    tesis_doctorado = "tesis_doctorado"
    tesis_maestria = "tesis_maestria"
    tesis_licenciatura = "tesis_licenciatura"
    memoria_congreso = "memoria_congreso"
    reporte_tecnico = "reporte_tecnico"
    preprint = "preprint"
    otro = "otro"


class TipoDocumentoCorpus(str, enum.Enum):
    pdf_subido = "pdf_subido"
    texto_subido = "texto_subido"
    paper_extraido = "paper_extraido"
    cv_publico = "cv_publico"
    entrevista = "entrevista"
    otro = "otro"


class EstadoDocumento(str, enum.Enum):
    pendiente = "pendiente"
    procesando = "procesando"
    procesado = "procesado"
    error = "error"
    descartado = "descartado"


class TipoFuente(str, enum.Enum):
    openalex = "openalex"
    vufind_uat = "vufind_uat"
    riuat = "riuat"
    snii_uat = "snii_uat"
    crossref = "crossref"
    orcid = "orcid"
    manual = "manual"


class EstadoCosecha(str, enum.Enum):
    programada = "programada"
    en_curso = "en_curso"
    completada = "completada"
    completada_con_errores = "completada_con_errores"
    fallida = "fallida"
    cancelada = "cancelada"


class EstadoSimulacion(str, enum.Enum):
    borrador = "borrador"
    en_cola = "en_cola"
    en_curso = "en_curso"
    agregando = "agregando"
    completada = "completada"
    fallida = "fallida"
    cancelada = "cancelada"


class PosturaRespuesta(str, enum.Enum):
    a_favor_fuerte = "a_favor_fuerte"
    a_favor = "a_favor"
    matizado = "matizado"
    neutral = "neutral"
    en_contra = "en_contra"
    en_contra_fuerte = "en_contra_fuerte"
    no_aplica = "no_aplica"
    sin_clasificar = "sin_clasificar"


class IntensidadRespuesta(str, enum.Enum):
    baja = "baja"
    media = "media"
    alta = "alta"


class RolUsuario(str, enum.Enum):
    admin = "admin"
    rectoria = "rectoria"
    asesor = "asesor"
    secretaria = "secretaria"
    investigador = "investigador"
    lectura = "lectura"
