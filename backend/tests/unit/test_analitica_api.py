"""
Tests de integración para los endpoints de analítica bibliométrica.
Crea datos de prueba directamente via SQLAlchemy y verifica las respuestas.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from intellectclone.models.institucional import CuerpoAcademico, Dependencia
from intellectclone.models.persona import Persona
from intellectclone.models.produccion import Coautoria, Paper


@pytest_asyncio.fixture
async def datos_analitica(test_session: AsyncSession) -> dict:  # type: ignore[type-arg]
    """
    Crea datos de prueba para analítica:
    - 2 dependencias (FACTAS, FACTAM)
    - 3 personas (2 en FACTAS, 1 en FACTAM)
    - 4 papers con años 2022-2024
    - 6 coautorias
    - 1 cuerpo académico
    """
    dep1 = Dependencia(
        id=uuid.uuid4(),
        codigo="FACTAS_TEST",
        nombre="Facultad de Ciencias Exactas Test",
        nombre_corto="FACTAS",
        tipo="facultad",
        activa=True,
    )
    dep2 = Dependencia(
        id=uuid.uuid4(),
        codigo="FACTAM_TEST",
        nombre="Facultad de Tamaulipas Test",
        nombre_corto="FACTAM",
        tipo="facultad",
        activa=True,
    )
    test_session.add_all([dep1, dep2])
    await test_session.flush()

    ca1 = CuerpoAcademico(
        id=uuid.uuid4(),
        nombre="CA Sistemas Inteligentes Test",
        activo=True,
        dependencia_id=dep1.id,
    )
    test_session.add(ca1)
    await test_session.flush()

    per1 = Persona(
        id=uuid.uuid4(),
        nombre_completo="Dr. Alfa Test",
        nombre_normalizado="dr alfa test",
        dependencia_id=dep1.id,
        activa=True,
        total_citas=50,
        indice_h=5,
    )
    per2 = Persona(
        id=uuid.uuid4(),
        nombre_completo="Dra. Beta Test",
        nombre_normalizado="dra beta test",
        dependencia_id=dep1.id,
        activa=True,
        total_citas=30,
        indice_h=3,
    )
    per3 = Persona(
        id=uuid.uuid4(),
        nombre_completo="Dr. Gamma Test",
        nombre_normalizado="dr gamma test",
        dependencia_id=dep2.id,
        activa=True,
        total_citas=10,
        indice_h=2,
    )
    test_session.add_all([per1, per2, per3])
    await test_session.flush()

    p1 = Paper(id=uuid.uuid4(), titulo="Paper Test 2022", año=2022, total_citas=15)
    p2 = Paper(id=uuid.uuid4(), titulo="Paper Test 2023 A", año=2023, total_citas=20)
    p3 = Paper(id=uuid.uuid4(), titulo="Paper Test 2023 B", año=2023, total_citas=8)
    p4 = Paper(id=uuid.uuid4(), titulo="Paper Test 2024", año=2024, total_citas=2)
    test_session.add_all([p1, p2, p3, p4])
    await test_session.flush()

    # per1 es autor de p1, p2, p4 (3 papers)
    # per2 es autor de p1, p3 (2 papers)
    # per3 es autor de p2 (1 paper)
    coautorias = [
        Coautoria(id=uuid.uuid4(), persona_id=per1.id, paper_id=p1.id, es_primer_autor=True),
        Coautoria(id=uuid.uuid4(), persona_id=per2.id, paper_id=p1.id),
        Coautoria(id=uuid.uuid4(), persona_id=per1.id, paper_id=p2.id, es_primer_autor=True),
        Coautoria(id=uuid.uuid4(), persona_id=per3.id, paper_id=p2.id),
        Coautoria(id=uuid.uuid4(), persona_id=per2.id, paper_id=p3.id, es_primer_autor=True),
        Coautoria(id=uuid.uuid4(), persona_id=per1.id, paper_id=p4.id, es_primer_autor=True),
    ]
    test_session.add_all(coautorias)
    await test_session.flush()

    return {
        "dep1": dep1,
        "dep2": dep2,
        "ca1": ca1,
        "per1": per1,
        "per2": per2,
        "per3": per3,
        "papers": [p1, p2, p3, p4],
    }


# ---------------------------------------------------------------------------
# GET /api/v1/analitica/estadisticas-globales
# ---------------------------------------------------------------------------


class TestEstadisticasGlobales:
    async def test_respuesta_vacia(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/estadisticas-globales")
        assert response.status_code == 200
        data = response.json()
        assert "total_personas" in data
        assert "total_papers" in data
        assert "total_coautorias" in data
        assert "total_dependencias" in data
        assert "total_cuerpos_academicos" in data

    async def test_con_datos(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/estadisticas-globales")
        assert response.status_code == 200
        data = response.json()
        assert data["total_personas"] >= 3
        assert data["total_papers"] >= 4
        assert data["total_coautorias"] >= 6
        assert data["total_dependencias"] >= 2
        assert data["total_cuerpos_academicos"] >= 1


# ---------------------------------------------------------------------------
# GET /api/v1/analitica/papers-por-año
# ---------------------------------------------------------------------------


class TestPapersPorAnio:
    async def test_respuesta_vacia(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/papers-por-año")
        assert response.status_code == 200
        data = response.json()
        assert "datos" in data
        assert "total_papers_historico" in data
        assert isinstance(data["datos"], list)

    async def test_con_datos_estructura(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/papers-por-año")
        assert response.status_code == 200
        data = response.json()
        assert data["total_papers_historico"] >= 4

        años = {punto["año"] for punto in data["datos"]}
        assert 2022 in años
        assert 2023 in años
        assert 2024 in años

    async def test_orden_cronologico(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/papers-por-año")
        datos = response.json()["datos"]
        # Filtrar solo los años de prueba
        años_prueba = [d["año"] for d in datos if d["año"] in {2022, 2023, 2024}]
        assert años_prueba == sorted(años_prueba)

    async def test_suma_citas_por_anio(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/papers-por-año")
        datos = response.json()["datos"]
        by_year = {d["año"]: d for d in datos}
        # 2023 tiene p2 (20 citas) + p3 (8 citas) = 28
        assert by_year[2023]["total_citas"] >= 28
        assert by_year[2023]["total_papers"] >= 2


# ---------------------------------------------------------------------------
# GET /api/v1/analitica/top-dependencias
# ---------------------------------------------------------------------------


class TestTopDependencias:
    async def test_respuesta_vacia(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/top-dependencias")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_con_datos_estructura(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/top-dependencias")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 2

        for item in items:
            assert "dependencia_id" in item
            assert "nombre" in item
            assert "total_papers" in item
            assert "total_personas" in item

    async def test_factas_tiene_mas_papers(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/top-dependencias?limite=50")
        items = response.json()["items"]
        dep1_id = str(datos_analitica["dep1"].id)
        dep2_id = str(datos_analitica["dep2"].id)

        dep1_item = next((i for i in items if i["dependencia_id"] == dep1_id), None)
        dep2_item = next((i for i in items if i["dependencia_id"] == dep2_id), None)
        assert dep1_item is not None
        assert dep2_item is not None
        # FACTAS: per1 (3 papers) + per2 (2 papers) = 4 papers únicos
        # FACTAM: per3 (1 paper) = 1 paper único
        assert dep1_item["total_papers"] > dep2_item["total_papers"]

    async def test_limite_parametro(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/top-dependencias?limite=1")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) <= 1

    async def test_limite_invalido(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/top-dependencias?limite=0")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/analitica/top-investigadores
# ---------------------------------------------------------------------------


class TestTopInvestigadores:
    async def test_respuesta_vacia(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/top-investigadores")
        assert response.status_code == 200
        assert "items" in response.json()

    async def test_con_datos_estructura(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/top-investigadores?limite=10")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 3
        for item in items:
            assert "persona_id" in item
            assert "nombre_completo" in item
            assert "n_papers_cosechados" in item
            assert "total_citas" in item
            assert "indice_h" in item

    async def test_orden_por_papers(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/top-investigadores?orden=papers&limite=50")
        items = response.json()["items"]
        per1_id = str(datos_analitica["per1"].id)
        per1_item = next((i for i in items if i["persona_id"] == per1_id), None)
        assert per1_item is not None
        # per1 tiene 3 papers → debe aparecer primero entre los de prueba
        assert per1_item["n_papers_cosechados"] >= 3

    async def test_orden_por_citas(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/top-investigadores?orden=citas&limite=50")
        assert response.status_code == 200
        items = response.json()["items"]
        # Verificar que están ordenados por citas descendente
        citas = [i["total_citas"] for i in items]
        assert citas == sorted(citas, reverse=True)

    async def test_orden_invalido(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/top-investigadores?orden=invalido")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/analitica/red-coautoria
# ---------------------------------------------------------------------------


class TestRedCoautoria:
    async def test_respuesta_vacia(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/red-coautoria")
        assert response.status_code == 200
        data = response.json()
        assert "nodos" in data
        assert "aristas" in data
        assert "total_nodos" in data
        assert "total_aristas" in data

    async def test_con_datos_estructura(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/red-coautoria")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodos"] >= 3
        assert data["total_nodos"] == len(data["nodos"])
        assert data["total_aristas"] == len(data["aristas"])

        for nodo in data["nodos"]:
            assert "persona_id" in nodo
            assert "nombre_completo" in nodo
            assert "grado" in nodo
            assert nodo["grado"] >= 1

    async def test_aristas_coautoria_correctas(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        response = await client.get("/api/v1/analitica/red-coautoria")
        data = response.json()
        # per1-per2 co-autorizaron p1 → debe haber arista
        per1_id = str(datos_analitica["per1"].id)
        per2_id = str(datos_analitica["per2"].id)
        pares_aristas = {(a["persona_a_id"], a["persona_b_id"]) for a in data["aristas"]}
        # El par debe estar en algún orden (a_id < b_id)
        par = tuple(sorted([per1_id, per2_id]))
        assert par in pares_aristas

    async def test_filtro_persona_id(
        self,
        client: AsyncClient,
        datos_analitica: dict,  # type: ignore[type-arg]
    ) -> None:
        per1_id = datos_analitica["per1"].id
        response = await client.get(f"/api/v1/analitica/red-coautoria?persona_id={per1_id}")
        assert response.status_code == 200
        data = response.json()
        # per1 tiene co-autores per2 y per3 → al menos 3 nodos
        assert data["total_nodos"] >= 3
        ids_nodos = {n["persona_id"] for n in data["nodos"]}
        assert str(per1_id) in ids_nodos

    async def test_limite_nodos(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/red-coautoria?limite_nodos=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total_nodos"] <= 2

    async def test_limite_invalido(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/analitica/red-coautoria?limite_nodos=0")
        assert response.status_code == 422
