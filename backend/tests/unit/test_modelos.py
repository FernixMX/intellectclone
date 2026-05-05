"""
Tests unitarios para los modelos SQLAlchemy de IntellectClone.
"""

from intellectclone.db.base import Base
from intellectclone.models import (
    AreaConocimiento,
    Auditoria,
    Cosecha,
    CuerpoAcademico,
    Dependencia,
    Gemelo,
    GemeloCorpusUso,
    Paper,
    Persona,
    PersonaArea,
    PersonaDependenciaHistorico,
    RespuestaSimulacion,
    Simulacion,
    UsuarioSistema,
)
from intellectclone.models.enums import (
    EstadoCosecha,
    EstadoGemelo,
    NivelRasgo,
    NivelSnii,
    PosturaRespuesta,
    RolUsuario,
    TipoFuente,
    TipoPaper,
    TipoPersona,
)


class TestTablenames:
    """Verifica que todos los modelos tienen __tablename__ definido."""

    def test_dependencia_tablename(self) -> None:
        assert Dependencia.__tablename__ == "dependencia"

    def test_cuerpo_academico_tablename(self) -> None:
        assert CuerpoAcademico.__tablename__ == "cuerpo_academico"

    def test_area_conocimiento_tablename(self) -> None:
        assert AreaConocimiento.__tablename__ == "area_conocimiento"

    def test_persona_tablename(self) -> None:
        assert Persona.__tablename__ == "persona"

    def test_persona_area_tablename(self) -> None:
        assert PersonaArea.__tablename__ == "persona_area"

    def test_persona_dependencia_historico_tablename(self) -> None:
        assert PersonaDependenciaHistorico.__tablename__ == "persona_dependencia_historico"

    def test_paper_tablename(self) -> None:
        assert Paper.__tablename__ == "paper"

    def test_gemelo_tablename(self) -> None:
        assert Gemelo.__tablename__ == "gemelo"

    def test_gemelo_corpus_uso_tablename(self) -> None:
        assert GemeloCorpusUso.__tablename__ == "gemelo_corpus_uso"

    def test_simulacion_tablename(self) -> None:
        assert Simulacion.__tablename__ == "simulacion"

    def test_respuesta_simulacion_tablename(self) -> None:
        assert RespuestaSimulacion.__tablename__ == "respuesta_simulacion"

    def test_usuario_sistema_tablename(self) -> None:
        assert UsuarioSistema.__tablename__ == "usuario_sistema"

    def test_cosecha_tablename(self) -> None:
        assert Cosecha.__tablename__ == "cosecha"

    def test_auditoria_tablename(self) -> None:
        assert Auditoria.__tablename__ == "auditoria"


class TestPersonaColumnas:
    """Verifica que el modelo Persona tiene los campos requeridos."""

    def test_persona_tiene_nombre_completo(self) -> None:
        cols = {c.key for c in Persona.__table__.columns}
        assert "nombre_completo" in cols

    def test_persona_tiene_tipo(self) -> None:
        cols = {c.key for c in Persona.__table__.columns}
        assert "tipo" in cols

    def test_persona_tiene_embedding_perfil(self) -> None:
        cols = {c.key for c in Persona.__table__.columns}
        assert "embedding_perfil" in cols

    def test_persona_tiene_nivel_snii(self) -> None:
        cols = {c.key for c in Persona.__table__.columns}
        assert "nivel_snii" in cols

    def test_persona_tiene_metadatos(self) -> None:
        cols = {c.key for c in Persona.__table__.columns}
        assert "metadatos" in cols

    def test_persona_tiene_activa(self) -> None:
        cols = {c.key for c in Persona.__table__.columns}
        assert "activa" in cols


class TestGemeloColumnas:
    """Verifica campos especiales del modelo Gemelo."""

    def test_gemelo_tiene_valores_schwartz(self) -> None:
        """valores_schwartz es un campo adicional confirmado por Fernando."""
        cols = {c.key for c in Gemelo.__table__.columns}
        assert "valores_schwartz" in cols

    def test_gemelo_tiene_system_prompt(self) -> None:
        cols = {c.key for c in Gemelo.__table__.columns}
        assert "system_prompt" in cols

    def test_gemelo_tiene_estado(self) -> None:
        cols = {c.key for c in Gemelo.__table__.columns}
        assert "estado" in cols

    def test_gemelo_tiene_posturas_tematicas(self) -> None:
        cols = {c.key for c in Gemelo.__table__.columns}
        assert "posturas_tematicas" in cols


class TestEnumeraciones:
    """Verifica que los enums tienen los valores correctos."""

    def test_tipo_persona_valores(self) -> None:
        valores = {e.value for e in TipoPersona}
        assert "investigador" in valores
        assert "docente" in valores
        assert "externo" in valores

    def test_estado_gemelo_valores(self) -> None:
        valores = {e.value for e in EstadoGemelo}
        assert "sin_corpus" in valores
        assert "validado" in valores
        assert "publicado" in valores
        assert "baja_solicitada" in valores

    def test_nivel_rasgo_valores(self) -> None:
        valores = {e.value for e in NivelRasgo}
        assert "muy_bajo" in valores
        assert "muy_alto" in valores

    def test_nivel_snii_valores(self) -> None:
        valores = {e.value for e in NivelSnii}
        assert "candidato" in valores
        assert "emerito" in valores

    def test_tipo_paper_valores(self) -> None:
        valores = {e.value for e in TipoPaper}
        assert "articulo" in valores
        assert "libro" in valores

    def test_tipo_fuente_valores(self) -> None:
        valores = {e.value for e in TipoFuente}
        assert "openalex" in valores
        assert "manual" in valores

    def test_estado_cosecha_valores(self) -> None:
        valores = {e.value for e in EstadoCosecha}
        assert "completada_con_errores" in valores

    def test_rol_usuario_valores(self) -> None:
        valores = {e.value for e in RolUsuario}
        assert "admin" in valores
        assert "rectoria" in valores
        assert "lectura" in valores

    def test_postura_respuesta_valores(self) -> None:
        valores = {e.value for e in PosturaRespuesta}
        assert "a_favor_fuerte" in valores
        assert "sin_clasificar" in valores

    def test_enums_son_str(self) -> None:
        """Los enums deben heredar de str para serialización JSON automática."""
        assert issubclass(TipoPersona, str)
        assert issubclass(EstadoGemelo, str)
        assert issubclass(NivelRasgo, str)


class TestMetadata:
    """Verifica que la metadata de SQLAlchemy tiene todas las tablas."""

    def test_total_tablas(self) -> None:
        tablas = list(Base.metadata.tables.keys())
        # Mínimo 21 tablas (16 principales + 5 auxiliares)
        assert len(tablas) >= 21

    def test_tablas_principales_existen(self) -> None:
        tablas = set(Base.metadata.tables.keys())
        tablas_esperadas = {
            "dependencia",
            "cuerpo_academico",
            "area_conocimiento",
            "persona",
            "persona_area",
            "persona_dependencia_historico",
            "paper",
            "coautoria",
            "documento_corpus",
            "gemelo",
            "gemelo_corpus_uso",
            "simulacion",
            "respuesta_simulacion",
            "usuario_sistema",
            "cosecha",
            "auditoria",
        }
        assert tablas_esperadas.issubset(tablas)

    def test_tablas_auxiliares_existen(self) -> None:
        tablas = set(Base.metadata.tables.keys())
        tablas_aux = {
            "validacion_gemelo",
            "export_token",
            "configuracion_presupuesto",
            "consumo_llm",
            "tema_tronco_comun",
        }
        assert tablas_aux.issubset(tablas)
