"""
Tests de integración para la API de personas.
Verifica el ciclo completo: POST /api/v1/personas, GET /api/v1/personas/{id}, GET /api/v1/personas
"""

from httpx import AsyncClient


class TestCrearPersona:
    """Tests del endpoint POST /api/v1/personas."""

    async def test_crear_persona_dummy(self, client: AsyncClient) -> None:
        """Crea una persona y verifica que devuelve 201 con los datos correctos."""
        payload = {
            "nombre_completo": "Dr. Luis Armando Cárdenas Nájera",
            "nombre_normalizado": "dr luis armando cardenas najera",
            "tipo": "investigador",
            "nivel_snii": "nivel_2",
            "grado_maximo": "doctorado",
            "grado_disciplina": "Ciencias de la Computación",
            "email_publico": "lacardenas@uat.edu.mx",
        }

        response = await client.post("/api/v1/personas", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["nombre_completo"] == "Dr. Luis Armando Cárdenas Nájera"
        assert data["nombre_normalizado"] == "dr luis armando cardenas najera"
        assert data["tipo"] == "investigador"
        assert data["nivel_snii"] == "nivel_2"
        assert "id" in data
        assert data["activa"] is True
        assert data["total_publicaciones"] == 0

    async def test_crear_persona_minimos(self, client: AsyncClient) -> None:
        """Crea una persona con solo los campos mínimos requeridos."""
        payload = {
            "nombre_completo": "Mtro. Jesús González",
            "nombre_normalizado": "mtro jesus gonzalez",
        }

        response = await client.post("/api/v1/personas", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["nombre_completo"] == "Mtro. Jesús González"
        assert data["tipo"] == "investigador"  # default

    async def test_crear_persona_falla_sin_campos_requeridos(self, client: AsyncClient) -> None:
        """Debe devolver 422 si faltan campos requeridos."""
        payload = {"nombre_completo": "Solo Nombre"}  # falta nombre_normalizado

        response = await client.post("/api/v1/personas", json=payload)

        assert response.status_code == 422


class TestObtenerPersona:
    """Tests del endpoint GET /api/v1/personas/{id}."""

    async def test_leer_persona(self, client: AsyncClient) -> None:
        """Crea una persona via POST y la recupera via GET."""
        # Crear
        payload = {
            "nombre_completo": "Dra. Ana Patricia Morales Ruiz",
            "nombre_normalizado": "dra ana patricia morales ruiz",
            "tipo": "investigador",
            "orcid": "0000-0001-2345-6789",
        }
        create_response = await client.post("/api/v1/personas", json=payload)
        assert create_response.status_code == 201
        persona_id = create_response.json()["id"]

        # Recuperar
        get_response = await client.get(f"/api/v1/personas/{persona_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == persona_id
        assert data["nombre_completo"] == "Dra. Ana Patricia Morales Ruiz"
        assert data["orcid"] == "0000-0001-2345-6789"

    async def test_leer_persona_no_existe(self, client: AsyncClient) -> None:
        """Debe devolver 404 para un UUID que no existe."""
        import uuid

        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/personas/{fake_id}")
        assert response.status_code == 404

        # Verificar que es RFC 7807
        data = response.json()
        assert "title" in data
        assert "status" in data
        assert data["status"] == 404

    async def test_leer_persona_uuid_invalido(self, client: AsyncClient) -> None:
        """Debe devolver 422 para un ID que no es UUID válido."""
        response = await client.get("/api/v1/personas/no-es-un-uuid")
        assert response.status_code == 422


class TestListarPersonas:
    """Tests del endpoint GET /api/v1/personas."""

    async def test_listar_personas_vacia(self, client: AsyncClient) -> None:
        """Lista personas en una base vacía devuelve lista vacía."""
        response = await client.get("/api/v1/personas")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_listar_personas_con_datos(self, client: AsyncClient) -> None:
        """Devuelve lista paginada después de crear personas."""
        # Crear 2 personas
        for i in range(2):
            await client.post(
                "/api/v1/personas",
                json={
                    "nombre_completo": f"Investigador {i}",
                    "nombre_normalizado": f"investigador {i}",
                },
            )

        response = await client.get("/api/v1/personas")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_listar_personas_paginacion(self, client: AsyncClient) -> None:
        """Verifica que la paginación funciona correctamente."""
        # Crear 3 personas
        for i in range(3):
            await client.post(
                "/api/v1/personas",
                json={
                    "nombre_completo": f"Paginacion Test {i}",
                    "nombre_normalizado": f"paginacion test {i}",
                },
            )

        response = await client.get("/api/v1/personas?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["items"]) <= 2

    async def test_listar_personas_filtro_tipo(self, client: AsyncClient) -> None:
        """Filtra por tipo de persona."""
        # Crear un directivo
        await client.post(
            "/api/v1/personas",
            json={
                "nombre_completo": "Rector UAT",
                "nombre_normalizado": "rector uat",
                "tipo": "directivo",
            },
        )

        response = await client.get("/api/v1/personas?tipo=directivo")
        assert response.status_code == 200
        data = response.json()
        assert all(item["tipo"] == "directivo" for item in data["items"])

    async def test_listar_personas_busqueda_q(self, client: AsyncClient) -> None:
        """Búsqueda por nombre con parámetro q."""
        await client.post(
            "/api/v1/personas",
            json={
                "nombre_completo": "Dr. Zeferino Velázquez Particular",
                "nombre_normalizado": "dr zeferino velazquez particular",
            },
        )

        response = await client.get("/api/v1/personas?q=Zeferino")
        assert response.status_code == 200
        data = response.json()
        nombres = [item["nombre_completo"] for item in data["items"]]
        assert any("Zeferino" in nombre for nombre in nombres)


class TestActualizarPersona:
    """Tests del endpoint PATCH /api/v1/personas/{id}."""

    async def test_actualizar_persona(self, client: AsyncClient) -> None:
        """Actualiza campos de una persona existente."""
        # Crear
        create_response = await client.post(
            "/api/v1/personas",
            json={
                "nombre_completo": "Dr. Carlos Mendoza",
                "nombre_normalizado": "dr carlos mendoza",
            },
        )
        persona_id = create_response.json()["id"]

        # Actualizar
        patch_response = await client.patch(
            f"/api/v1/personas/{persona_id}",
            json={"cargo": "Profesor de Tiempo Completo", "grado_maximo": "doctorado"},
        )
        assert patch_response.status_code == 200
        data = patch_response.json()
        assert data["cargo"] == "Profesor de Tiempo Completo"
        assert data["grado_maximo"] == "doctorado"

    async def test_actualizar_persona_no_existe(self, client: AsyncClient) -> None:
        """Devuelve 404 al intentar actualizar una persona inexistente."""
        import uuid

        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/api/v1/personas/{fake_id}",
            json={"cargo": "Test"},
        )
        assert response.status_code == 404
