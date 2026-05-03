# IntellectClone — API interna

**Documento técnico 07 — Endpoints REST para la UI**
**Versión 0.1**
**Audiencia:** Claude Code (constructor) + revisión humana de Fernando

---

## Índice

1. [Filosofía de la API interna](#1-filosofía-de-la-api-interna)
2. [Diferencias con la API de exportación](#2-diferencias-con-la-api-de-exportación)
3. [Autenticación con JWT](#3-autenticación-con-jwt)
4. [Roles y permisos](#4-roles-y-permisos)
5. [Estructura de endpoints](#5-estructura-de-endpoints)
6. [Endpoints de personas](#6-endpoints-de-personas)
7. [Endpoints de papers y coautorías](#7-endpoints-de-papers-y-coautorías)
8. [Endpoints de gemelos](#8-endpoints-de-gemelos)
9. [Endpoints de validación humana](#9-endpoints-de-validación-humana)
10. [Endpoints de cosechas](#10-endpoints-de-cosechas)
11. [Endpoints de tokens de exportación](#11-endpoints-de-tokens-de-exportación)
12. [Endpoints de búsqueda compleja](#12-endpoints-de-búsqueda-compleja)
13. [Endpoints de administración](#13-endpoints-de-administración)
14. [Manejo de errores estandarizado](#14-manejo-de-errores-estandarizado)
15. [Convenciones globales](#15-convenciones-globales)

---

## 1. Filosofía de la API interna

La API interna es **el contrato entre el frontend Next.js y el backend FastAPI** de IntellectClone. Todo lo que la UI muestra, todo lo que el admin hace, todo lo que un asesor consulta, pasa por esta API.

### Cinco principios

**Primero, REST sobre recursos canónicos.** Cada entidad del modelo de datos tiene su conjunto de endpoints CRUD: `/api/v1/personas`, `/api/v1/papers`, `/api/v1/gemelos`. La estructura es predecible, autodocumentada, y se mapea 1 a 1 con los recursos que el usuario manipula.

**Segundo, búsqueda compleja como recurso aparte.** Para vistas que combinan múltiples filtros, agregaciones y joins, hay endpoints dedicados bajo `/api/v1/buscar/*`. No se intenta forzar todo a REST puro porque la UI necesita queries que cruzan recursos.

**Tercero, endpoints de acción para flujos no-CRUD.** Validar un gemelo, disparar una cosecha, regenerar un perfil son **acciones**, no creaciones de recursos. Estos endpoints son `POST /api/v1/.../action/{nombre_accion}` con cuerpo descriptivo. Más legible que forzar a CRUD lo que conceptualmente no lo es.

**Cuarto, separación estricta entre lectura y escritura.** Los endpoints `GET` son idempotentes y cacheables. Los endpoints que modifican estado (`POST`, `PATCH`, `DELETE`) están claramente marcados, requieren autenticación con permisos específicos, y se registran en auditoría.

**Quinto, OpenAPI como contrato vivo.** FastAPI auto-genera la documentación OpenAPI 3.1. La UI Next.js debería usar esa especificación para generar tipos TypeScript automáticamente (con `openapi-typescript`). Esto elimina desincronización entre frontend y backend.

### Lo que la API interna NO es

- **No es la API de exportación a Mirrorfish.** Esa es `/export/v1/*`, definida en documento 06, con tokens propios y políticas separadas. La API interna es `/api/v1/*` y nunca se cruzan.
- **No es API pública para terceros.** Solo es accesible desde el frontend Next.js de IntellectClone, autenticado.
- **No expone gemelos en estado distinto de los validados a usuarios sin permisos de admin.** La política de visibilidad se aplica en cada endpoint según el rol.

---

## 2. Diferencias con la API de exportación

Vale la pena reflejar en una tabla la separación, porque ambas APIs viven en el mismo backend pero tienen propósitos distintos.

| Aspecto | API interna `/api/v1/*` | API exportación `/export/v1/*` |
|---|---|---|
| Consumidor | Frontend Next.js (UI) | Mirrorfish externo |
| Autenticación | JWT (usuario humano) | Bearer token (machine-to-machine) |
| Operaciones | Lectura + escritura completa | Solo lectura |
| Datos visibles | Según rol (admin ve todo, lectura ve poco) | Solo gemelos validados |
| Rate limiting | Por usuario JWT | Por token de exportación |
| Versionado | v1, evoluciona con la UI | v1, contrato estable largo plazo |
| Auditoría | Cada acción registrada | Solo accesos para auditoría |
| Esquemas | Pydantic optimizados para UI | Esquema canónico definido en doc 06 |

Esta separación es **buena ingeniería**: cada API tiene su propósito, su seguridad, su evolución. Compartir backend ahorra código; compartir API confunde y arriesga.

---

## 3. Autenticación con JWT

### Mecanismo

JWT con refresh tokens, estándar moderno. Implementación con `python-jose` o `pyjwt` en el backend; en el frontend Next.js, manejados por NextAuth.js v5.

### Endpoints de autenticación

**`POST /api/v1/auth/login`**

Request:
```json
{
  "email": "asesor@uat.edu.mx",
  "password": "..."
}
```

Response 200:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900,
  "usuario": {
    "id": "...",
    "email": "asesor@uat.edu.mx",
    "nombre": "Asesor de Rectoría",
    "rol": "asesor"
  }
}
```

Response 401: credenciales inválidas.

**`POST /api/v1/auth/refresh`**

Request:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

Response 200: nuevo `access_token` y opcionalmente nuevo `refresh_token` (rotación).

**`POST /api/v1/auth/logout`**

Invalida el refresh token actual (lo agrega a una blocklist en Redis con TTL hasta su expiración natural).

**`GET /api/v1/auth/me`**

Devuelve el usuario actual desde el JWT. Útil para que el frontend valide sesión al inicio.

**`POST /api/v1/auth/cambiar_password`**

Request:
```json
{
  "password_actual": "...",
  "password_nuevo": "..."
}
```

Requiere autenticación. Invalida todos los refresh tokens del usuario.

### Configuración de JWT

```python
JWT_SECRET = os.environ["JWT_SECRET"]            # 256-bit random, en .env
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15                 # tokens cortos, refresh frecuente
REFRESH_TOKEN_EXPIRE_DAYS = 7                    # 1 semana de sesión sin login
REFRESH_TOKEN_ROTATION = True                    # cada uso del refresh genera uno nuevo
```

### Claims del JWT

```json
{
  "sub": "user_uuid",
  "email": "asesor@uat.edu.mx",
  "rol": "asesor",
  "iat": 1714780800,
  "exp": 1714781700,
  "jti": "token_uuid"
}
```

`jti` se usa para invalidación selectiva en blocklist Redis si fuera necesario.

### Política de password

- Mínimo 12 caracteres.
- Hash con `bcrypt` (no SHA, no MD5).
- No reutilización de los últimos 3 passwords.
- Cambio forzado cada 6 meses para roles `admin` y `rectoria`.

---

## 4. Roles y permisos

Heredados del enum `rol_usuario` definido en el modelo de datos. La política se aplica con un decorador FastAPI `require_role()`:

```python
@router.post("/personas", dependencies=[Depends(require_role(["admin"]))])
async def crear_persona(...): ...
```

### Matriz de permisos

| Operación | admin | rectoria | asesor | secretaria | investigador | lectura |
|---|---|---|---|---|---|---|
| Ver listado de personas | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ver detalle de persona | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Crear persona manual | ✓ | — | — | — | — | — |
| Editar metadatos persona | ✓ | — | ✓* | — | ✓** | — |
| Eliminar persona | ✓ | — | — | — | — | — |
| Ver gemelo validado | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Ver gemelo en borrador | ✓ | — | ✓ | — | ✓** | — |
| Validar gemelo | ✓ | — | ✓ | — | ✓** | — |
| Regenerar gemelo | ✓ | — | ✓ | — | — | — |
| Disparar cosecha | ✓ | — | — | — | — | — |
| Crear token de exportación | ✓ | — | — | — | — | — |
| Ver auditoría completa | ✓ | ✓ | — | — | — | — |
| Ver presupuesto LLM | ✓ | ✓ | ✓ | — | — | — |

\* asesor solo puede editar campos no críticos (no nivel_snii ni dependencia).
\** investigador solo puede sobre su propio perfil (vía `usuario_sistema.persona_id`).

---

## 5. Estructura de endpoints

### Convenciones

- Base URL: `https://intellectclone.uat.edu.mx/api/v1` (o equivalente local).
- Todos los endpoints retornan JSON.
- Ningún endpoint requiere parámetros en el body para `GET`.
- Todos los endpoints autenticados, salvo `/auth/login` y `/auth/refresh`.
- Convención de nombres: kebab-case en URLs (`/cuerpos-academicos`), snake_case en JSON.
- Identificadores: UUIDs en path params.

### Agrupación

```
/api/v1/
├── auth/                    Autenticación y sesión
├── personas/                CRUD de personas
├── papers/                  Lectura de papers (no se crean a mano)
├── coautorias/              Lectura de coautorías
├── gemelos/                 Lectura, validación, regeneración
├── dependencias/            Lectura de dependencias UAT
├── cuerpos-academicos/      Lectura
├── areas-conocimiento/      Lectura
├── temas/                   Tronco común UAT (admin gestiona)
├── cosechas/                Disparar y consultar cosechas
├── tokens-export/           Gestión de tokens de exportación
├── usuarios/                Gestión de usuarios del sistema
├── auditoria/               Lectura de logs (solo admin/rectoria)
├── buscar/                  Endpoints de búsqueda compleja
└── stats/                   Métricas y dashboards
```

### Paginación estándar

Todos los endpoints `GET` que devuelvan listas usan paginación común:

Query params:
- `limit` (int, default 50, max 200)
- `offset` (int, default 0)
- `sort` (string, ej `nombre`, `-fecha_creacion` para descendente)

Response:
```json
{
  "total": 187,
  "limit": 50,
  "offset": 0,
  "items": [...],
  "next_offset": 50
}
```

---

## 6. Endpoints de personas

### `GET /api/v1/personas`

Lista personas con filtros básicos.

Query params:
- `tipo`: `investigador | docente | estudiante | directivo | administrativo | externo`
- `dependencia_id`: UUID
- `cuerpo_academico_id`: UUID
- `nivel_snii`: enum
- `tiene_gemelo_validado`: boolean
- `q`: búsqueda fuzzy en nombre normalizado
- `limit`, `offset`, `sort`

Response 200:
```json
{
  "total": 700,
  "items": [
    {
      "id": "...",
      "nombre_completo": "María Elena Cárdenas Ruiz",
      "tipo": "investigador",
      "nivel_snii": "nivel_2",
      "dependencia": { "id": "...", "nombre": "Facultad de Ingeniería..." },
      "cuerpo_academico": { "id": "...", "nombre": "Sistemas Inteligentes" },
      "metricas": {
        "total_publicaciones": 47,
        "total_citas": 1284,
        "indice_h": 23
      },
      "estado_gemelo": "validado",
      "actualizada_en": "2026-04-16T..."
    }
  ]
}
```

### `GET /api/v1/personas/{id}`

Detalle completo de una persona.

Response 200:
```json
{
  "id": "...",
  "nombre_completo": "...",
  "primer_nombre": "...",
  "apellido_paterno": "...",
  "apellido_materno": "...",
  "tipo": "investigador",
  "orcid": "0000-0002-1234-5678",
  "openalex_id": "A1234567890",
  "scopus_id": null,
  "cvu_conacyt": null,
  "dependencia": { ... },
  "cuerpo_academico": { ... },
  "cargo": "Profesora de Tiempo Completo",
  "nivel_snii": "nivel_2",
  "snii_vigente_hasta": "2027-12-31",
  "grado_maximo": "doctorado",
  "grado_disciplina": "Ciencias de la Computación",
  "metricas": { ... },
  "areas": [
    { "id": "...", "nombre": "...", "peso": 0.85 }
  ],
  "gemelo_actual": {
    "id": "...",
    "version": 3,
    "estado": "validado",
    "scores": { "veracidad": 0.85, "completitud": 0.78, "consistencia": 0.91 }
  },
  "historico_dependencias": [...],
  "fuente_principal": "openalex",
  "activa": true,
  "metadatos": {}
}
```

### `POST /api/v1/personas`

Crear persona manualmente. Solo admin.

Request:
```json
{
  "nombre_completo": "...",
  "tipo": "investigador",
  "dependencia_id": "...",
  "cuerpo_academico_id": "...",
  "orcid": "...",
  "nivel_snii": "nivel_1"
}
```

Response 201: persona creada.
Response 409: si ya existe persona con ese ORCID o nombre+dependencia.

### `PATCH /api/v1/personas/{id}`

Editar parcial de persona. Permisos según matriz.

Request: subset de campos editables.

Response 200: persona actualizada.

### `DELETE /api/v1/personas/{id}`

No elimina físicamente. Marca `activa=false`, `motivo_baja`, `fecha_baja`. Solo admin.

Request:
```json
{
  "motivo": "Solicitud explícita de la persona retratada",
  "eliminar_fisicamente_en_dias": 90
}
```

Response 200.

### `GET /api/v1/personas/{id}/papers`

Lista paginada de papers de la persona.

### `GET /api/v1/personas/{id}/coautores`

Red de coautoría de la persona. Devuelve lista de personas con quienes ha co-autoreado, con conteo y peso.

### `GET /api/v1/personas/{id}/areas`

Áreas de expertise con sus pesos.

---

## 7. Endpoints de papers y coautorías

### `GET /api/v1/papers`

Lista de papers con filtros.

Query params:
- `año`: filtrar por año
- `tipo`: enum
- `concepto`: substring en conceptos
- `q`: fuzzy en título
- `solo_doi`: boolean
- `limit`, `offset`, `sort`

### `GET /api/v1/papers/{id}`

Detalle completo de un paper, incluyendo lista de coautores con sus personas vinculadas.

### `GET /api/v1/papers/{id}/coautores`

Lista de personas que coautoraron este paper.

### `GET /api/v1/coautorias`

Lista paginada de coautorías. Útil para construir red de colaboración.

Query params:
- `persona_id`: filtrar por persona
- `paper_id`: filtrar por paper

---

## 8. Endpoints de gemelos

### `GET /api/v1/gemelos`

Lista gemelos según rol y filtros.

Query params:
- `persona_id`: filtrar por persona
- `estado`: enum (admins ven todos los estados, otros solo `validado`/`publicado`)
- `version_actual`: boolean (default true)
- `score_veracidad_min`: 0..1
- `interpretacion`: `perfil_solido | perfil_aceptable | perfil_limitado`

### `GET /api/v1/gemelos/{id}`

Detalle completo del gemelo. Estructura idéntica a la del contrato de exportación (documento 06), reutilizando el mismo serializador.

### `GET /api/v1/personas/{persona_id}/gemelos`

Histórico de versiones del gemelo de una persona. Solo admin/asesor pueden ver versiones archivadas; otros solo ven la actual.

### `POST /api/v1/gemelos/regenerar`

Dispara regeneración de gemelo(s).

Request:
```json
{
  "modo": "individual",
  "persona_ids": ["..."],
  "modo_corpus": "profundo",
  "modelo_perfilador": "claude-sonnet-4-6",
  "razon": "manual_individual"
}
```

Modos disponibles:
- `individual`: regenera el gemelo de las personas listadas.
- `por_filtro`: regenera todos los gemelos que cumplan filtros (cuerpo académico, área, etc.).
- `total`: regenera todos los gemelos del sistema (requiere doble confirmación, advertencia de costo).

Response 202:
```json
{
  "tarea_id": "celery_task_uuid",
  "personas_afectadas": 1,
  "costo_estimado_usd": 0.15,
  "estado": "en_cola"
}
```

### `GET /api/v1/gemelos/{id}/system-prompt`

Devuelve solo el `system_prompt` operativo del gemelo. Útil para previsualizaciones rápidas en la UI.

### `GET /api/v1/gemelos/{id}/linaje`

Lista los papers y documentos que se usaron para construir esta versión del gemelo.

---

## 9. Endpoints de validación humana

Esta es la sección que materializa la decisión de "UI dedicada de validación con comentarios y sugerencias".

### Modelo de datos auxiliar

Necesitamos una tabla nueva no incluida en el modelo original:

```sql
CREATE TABLE validacion_gemelo (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gemelo_id                   UUID NOT NULL REFERENCES gemelo (id) ON DELETE CASCADE,
    validador_id                UUID NOT NULL REFERENCES usuario_sistema (id),
    decision                    VARCHAR(30) NOT NULL,    -- 'aprobado' | 'rechazado' | 'requiere_correccion'
    comentario_general          TEXT,
    observaciones_por_dimension JSONB,                   -- {"hexaco_extraversion": "...", "schwartz_universalismo": "..."}
    sugerir_regeneracion        BOOLEAN NOT NULL DEFAULT FALSE,
    sugerencias_prompt          TEXT,                    -- feedback al perfilador
    tiempo_invertido_segundos   INTEGER,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_validacion_gemelo ON validacion_gemelo (gemelo_id);
CREATE INDEX idx_validacion_validador ON validacion_gemelo (validador_id);
CREATE INDEX idx_validacion_decision ON validacion_gemelo (decision);
```

Esto se agrega como migración Alembic posterior al esquema inicial. Razón de no incluirlo en el SQL inicial: cuando diseñamos el modelo, no habíamos decidido aún el flujo de validación.

### Endpoints

### `GET /api/v1/validacion/pendientes`

Lista gemelos en estado `borrador` esperando validación.

Query params:
- `priorizar`: `por_score | por_fecha | por_relevancia`
- `cuerpo_academico_id`: filtrar
- `nivel_snii`: filtrar

Response: lista con preview rápido de cada gemelo (nombre persona, scores, fecha generación).

### `GET /api/v1/validacion/gemelo/{gemelo_id}`

Vista completa de un gemelo en modo validación. Incluye:
- El gemelo completo (todas las dimensiones).
- Snippets de evidencia textual para revisión rápida.
- Comparación con la versión anterior si existe.
- Histórico de validaciones previas si las hay.

### `POST /api/v1/validacion/gemelo/{gemelo_id}/aprobar`

Aprobar gemelo. Cambia estado a `validado` y registra en `validacion_gemelo`.

Request:
```json
{
  "comentario_general": "...",
  "observaciones_por_dimension": {
    "hexaco_responsabilidad": "Bien capturado, evidencia clara"
  },
  "tiempo_invertido_segundos": 420
}
```

Response 200.

### `POST /api/v1/validacion/gemelo/{gemelo_id}/rechazar`

Rechazar gemelo. Cambia estado a `error`, registra razones, NO se reusa.

Request:
```json
{
  "comentario_general": "El perfil es muy genérico, no captura la especificidad de la persona",
  "observaciones_por_dimension": {
    "idiolecto_modus_operandi": "Demasiado vago, podría ser cualquier ingeniero"
  },
  "sugerencias_prompt": "El prompt del idiolecto debería pedir ejemplos textuales más específicos"
}
```

Response 200.

### `POST /api/v1/validacion/gemelo/{gemelo_id}/solicitar-correccion`

El gemelo necesita ajustes pero no es un rechazo total. Marca para regeneración con feedback específico.

Request:
```json
{
  "dimensiones_a_corregir": ["hexaco_extraversion", "valores_schwartz"],
  "comentario_general": "...",
  "observaciones_por_dimension": {...},
  "regenerar_inmediatamente": true
}
```

Si `regenerar_inmediatamente=true`, dispara regeneración Celery automáticamente con el feedback como contexto adicional al prompt.

### `GET /api/v1/validacion/historico`

Lista validaciones realizadas. Filtros por validador, decisión, rango de fechas.

### `GET /api/v1/validacion/stats`

Estadísticas agregadas: cuántos gemelos validados por mes, tasa de aprobación, tiempo promedio invertido por validación, sugerencias más frecuentes (útil para mejorar prompts del perfilador).

---

## 10. Endpoints de cosechas

Implementan la decisión de "cosecha solo manual" del documento 04.

### `GET /api/v1/cosechas`

Histórico de corridas de cosecha.

Query params: `fuente`, `estado`, `desde`, `hasta`.

### `GET /api/v1/cosechas/{id}`

Detalle de una corrida específica con log estructurado de errores.

### `GET /api/v1/cosechas/estado-fuentes`

Estado actual de cada fuente: última cosecha, próxima recomendada, número de registros, errores recientes.

Response:
```json
{
  "fuentes": [
    {
      "nombre": "openalex",
      "ultima_cosecha": "2026-05-01T...",
      "estado_ultima": "completada",
      "registros_totales": 3812,
      "registros_nuevos_ultima": 47,
      "advertencia": null
    },
    {
      "nombre": "snii_uat",
      "ultima_cosecha": "2026-04-01T...",
      "estado_ultima": "completada",
      "registros_totales": 583,
      "advertencia": "Cosecha desactualizada (más de 30 días)"
    }
  ]
}
```

### `POST /api/v1/cosechas/disparar`

Solo admin. Inicia una corrida.

Request:
```json
{
  "fuente": "openalex",
  "modo": "incremental",
  "parametros": {
    "from_date": "2026-04-01"
  }
}
```

Response 202:
```json
{
  "cosecha_id": "...",
  "tarea_celery_id": "...",
  "estimacion_duracion_minutos": 5
}
```

### `POST /api/v1/cosechas/{id}/cancelar`

Solo admin. Cancela una cosecha en curso.

### `GET /api/v1/cosechas/{id}/progreso`

Progreso en vivo de una corrida. La UI hace polling cada 2-3 segundos.

Response:
```json
{
  "estado": "en_curso",
  "progreso_porcentaje": 67,
  "registros_procesados": 2540,
  "registros_estimados_totales": 3800,
  "velocidad_rps": 8.5,
  "eta_segundos": 148,
  "errores_count": 2,
  "ultimo_error": { ... }
}
```

---

## 11. Endpoints de tokens de exportación

Para que admin gestione los tokens que Mirrorfish usa para consumir la API de exportación.

### `GET /api/v1/tokens-export`

Lista tokens activos.

### `POST /api/v1/tokens-export`

Crear nuevo token.

Request:
```json
{
  "nombre": "mirrorfish_main",
  "permisos": ["read:gemelos", "read:personas"],
  "expira_en": "2027-05-03T00:00:00Z"
}
```

Response 201: incluye el token plano **una sola vez** (después solo se ve el hash).

```json
{
  "id": "...",
  "nombre": "mirrorfish_main",
  "token": "mfsh_abc123...",
  "permisos": [...],
  "expira_en": "..."
}
```

### `PATCH /api/v1/tokens-export/{id}`

Actualizar permisos o nombre.

### `DELETE /api/v1/tokens-export/{id}`

Revocar (marca `activo=false`, no borra para preservar histórico).

### `GET /api/v1/tokens-export/{id}/uso`

Estadísticas de uso del token: requests por día, endpoints más usados, errores.

---

## 12. Endpoints de búsqueda compleja

Para vistas que combinan múltiples filtros y agregaciones que no encajan en CRUD puro.

### `POST /api/v1/buscar/personas-avanzado`

Búsqueda compleja de personas con múltiples filtros booleanos.

Request:
```json
{
  "filtros": {
    "and": [
      {"nivel_snii": ["nivel_2", "nivel_3"]},
      {"areas": ["uuid1", "uuid2"]},
      {"or": [
        {"dependencia_id": "uuid_facultad"},
        {"cuerpo_academico_id": "uuid_ca"}
      ]},
      {"score_veracidad_min": 0.7}
    ]
  },
  "ordenar_por": "indice_h",
  "limit": 100
}
```

Response: estructura paginada estándar.

Razón de POST en lugar de GET: query params no soportan estructura booleana compleja sin volverse ilegibles.

### `POST /api/v1/buscar/red-coautoria`

Construcción del grafo de coautoría para visualización.

Request:
```json
{
  "centro": {
    "tipo": "persona",
    "id": "uuid"
  },
  "max_distancia": 2,
  "min_coautorias": 2
}
```

Response: nodos y aristas del grafo en formato compatible con D3.

```json
{
  "nodos": [
    {"id": "...", "nombre": "...", "tipo": "investigador", "papers": 47}
  ],
  "aristas": [
    {"source": "...", "target": "...", "peso": 12, "primer_año": 2018}
  ]
}
```

### `POST /api/v1/buscar/papers-similares`

Encuentra papers similares semánticamente usando embeddings (pgvector).

Request:
```json
{
  "paper_id": "...",
  "limit": 20,
  "umbral_similitud": 0.7
}
```

### `POST /api/v1/buscar/personas-afines`

Personas con perfil de gemelo similar (clustering por embedding del gemelo).

---

## 13. Endpoints de administración

### `GET /api/v1/usuarios`

Lista usuarios del sistema. Solo admin.

### `POST /api/v1/usuarios`

Crear usuario. Solo admin.

### `PATCH /api/v1/usuarios/{id}`

Actualizar usuario. Solo admin.

### `DELETE /api/v1/usuarios/{id}`

Desactivar usuario.

### `GET /api/v1/auditoria`

Log de auditoría. Solo admin/rectoria.

Query params: `usuario_id`, `accion`, `desde`, `hasta`, `entidad_tipo`.

### `GET /api/v1/temas`

Lista de temas del tronco común UAT (los 18 que evalúa el perfilador).

### `POST /api/v1/temas`

Crear tema. Solo admin. Esto modifica el tronco común para futuras generaciones de gemelos.

### `PATCH /api/v1/temas/{id}` y `DELETE`

Gestionar temas.

### `GET /api/v1/stats/dashboard`

Métricas para el dashboard principal del admin.

Response:
```json
{
  "personas": { "total": 700, "investigadores": 580, "con_gemelo_validado": 423 },
  "papers": { "total": 3812, "este_año": 287 },
  "gemelos": { "validados": 423, "borrador": 47, "error": 12 },
  "simulaciones_externas": { "total_30dias": 156, "tokens_consumidos_usd": 14.50 },
  "presupuesto_llm": { "limite_mensual_usd": 500, "consumido_mes_usd": 47.30 },
  "cosechas_atrasadas": ["snii_uat"]
}
```

### `GET /api/v1/stats/costos-llm`

Detalle de consumo de LLMs por persona, modelo, propósito.

---

## 14. Manejo de errores estandarizado

Todos los errores siguen formato común RFC 7807 (Problem Details for HTTP APIs), adaptado al dominio:

```json
{
  "type": "https://intellectclone.uat.edu.mx/errors/persona-no-encontrada",
  "title": "Persona no encontrada",
  "status": 404,
  "detail": "No existe persona con id 550e8400-e29b-41d4-a716-446655440000",
  "instance": "/api/v1/personas/550e8400-e29b-41d4-a716-446655440000",
  "request_id": "req_abc123"
}
```

### Códigos HTTP usados

- `200`: éxito con respuesta.
- `201`: recurso creado.
- `202`: aceptado (tarea asíncrona iniciada, devuelve `tarea_id`).
- `204`: éxito sin respuesta (deletes).
- `400`: bad request (validación de input).
- `401`: no autenticado.
- `403`: autenticado pero sin permisos.
- `404`: recurso no existe.
- `409`: conflicto (duplicado, estado inválido).
- `422`: validación Pydantic falló (FastAPI lo genera).
- `429`: rate limit.
- `500`: error interno (con stack trace solo en log, no en response).
- `503`: servicio no disponible (cosecha caída, LLM no responde).

### Errores de validación Pydantic

FastAPI los maneja por defecto con código 422 y estructura:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 15. Convenciones globales

### Headers comunes

Todos los responses incluyen:
- `X-Request-ID`: UUID único del request, también en logs.
- `X-Response-Time-Ms`: tiempo de procesamiento.
- `X-Schema-Version`: versión del schema actual.

### Cache

Endpoints de lectura cacheables (estáticos como `/dependencias`, `/areas-conocimiento`, `/temas`):
- `Cache-Control: public, max-age=3600`
- `ETag` para validación condicional.

Endpoints dinámicos (personas, gemelos, cosechas):
- `Cache-Control: no-cache`

### CORS

Configurado para aceptar solo el origen del frontend Next.js (`https://intellectclone.uat.edu.mx` o equivalente).

```python
CORS_ALLOWED_ORIGINS = ["https://intellectclone.uat.edu.mx"]
```

En desarrollo, se permite también `http://localhost:3000`.

### Rate limiting

Por usuario JWT:
- Endpoints de lectura: 300 requests/minuto.
- Endpoints de escritura: 60 requests/minuto.
- Endpoints de regeneración o cosecha: 10 requests/minuto.

Implementado con `slowapi` o middleware custom contra Redis.

### Auditoría

Cada request a endpoint de escritura (POST, PATCH, DELETE) registra automáticamente:

```sql
INSERT INTO auditoria (usuario_id, accion, entidad_tipo, entidad_id, detalle, ip_origen, user_agent)
VALUES (...)
```

Esto sucede en middleware FastAPI, sin que cada handler tenga que recordarlo.

### Documentación OpenAPI

FastAPI genera automáticamente:
- `/docs` (Swagger UI) — solo accesible en desarrollo.
- `/redoc` (ReDoc) — solo accesible en desarrollo.
- `/openapi.json` — siempre disponible para que el frontend genere tipos TypeScript.

En producción, los endpoints `/docs` y `/redoc` se desactivan o requieren autenticación de admin.

---

## Cierre del paquete técnico

Este es el último documento técnico del paquete v1 de IntellectClone. Con esto, Claude Code tiene:

1. **Visión:** documento conceptual.
2. **Plan:** especificación operativa con fases y criterios de cierre.
3. **Datos:** modelo de datos validado contra PostgreSQL real + SQL ejecutable.
4. **Cosecha:** especificaciones de harvesters por fuente.
5. **Cerebro:** perfilador HEXACO + Schwartz + idiolecto + posturas.
6. **Salida externa:** contrato de exportación a Mirrorfish.
7. **Roadmap:** ruta de absorción a v1.5.
8. **API interna:** este documento, que conecta todo con la UI.
9. **Diseño visual:** prompt para Claude Design (cuando esté disponible).
10. **Trazabilidad:** changelog del alcance.

El paquete está cerrado y listo para handoff a Claude Code.

---

## Mensaje a Claude Code

Si estás leyendo el paquete completo:

1. Lee los documentos en orden: 01, 02, 03, 04, 05, 06, 06-bis, 07, CHANGELOG.
2. Antes de escribir código, dime qué entendiste y qué dudas tienes.
3. No saltes fases del plan operativo (documento 02). Construye en orden.
4. La API interna (este documento) se construye en Fase B y se expande en cada fase posterior conforme nuevos endpoints son necesarios.
5. La separación entre `/api/v1/*` (UI) y `/export/v1/*` (Mirrorfish) es **invariante**. No las mezcles.
6. Implementa los endpoints más críticos primero: auth, personas (lectura), gemelos (lectura). Después escritura. Después validación. Después tokens y admin.

Tiempo estimado de implementación API interna: distribuido en todas las fases, aproximadamente 30% del esfuerzo backend total. La API es la columna vertebral; cada feature de la UI consume varios endpoints.

---

*Fin del documento técnico 07. Versión 0.1 — pendiente de validación de Fernando.*
*Fin del paquete v1 de IntellectClone.*
