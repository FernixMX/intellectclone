# IntellectClone — Contrato de exportación de gemelos

**Documento técnico 06 — Integración con Mirrorfish**
**Versión 0.1**
**Audiencia:** Claude Code (constructor) + revisión humana de Fernando

---

## Cómo leer este documento

Este documento define **el contrato técnico** entre IntellectClone (productor de gemelos digitales) y Mirrorfish (consumidor de gemelos para simulación). Define el formato de los datos, los endpoints REST que IntellectClone expone, las reglas de autenticación, y las garantías que cada lado debe respetar.

Si IntellectClone es la fábrica y Mirrorfish es el cliente, este documento es el contrato de suministro: qué se entrega, en qué formato, con qué periodicidad, con qué garantías.

Reemplaza a la sección de "simulador interno" que aparecía en documentos previos del proyecto. IntellectClone ya **no incluye simulador propio en v1**: Fernando ya tiene Mirrorfish funcionando aparte y se conecta a IntellectClone para alimentarse.

---

## 1. Arquitectura de la integración

### Topología

Ambos sistemas viven en el **mismo VPS Linux IONOS**, accesibles entre sí a través de la red interna del servidor. No hay tráfico cruzando internet entre ellos. Esto simplifica la autenticación, reduce latencia a milisegundos, y mantiene todos los datos institucionales bajo el control de un único servidor UAT.

Cada sistema corre en sus propios contenedores Docker dentro del mismo `docker-compose`. La comunicación entre ellos es por HTTP sobre la red interna de Docker, usando nombres de servicio (`http://intellectclone-api:8000` desde la red privada) o, si se prefiere, por reverse proxy local de Nginx.

### Patrón de comunicación

**Pull bajo demanda.** Mirrorfish es el cliente activo: pregunta a IntellectClone cuando necesita gemelos. IntellectClone es servidor pasivo: escucha y responde.

No hay webhooks, no hay push, no hay sincronización nocturna en v1. Si Mirrorfish necesita un gemelo lo pide; si no lo necesita, no pide. Esto mantiene el sistema simple, libre de bugs de sincronización, y fácil de razonar.

Cuando un gemelo se actualiza en IntellectClone (regeneración manual disparada por admin), la próxima petición que Mirrorfish haga sobre ese gemelo recibirá la nueva versión automáticamente. Si Mirrorfish quisiera cachear, debe gestionar la invalidación de cache por su cuenta.

### Política de qué se exporta

Solo se exportan gemelos en estado **`validado`** o **`publicado`**. Los gemelos en `borrador`, `en_proceso`, `error`, `archivado` (versiones anteriores), `baja_solicitada` o `sin_corpus` **nunca** son visibles desde la API de exportación.

Esta restricción es la garantía institucional más importante del contrato: Mirrorfish **nunca puede consumir un gemelo que no haya sido validado humanamente**. Esto está implementado en la capa de servicio de IntellectClone, no en filtros opcionales — es una restricción dura que no se puede evadir desde la API.

Cuando un gemelo se regenera (nueva versión), automáticamente vuelve a estado `borrador` hasta que un admin lo valide. Durante ese tiempo, Mirrorfish sigue viendo la versión anterior validada. Cuando la nueva se valida, las peticiones siguientes recibirán la nueva.

---

## 2. Esquema JSON del gemelo exportado

Esta es la estructura completa que Mirrorfish recibe. Es JSON estándar, codificación UTF-8, formato pretty-printed cuando es individual y minificado cuando es masivo. Todos los nombres de campos son `snake_case`.

