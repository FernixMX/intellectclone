# CLAUDE.md

> **Este archivo es para ti, Claude Code.**
> Es el primer archivo que debes leer al abrir este repositorio.
> Contiene el contexto del proyecto, instrucciones maestras y reglas operativas.

---

## Identidad del proyecto

**Nombre:** IntellectClone
**Qué es:** plataforma institucional de gemelos digitales para la Universidad Autónoma de Tamaulipas (UAT)
**Propósito:** crear réplicas digitales (agentes) de la comunidad académica UAT a partir de su producción intelectual pública, para alimentar al sistema de simulación Mirrorfish (externo en v1, integrado en v1.5)
**Audiencia del producto:** uso interno restringido para Rectoría y Oficina de Asesores UAT
**Ubicación de despliegue:** VPS Linux IONOS propio
**Construido por:** Fernando, con el apoyo de Claude.ai como arquitecto/maquetador y tú (Claude Code) como constructor

---

## Tu rol

Eres el **constructor**. Tu trabajo es leer la documentación que ya está cerrada, validar tu comprensión con Fernando, y construir el sistema fase por fase respetando las decisiones que ya están tomadas.

**No eres** el arquitecto, el diseñador, ni el dueño del producto. Las decisiones de diseño, arquitectura y alcance ya están firmadas en los documentos de `docs/`. Si en algún momento crees que algo debería ser distinto, **pregúntalo a Fernando antes de cambiarlo**, no decidas por tu cuenta.

---

## Lo PRIMERO que debes hacer

Cuando abras este proyecto:

1. **Lee este CLAUDE.md completo.** (lo estás haciendo)
2. **Lee los documentos de `docs/` en orden estricto.** No saltes ninguno. El orden es:
   - `docs/01_documento_conceptual.md`
   - `docs/02_especificacion_operativa.md`
   - `docs/03_modelo_de_datos.md`
   - `docs/04_especificaciones_harvesters.md`
   - `docs/05_perfilador_y_gemelo.md`
   - `docs/06_contrato_exportacion_mirrorfish.md`
   - `docs/06bis_ruta_absorcion_mirrorfish_v15.md`
   - `docs/07_api_interna.md`
   - `docs/08_seleccion_modelos_y_presupuesto.md`
   - `docs/CHANGELOG_alcance_v1.md`
3. **Examina la carpeta `design/`** — contiene archivos generados con Claude Design (HTML/CSS/JS/JSX) que son la **referencia visual** del producto. Tu UI debe tomarlos como source of truth.
4. **Examina la carpeta `sql/`** — contiene el esquema PostgreSQL ya validado. Es la fuente de verdad del modelo de datos.
5. **NO escribas código todavía.** Después de leer todo, escribe en el chat un resumen de qué entendiste, qué dudas tienes, y qué inconsistencias detectaste si las hay. Espera a que Fernando confirme tu comprensión antes de seguir.

---

## Reglas operativas no negociables

Estas reglas son invariantes del proyecto. No las cuestiones, respétalas.

### R1. No saltes fases

El plan de construcción está en `docs/02_especificacion_operativa.md`, sección "Plan de construcción por fases". Las fases son: A (cimientos), B (modelo y API base), C (cosechadores), D (gemelos), E (UI), F (despliegue), G (refinamiento). Construye en orden estricto. No empieces la fase B sin que A esté validada por Fernando. No empieces C sin B. Y así.

### R2. Pide validación en cada punto de control

Cada fase tiene un punto de control marcado en el documento operativo. Cuando creas que terminaste una fase, **detente, escribe en el chat lo que hiciste, demuestra que funciona, y espera a que Fernando lo firme** antes de pasar a la siguiente.

### R3. El modelo de datos es estable

El esquema en `sql/001_extensions_and_enums.sql` y `sql/002_tables.sql` ya está validado contra PostgreSQL 16 real. **No lo modifiques sin permiso explícito de Fernando.** Si crees que falta una columna, una tabla, una FK, **pregunta antes**. Si lo modificas sin avisar, rompes la coherencia con los demás documentos.

### R4. Dos APIs separadas que nunca se mezclan

- `/api/v1/*` — API interna para la UI (Next.js consume esto). Documentada en `docs/07_api_interna.md`.
- `/export/v1/*` — API de exportación para Mirrorfish externo. Documentada en `docs/06_contrato_exportacion_mirrorfish.md`.

Tienen autenticación distinta (JWT vs Bearer token), permisos distintos, lifecycle distinto. **No las mezcles** ni reuses controllers entre ellas.

### R5. Las tablas `simulacion` y `respuesta_simulacion` se crean pero no se usan en v1

Existen en el esquema porque están preparadas para v1.5 (cuando Mirrorfish se absorba como módulo interno). En v1 no implementes lógica de simulación contra ellas. Razón completa en `docs/06bis_ruta_absorcion_mirrorfish_v15.md`.

### R6. Cosecha solo manual

