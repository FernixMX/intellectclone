"""
Tests unitarios para los schemas Pydantic de IntellectClone.
"""

import uuid
from datetime import UTC

import pytest
from pydantic import ValidationError

from intellectclone.models.enums import TipoPersona
from intellectclone.schemas.persona import PersonaCreate, PersonaListItem, PersonaRead


class TestPersonaCreate:
    """Tests de validación del schema PersonaCreate."""

    def test_campos_requeridos_minimos(self) -> None:
        """Crea una persona con solo los campos mínimos requeridos."""
        persona = PersonaCreate(
            nombre_completo="Dr. Juan Pérez García",
            nombre_normalizado="dr juan perez garcia",
        )
        assert persona.nombre_completo == "Dr. Juan Pérez García"
        assert persona.nombre_normalizado == "dr juan perez garcia"
        assert persona.tipo == TipoPersona.investigador  # default

    def test_falla_sin_nombre_completo(self) -> None:
        """Debe fallar si falta nombre_completo."""
        with pytest.raises(ValidationError):
            PersonaCreate(nombre_normalizado="juan perez")  # type: ignore[call-arg]

    def test_falla_sin_nombre_normalizado(self) -> None:
        """Debe fallar si falta nombre_normalizado."""
        with pytest.raises(ValidationError):
            PersonaCreate(nombre_completo="Juan Pérez")  # type: ignore[call-arg]

    def test_tipo_default_investigador(self) -> None:
        """El tipo default debe ser 'investigador'."""
        persona = PersonaCreate(
            nombre_completo="Test",
            nombre_normalizado="test",
        )
        assert persona.tipo == TipoPersona.investigador

    def test_tipo_personalizado(self) -> None:
        """Acepta otros tipos de persona."""
        persona = PersonaCreate(
            nombre_completo="Rector UAT",
            nombre_normalizado="rector uat",
            tipo=TipoPersona.directivo,
        )
        assert persona.tipo == TipoPersona.directivo

    def test_orcid_longitud_maxima(self) -> None:
        """ORCID tiene max_length=19."""
        persona = PersonaCreate(
            nombre_completo="Test",
            nombre_normalizado="test",
            orcid="0000-0000-0000-0001",
        )
        assert persona.orcid == "0000-0000-0000-0001"

    def test_metadatos_default_dict_vacio(self) -> None:
        """metadatos default debe ser dict vacío."""
        persona = PersonaCreate(
            nombre_completo="Test",
            nombre_normalizado="test",
        )
        assert persona.metadatos == {}


class TestPersonaRead:
    """Tests de serialización del schema PersonaRead."""

    def _make_persona_data(self, **kwargs) -> dict:  # type: ignore[type-arg]
        """Devuelve datos mínimos válidos para PersonaRead."""
        from datetime import datetime

        now = datetime.now(UTC)
        base = {
            "id": uuid.uuid4(),
            "nombre_completo": "Dr. María López",
            "nombre_normalizado": "dr maria lopez",
            "primer_nombre": "María",
            "apellido_paterno": "López",
            "apellido_materno": None,
            "tipo": TipoPersona.investigador,
            "orcid": None,
            "openalex_id": None,
            "scopus_id": None,
            "cvu_conacyt": None,
            "google_scholar_id": None,
            "dependencia_id": None,
            "cuerpo_academico_id": None,
            "cargo": None,
            "nivel_snii": None,
            "snii_vigente_hasta": None,
            "grado_maximo": "doctorado",
            "grado_disciplina": "Educación",
            "total_publicaciones": 5,
            "total_citas": 20,
            "indice_h": 2,
            "indice_i10": 1,
            "primera_publicacion": None,
            "ultima_publicacion": None,
            "email_publico": "maria@uat.edu.mx",
            "sitio_web": None,
            "activa": True,
            "motivo_baja": None,
            "fecha_baja": None,
            "fuente_principal": None,
            "metadatos": {},
            "created_at": now,
            "updated_at": now,
        }
        base.update(kwargs)
        return base

    def test_serializa_correctamente(self) -> None:
        """PersonaRead debe construirse desde un dict completo."""
        data = self._make_persona_data()
        persona = PersonaRead(**data)
        assert persona.nombre_completo == "Dr. María López"
        assert persona.tipo == TipoPersona.investigador

    def test_id_es_uuid(self) -> None:
        """El id debe ser un UUID."""
        data = self._make_persona_data()
        persona = PersonaRead(**data)
        assert isinstance(persona.id, uuid.UUID)

    def test_serializa_a_json(self) -> None:
        """Debe serializar a JSON sin errores."""
        data = self._make_persona_data()
        persona = PersonaRead(**data)
        json_str = persona.model_dump_json()
        assert "nombre_completo" in json_str


class TestPersonaListItem:
    """Tests del schema compacto PersonaListItem."""

    def test_campos_compactos(self) -> None:
        """PersonaListItem tiene menos campos que PersonaRead."""
        campos_read = set(PersonaRead.model_fields.keys())
        campos_list = set(PersonaListItem.model_fields.keys())
        assert len(campos_list) < len(campos_read)

    def test_tiene_campos_esenciales(self) -> None:
        """PersonaListItem debe tener los campos mínimos para listados."""
        campos = set(PersonaListItem.model_fields.keys())
        assert "id" in campos
        assert "nombre_completo" in campos
        assert "tipo" in campos