```json
{
  "schema_version": "1.0",

  "gemelo": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "version": 3,
    "estado": "validado",
    "generado_en": "2026-04-15T18:42:11Z",
    "validado_en": "2026-04-16T09:15:33Z",
    "modelo_perfilador": "claude-sonnet-4-6",
    "prompt_perfilador_version": "0.2"
  },

  "persona": {
    "id": "0d8e3a17-2c1f-4f33-9e8b-72a8d4c5b1a9",
    "nombre_completo": "María Elena Cárdenas Ruiz",
    "primer_nombre": "María Elena",
    "apellido_paterno": "Cárdenas",
    "apellido_materno": "Ruiz",
    "tipo": "investigador",
    "orcid": "0000-0002-1234-5678",
    "openalex_id": "A1234567890"
  },

  "institucional": {
    "dependencia": {
      "id": "...",
      "nombre": "Facultad de Ingeniería y Ciencias",
      "campus": "Victoria"
    },
    "cuerpo_academico": {
      "id": "...",
      "nombre": "Sistemas Inteligentes",
      "estatus": "consolidado"
    },
    "cargo": "Profesora de Tiempo Completo",
    "nivel_snii": "nivel_2",
    "snii_vigente_hasta": "2027-12-31",
    "grado_maximo": "doctorado",
    "areas_principales": [
      { "nombre": "Ciencias de la Computación", "peso": 0.85 },
      { "nombre": "Ingeniería Industrial", "peso": 0.42 }
    ]
  },

  "metricas_bibliometricas": {
    "total_publicaciones": 47,
    "total_citas": 1284,
    "indice_h": 23,
    "indice_i10": 35,
    "primera_publicacion": "2008-06-01",
    "ultima_publicacion": "2025-11-12"
  },

  "personalidad_hexaco": {
    "extraversion": {
      "nivel": "medio",
      "evidencia": [
        "...",
        "..."
      ],
      "justificacion": "Su lenguaje muestra equilibrio entre expresividad y reserva..."
    },
    "neuroticismo": {
      "nivel": "bajo",
      "evidencia": ["..."],
      "justificacion": "..."
    },
    "responsabilidad": {
      "nivel": "alto",
      "evidencia": ["..."],
      "justificacion": "..."
    },
    "amabilidad": {
      "nivel": "medio",
      "evidencia": ["..."],
      "justificacion": "..."
    },
    "apertura": {
      "nivel": "alto",
      "evidencia": ["..."],
      "justificacion": "..."
    },
    "honestidad_humildad": {
      "nivel": "alto",
      "evidencia": ["..."],
      "justificacion": "..."
    }
  },

  "valores_schwartz": {
    "valores": [
      {
        "valor": "universalismo",
        "score": 85,
        "rango": 1,
        "evidencia": ["..."]
      },
      {
        "valor": "autodireccion",
        "score": 78,
        "rango": 2,
        "evidencia": ["..."]
      }
    ],
    "valores_dominantes": ["universalismo", "autodireccion", "logro"],
    "valores_subordinados": ["tradicion", "poder"]
  },

  "idiolecto": {
    "longitud_promedio_frase": 24.5,
    "riqueza_lexica": 0.67,
    "ngrams_top_unigram": ["sistema", "análisis", "industrial"],
    "ngrams_top_bigram": ["aprendizaje profundo", "visión computacional"],
    "ngrams_top_trigram": ["redes neuronales convolucionales"],
    "firma_linguistica": "Estilo técnico-académico riguroso con preferencia por construcciones nominales y citas frecuentes a literatura especializada en aprendizaje profundo industrial.",
    "modus_operandi": "Análisis sistemático que parte de planteamiento de problema industrial concreto, propone método basado en redes neuronales adaptadas a restricciones de hardware, y valida con métricas cuantitativas.",
    "tono_dominante": "analitico_critico",
    "registro": "academico_formal"
  },

  "posturas_tematicas": {
    "tronco_comun_uat": [
      {
        "tema": "evaluacion_docente_basada_en_publicaciones",
        "postura": "matizado",
        "intensidad": "media",
        "evidencia": ["..."],
        "confianza": 0.7
      },
      {
        "tema": "uso_de_ia_en_aulas_y_evaluacion",
        "postura": "a_favor",
        "intensidad": "alta",
        "evidencia": ["..."],
        "confianza": 0.85
      },
      {
        "tema": "autonomia_universitaria",
        "postura": "sin_evidencia",
        "confianza": 0.0
      }
    ],
    "posturas_dinamicas": [
      {
        "tema": "ética del uso de IA en revisión por pares",
        "postura": "en_contra",
        "intensidad": "alta",
        "evidencia": ["..."],
        "confianza": 0.85
      }
    ]
  },

  "system_prompt": "Eres María Elena Cárdenas Ruiz, Profesora de Tiempo Completo en la Facultad de Ingeniería y Ciencias, Universidad Autónoma de Tamaulipas...\n\nPERSONALIDAD (HEXACO)\n- Extraversión: medio...\n\n[texto completo del system prompt operativo, generado por el sintetizador]",

  "scores_calidad": {
    "veracidad": 0.85,
    "completitud": 0.78,
    "consistencia": 0.91,
    "interpretacion": "perfil_solido"
  },

  "linaje": {
    "papers_usados": 47,
    "documentos_manuales_usados": 2,
    "fuentes_web_usadas": 0,
    "longitud_corpus_caracteres": 73850,
    "rango_temporal_corpus": {
      "desde": "2014-03-15",
      "hasta": "2025-11-12"
    }
  },

  "metadatos_export": {
    "exportado_en": "2026-05-03T01:42:11Z",
    "exportado_por_token": "mirrorfish_main",
    "request_id": "req_8a7b6c5d4e3f"
  }
}
```