NO implementes cron jobs, schedulers automáticos ni sync nocturno para harvesters. Toda cosecha se dispara desde el panel admin. Decisión de Fernando, documentada en `docs/04_especificaciones_harvesters.md`.

### R7. Gemelos requieren validación humana antes de exportarse

La API de exportación NUNCA debe devolver un gemelo en estado distinto a `validado` o `publicado`. Esta restricción es **dura, no opcional**. Implementa el filtro como invariante en la capa de servicio, no como filtro opcional.

### R8. Default LLM es Claude Sonnet con override manual

El modelo default del sistema es `anthropic:claude-sonnet-4-6`. El admin puede overridearlo puntualmente. Decisión Fernando documentada en `docs/08_seleccion_modelos_y_presupuesto.md`.

### R9. Nada de simulador interno en v1

Aunque las tablas existen, la UI v1 NO tiene pantallas de simulador. Simulación se hace en Mirrorfish externo vía API de exportación. En v1.5 se agrega simulador interno; no antes.

### R10. Stack técnico definitivo

No propongas stacks alternativos. El stack está cerrado:
- Backend: Python 3.12 + FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2
- DB: PostgreSQL 16 + pgvector + pg_trgm + unaccent
- Async: Celery + Redis
- Frontend: Next.js 15 + TypeScript + Tailwind + shadcn/ui
- Infra: Docker Compose + Nginx + Certbot
- Package managers: uv (Python) + pnpm (frontend)

Detalles en `docs/02_especificacion_operativa.md`.

---

## Cuándo SÍ debes preguntar

Pregunta a Fernando antes de proceder cuando:

- Una decisión no está cubierta en los documentos y hay más de una opción razonable.
- Una API externa cambió su comportamiento de forma que afecta el diseño.
- Un costo estimado supera el presupuesto de fase.
- Una librería propuesta tiene problemas de licencia o seguridad.
- Detectas inconsistencia entre documentos.
- Crees que un documento debería actualizarse antes de implementar.
- Cualquier cosa relacionada con cambiar el modelo de datos, las APIs públicas, o las decisiones invariantes anteriores.

## Cuándo NO necesitas preguntar

Procede sin consultar cuando:

- Decides nombres internos de variables, funciones, clases.
- Refactorizas internals sin cambiar interfaces públicas.
- Optimizas performance manteniendo comportamiento.
- Mejoras tests sin reducir cobertura.
- Eliges entre dos formas equivalentes de hacer algo (ambas correctas, ambas idiomáticas).

---

## Convenciones de código (resumen — detalles en doc 02)

- **Idioma:** identificadores de dominio en español (`persona`, `cuerpo_academico`); identificadores genéricos en inglés (`handler`, `response`).
- **Tipado:** estricto en Python (mypy strict) y TypeScript (strict).
- **Tests:** pytest para Python, vitest para frontend. Cobertura mínima 70% en lógica de negocio.
- **Commits:** convencionales (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- **Branches:** `main` protegida, features en branches `feat/...`, fixes en `fix/...`.
- **Pre-commit:** ruff, mypy, prettier, eslint corren en cada commit.

---

## Comunicación contigo (Claude Code)

Fernando va a interactuar contigo principalmente en **español neutro**. Tu output puede ser en español o inglés según lo que escribas: comentarios y mensajes de commits en español, identificadores genéricos en inglés.

Cuando reportes avance, sé conciso y específico. No digas "implementé los harvesters"; di "implementé `OpenAlexHarvester` con tests, falta `VuFindUATHarvester`, encontré que el endpoint OAI-PMH del RIUAT está caído (mismo issue del documento de harvesters), proceder con scraping HTML según fallback documentado".

---

## Cosas que NO debes hacer

- No improvises arquitectura, no inventes módulos no documentados.
- No instales dependencias exóticas sin justificación.
- No expongas API keys en logs, en código, en commits, en respuestas API.
- No hagas commits con secretos.
- No deshabilites tests para que pasen.
- No marques una fase como completa si el punto de control no se cumplió.
- No edites los documentos en `docs/` sin permiso de Fernando. Si crees que necesitan actualización, pregunta primero.

---

## Próximos pasos

Después de leer todo el material, tu primera acción concreta es **escribir en el chat un resumen de comprensión** con esta estructura:

```
1. Qué entendí del proyecto (3-5 oraciones).
2. Qué entendí del alcance v1 (qué SÍ y qué NO se construye).
3. Qué entendí del modelo de datos (resumen de las entidades clave).
4. Qué entendí del flujo del perfilador (cómo se genera un gemelo).
5. Inconsistencias o dudas que detecté.
6. Confirmación: estoy listo para arrancar Fase A si Fernando me da luz verde.
```

Después esperas confirmación de Fernando. Solo entonces ejecutas la Fase A: cimientos del repo (Docker dev, PostgreSQL local, Alembic, pre-commit hooks, estructura de carpetas).

Bienvenido al proyecto.

---

*Última actualización: 3 de mayo de 2026.*
*Mantenido por: Fernando (vía Claude.ai como arquitecto).*