### Notas sobre el esquema

- `schema_version` permite evolucionar el contrato sin romper Mirrorfish. Cuando se agreguen campos en v2, Mirrorfish puede checar la versión y adaptarse o ignorar.
- `gemelo.id` y `persona.id` son UUIDs de PostgreSQL. Mirrorfish puede usarlos como referencias estables.
- Los campos en `posturas_tematicas.tronco_comun_uat` con `postura: "sin_evidencia"` se incluyen en el JSON pero con confianza 0. Mirrorfish puede ignorarlos o usarlos para saber que la persona NO tiene postura inferible sobre ese tema.
- El `system_prompt` es texto Markdown plano, listo para inyectar al LLM que use Mirrorfish.
- Los `scores_calidad.interpretacion` es un campo derivado:
  - `perfil_solido`: veracidad ≥ 0.8 y completitud ≥ 0.7 y consistencia ≥ 0.85.
  - `perfil_aceptable`: veracidad ≥ 0.65 y completitud ≥ 0.5.
  - `perfil_limitado`: cualquier score por debajo de los umbrales aceptables.
  - Mirrorfish debería respetar esto al ponderar simulaciones.

---

## 3. Endpoints REST

IntellectClone expone una **API de exportación** dedicada para Mirrorfish, separada de la API principal de la UI. Esto permite control de acceso, rate limits y observabilidad independientes.

Base URL en el VPS: `http://intellectclone-api:8000/export/v1` (red interna Docker) o `https://intellectclone.uat.edu.mx/export/v1` (si se decide exponer externamente con reverse proxy).

### GET /export/v1/gemelos/{persona_id}

Obtiene el gemelo validado actual de una persona específica.

**Parámetros de URL:**
- `persona_id`: UUID de la persona.

**Headers:**
- `Authorization: Bearer {token}` (obligatorio)
- `Accept: application/json`

**Respuestas:**
- `200 OK`: gemelo encontrado, devuelve el JSON descrito arriba.
- `404 Not Found`: persona no existe, no tiene gemelo validado, o está en baja.
- `401 Unauthorized`: token inválido o faltante.
- `403 Forbidden`: token válido pero sin permisos sobre esta persona.

**Ejemplo:**
```bash
curl -H "Authorization: Bearer mfsh_abc123..." \
     http://intellectclone-api:8000/export/v1/gemelos/0d8e3a17-2c1f-4f33-9e8b-72a8d4c5b1a9
```

### GET /export/v1/gemelos

Lista gemelos según filtros. Devuelve respuestas paginadas con el esquema completo de cada gemelo.

**Query parameters:**
- `nivel_snii`: filtrar por nivel SNII (puede repetirse: `?nivel_snii=nivel_2&nivel_snii=nivel_3`)
- `dependencia_id`: UUID de dependencia
- `cuerpo_academico_id`: UUID de cuerpo académico
- `area_id`: UUID de área de conocimiento
- `tipo`: `investigador | docente | estudiante | directivo | administrativo | externo`
- `score_veracidad_min`: número 0..1, gemelos con veracidad >= valor
- `score_completitud_min`: análogo
- `interpretacion`: `perfil_solido | perfil_aceptable | perfil_limitado`
- `actualizado_desde`: ISO 8601 timestamp, gemelos validados desde esa fecha
- `limit`: int, default 50, máximo 200
- `offset`: int, default 0
- `formato`: `completo | minimo` — para v1 solo `completo`, dejado para futuro

**Respuesta 200 OK:**
```json
{
  "total": 187,
  "limit": 50,
  "offset": 0,
  "gemelos": [
    { /* objeto completo según esquema sección 2 */ },
    { /* ... */ }
  ],
  "next_offset": 50,
  "metadatos_consulta": {
    "filtros_aplicados": { /* eco de los query params */ },
    "tiempo_consulta_ms": 142,
    "request_id": "req_8a7b6c5d4e3f"
  }
}
```

### GET /export/v1/cohortes/{cohorte_id}

Si Mirrorfish guarda cohortes nombradas en IntellectClone (opcional, v2), las recupera por ID. En v1, este endpoint puede omitirse — Mirrorfish gestiona sus propias cohortes y solo usa `/gemelos` con filtros.

### GET /export/v1/personas

Lista personas sin sus gemelos completos. Útil cuando Mirrorfish quiere construir una cohorte por filtros antes de pedir los gemelos.

**Respuesta 200 OK:**
```json
{
  "total": 700,
  "personas": [
    {
      "id": "0d8e3a17-...",
      "nombre_completo": "María Elena Cárdenas Ruiz",
      "tipo": "investigador",
      "nivel_snii": "nivel_2",
      "dependencia_nombre": "Facultad de Ingeniería y Ciencias",
      "cuerpo_academico_nombre": "Sistemas Inteligentes",
      "tiene_gemelo_validado": true,
      "gemelo_actualizado_en": "2026-04-16T09:15:33Z"
    }
  ]
}
```

Acepta los mismos filtros que `/gemelos` excepto los relacionados con scores (porque scores viven en el gemelo, no en la persona).

### GET /export/v1/health

Endpoint de salud para que Mirrorfish verifique que IntellectClone está disponible.

**Respuesta 200 OK:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "schema_version": "1.0",
  "gemelos_disponibles": 187,
  "ultima_actualizacion": "2026-05-03T01:42:11Z"
}
```

### GET /export/v1/schema

Devuelve el JSON Schema completo (Draft 2020-12) del esquema de gemelo. Mirrorfish puede usarlo para validar respuestas y para auto-documentación.

---

## 4. Autenticación y permisos

### Modelo

Tokens tipo "machine-to-machine". No es OAuth completo: para v1 con un solo cliente conocido (Mirrorfish), basta con tokens estáticos rotables.

Cada token tiene asociado:
- `nombre`: identificador legible (`mirrorfish_main`, `mirrorfish_dev`)
- `permisos`: lista de scopes (`read:gemelos`, `read:personas`, `read:health`)
- `creado_por`: usuario admin que generó el token
- `expira_en`: fecha opcional de expiración
- `activo`: booleano para revocación inmediata
- `ultimo_uso`: timestamp del último request exitoso
- `total_requests`: contador

### Generación

Desde el panel admin de IntellectClone, sección "Tokens de exportación", el admin puede:
- Generar nuevo token (formato `mfsh_` + 48 caracteres random)
- Asignar permisos
- Establecer expiración
- Revocar (`activo = false`)
- Ver historial de uso

### Uso

Mirrorfish incluye el token en cada request:
```
Authorization: Bearer mfsh_abc123def456...
```

### Rate limiting

- 60 requests/minuto por token, en condiciones normales.
- 600 requests/hora por token.
- 5,000 requests/día por token.
- Endpoint `/export/v1/health` no cuenta.

Si Mirrorfish excede el rate limit, IntellectClone responde `429 Too Many Requests` con header `Retry-After: {segundos}`.

### Logs

Cada request a la API de exportación se registra en la tabla `auditoria` de IntellectClone con:
- token usado
- endpoint
- query params
- IP de origen
- duración
- status code
- request_id

Esto permite auditar uso y detectar abuso.

---

## 5. Garantías y SLAs

### Garantías de IntellectClone

**Disponibilidad:** la API de exportación está disponible cuando IntellectClone está corriendo. No hay SLA formal en v1, pero se diseña para 99% de uptime en el VPS IONOS.

**Latencia esperada:**
- `GET /gemelos/{id}` individual: < 100 ms (p95).
- `GET /gemelos` con filtros, 50 resultados: < 500 ms (p95).
- `GET /personas` listado: < 300 ms (p95).

**Consistencia:** los gemelos exportados reflejan el estado de la base al momento del request, sin lag de sincronización. Si un gemelo se actualizó hace 1 segundo, el siguiente request lo verá.

**Restricción dura de validación:** un gemelo en estado distinto de `validado` o `publicado` **nunca** será exportado, sin excepciones, sin filtros que lo evadan. Esto es invariante del sistema.

**Esquema estable:** el `schema_version: "1.0"` no cambiará durante v1. Los campos pueden agregarse (no se rompen consumidores) pero no se eliminarán ni renombrarán. Cualquier cambio breaking incrementa la versión de schema y se mantienen ambas versiones por al menos 6 meses.

### Responsabilidades de Mirrorfish

**Manejo de errores:** Mirrorfish debe manejar los códigos `4xx` y `5xx` con políticas de retry adecuadas. `5xx` reintentar con backoff exponencial. `4xx` no reintentar.

**Validación de scores:** Mirrorfish debería respetar la `interpretacion` y `scores_calidad` antes de usar un gemelo en simulaciones críticas. Un gemelo con `interpretacion: "perfil_limitado"` puede usarse pero el resultado debe interpretarse con precaución.

**Cache propio:** si Mirrorfish quiere cachear gemelos para reducir requests, debe gestionar la invalidación. Sugerencia: cachear con TTL de 1 hora y refrescar cuando la simulación lo amerite.

**Privacidad:** los datos exportados incluyen información sobre personas reales identificables. Mirrorfish hereda las obligaciones de uso interno restringido del proyecto IntellectClone.

---

## 6. Implementación en IntellectClone (para Claude Code)

### Estructura de código

```
backend/intellectclone/
├── api/
│   ├── export/
│   │   ├── __init__.py
│   │   ├── router.py           # FastAPI router /export/v1/*
│   │   ├── schemas.py          # Pydantic schemas del JSON exportado
│   │   ├── dependencies.py     # auth, rate limit, db session
│   │   └── serializers.py      # objeto SQLAlchemy → JSON exportado
│   └── ...
├── auth/
│   ├── tokens.py               # generación, verificación de tokens
│   └── ...
└── ...
```

### Pydantic schemas

Los schemas Pydantic deben replicar exactamente el esquema JSON definido en sección 2. Usar `Field(...)` con descripción para que el OpenAPI auto-generado sea documentación útil.

### Dependencia de FastAPI para auth

```python
async def verify_export_token(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> ExportToken:
    """
    Verifica el token Bearer y devuelve el ExportToken activo.
    Lanza HTTPException 401 si inválido.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    token_str = authorization.replace("Bearer ", "")
    token = await db.scalar(
        select(ExportToken).where(
            ExportToken.token == token_str,
            ExportToken.activo == True,
            or_(ExportToken.expira_en == None, ExportToken.expira_en > datetime.utcnow())
        )
    )
    if not token:
        raise HTTPException(401, "Invalid or expired token")
    # Actualizar ultimo_uso, total_requests asincrónicamente
    return token
```

### Filtro obligatorio de validación

Toda query a la tabla `gemelo` desde la API de exportación **debe** incluir esta cláusula:

```python
.where(
    Gemelo.estado.in_(['validado', 'publicado']),
    Gemelo.es_version_actual == True,
    Persona.activa == True
)
```

Implementarlo como un mixin o como un default scope para evitar olvidos.

### Tests obligatorios

- Test que verifica que un gemelo en `borrador` NO aparece en `/export/v1/gemelos/{id}`.
- Test que verifica que un gemelo en `archivado` NO aparece.
- Test que verifica que una persona en `baja_solicitada` NO aparece.
- Test que verifica que el token expirado devuelve 401.
- Test que verifica que el rate limit funciona.
- Test que verifica que el JSON exportado pasa la validación contra el JSON Schema.

---

## 7. Implementación en Mirrorfish (para futuro)

Esto está fuera del alcance de la construcción de IntellectClone, pero queda documentado como referencia para cuando Fernando o quien construya Mirrorfish necesite integrar.

### Cliente Python sugerido

```python
import httpx
from typing import Optional

class IntellectCloneClient:
    """Cliente para consumir gemelos de IntellectClone desde Mirrorfish."""

    def __init__(self, base_url: str, token: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout
        )

    def get_gemelo(self, persona_id: str) -> Optional[dict]:
        """Obtiene un gemelo individual. Devuelve None si no existe."""
        response = self.client.get(f"{self.base_url}/export/v1/gemelos/{persona_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def list_gemelos(self, **filtros) -> dict:
        """Lista gemelos según filtros. Devuelve estructura con paginación."""
        response = self.client.get(
            f"{self.base_url}/export/v1/gemelos",
            params=filtros
        )
        response.raise_for_status()
        return response.json()

    def list_gemelos_completo(self, **filtros) -> list[dict]:
        """Itera todas las páginas y devuelve lista plana."""
        gemelos = []
        offset = 0
        limit = 200
        while True:
            page = self.list_gemelos(**filtros, limit=limit, offset=offset)
            gemelos.extend(page["gemelos"])
            if page.get("next_offset") is None:
                break
            offset = page["next_offset"]
        return gemelos
```

### Patrón de uso típico

```python
# En Mirrorfish
ic = IntellectCloneClient(
    base_url="http://intellectclone-api:8000",
    token=os.environ["INTELLECTCLONE_TOKEN"]
)

# Construir cohorte
gemelos_snii = ic.list_gemelos_completo(
    nivel_snii=["nivel_2", "nivel_3"],
    score_veracidad_min=0.7
)

# Para cada gemelo, ejecutar simulación
for gemelo in gemelos_snii:
    system_prompt = gemelo["system_prompt"]
    # Llamar al LLM con system_prompt + escenario...
    # Procesar respuesta...
```

---

## 8. Evolución del contrato (v2 y más allá)

Lo que se planea agregar en versiones futuras del contrato:

**Versión 1.1:** webhooks opcionales. IntellectClone notifica a Mirrorfish cuando un gemelo se valida o se actualiza, para invalidación de cache.

**Versión 1.2:** endpoint `POST /export/v1/cohortes` para que Mirrorfish guarde cohortes nombradas en IntellectClone y las recupere por ID.

**Versión 2.0:** modo `formato=minimo` (solo system_prompt + scores) para casos de bajo ancho de banda. Probablemente nunca se necesite.

**Versión 2.0:** GraphQL alternativo para consultas más flexibles. Solo si REST se vuelve limitante.

Cualquier cambio breaking incrementa el major version del schema. Cambios aditivos solo el minor.

---

## 9. Cierre

Este contrato sustituye al simulador interno que estaba originalmente planteado en IntellectClone v1. El alcance se simplifica:

- IntellectClone se especializa en **cosechar y perfilar**.
- Mirrorfish (sistema separado, ya existente) se especializa en **simular**.
- La API de exportación es el único punto de contacto entre ambos.

Esta separación es mejor diseño que un sistema integrado: cada componente hace una cosa bien, se desarrolla y testea independientemente, y se actualiza sin afectar al otro.

Sobre los siguientes pasos: con este documento firmado, el alcance técnico de IntellectClone v1 queda **completamente cerrado**. Los documentos pendientes son ahora dos: el de cosechadores (`04_especificaciones_harvesters.md`) y el de API interna de la UI (`07_api_interna.md`, ahora más sencillo porque no hay endpoints de simulación). Después de esos dos, el paquete está completo para handoff a Claude Code.

---

*Fin del documento técnico 06. Versión 0.1 — pendiente de validación de Fernando.*
