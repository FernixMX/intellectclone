# IntellectClone — Especificación operativa para construcción

**Audiencia de este documento:** Claude Code (agente constructor)
**Documento complementario:** `IntellectClone_Fase1_Documento_Conceptual.md` (visión y alcance)
**Versión:** 0.1 — base para iteración

---

## Cómo leer este documento

Este es un documento técnico operativo. No describe qué hace el producto ni para qué sirve (eso está en el documento conceptual de Fase 1). Describe **cómo se construye**, en qué orden, con qué tecnologías, y bajo qué contratos. Está escrito para que Claude Code pueda leerlo, entender el alcance del trabajo, y ejecutarlo con interrupciones mínimas al usuario humano.

Si hay contradicción entre este documento y el conceptual, gana este. Si hay ambigüedad, pregunta antes de decidir.

---

## Identidad del proyecto

- **Nombre del producto:** IntellectClone
- **Nombre del repositorio sugerido:** `intellectclone`
- **Idioma del código y comentarios:** español neutro para identificadores de dominio académico (persona, paper, dependencia, cuerpo_academico) y comentarios; inglés para identificadores genéricos de programación (handler, response, error). Razón: esto va a ser leído y mantenido por personal UAT en algún momento.
- **Idioma de la UI:** español como idioma primario, inglés como secundario opcional en v2.
- **Licencia:** por definir con el usuario antes de publicar el repo.

---

## Restricciones del entorno de despliegue

- VPS Linux IONOS con acceso root.
- Distribución asumida: Ubuntu 24.04 LTS. Si el VPS viene con otra distro, ajustar las instrucciones de instalación pero mantener el stack.
- Recursos del VPS por confirmar con el usuario antes de configurar Docker (CPU, RAM, disco). Diseño asume mínimo razonable: 4 vCPU, 8 GB RAM, 100 GB SSD.
- Sin dominio asignado todavía. Diseñar para que el dominio sea variable de configuración, no esté hardcoded en ningún lado.
- Conexión a internet desde el VPS para cosechar fuentes externas y consumir APIs de LLMs.

---

## Stack técnico definitivo

### Backend
- **Lenguaje:** Python 3.12.
- **Framework web:** FastAPI (última estable).
- **ORM:** SQLAlchemy 2.x con tipado estricto.
- **Validación de datos:** Pydantic v2.
- **Migraciones:** Alembic.
- **Cosecha:** httpx para HTTP, sickle para OAI-PMH, pyalex para OpenAlex, BeautifulSoup4 para scraping HTML, playwright solo si es estrictamente necesario.
- **Tareas asíncronas:** Celery con broker Redis.
- **Cliente LLMs:** anthropic, openai, google-genai. Capa propia de abstracción para intercambiar modelos sin cambiar lógica de negocio.

### Almacenamiento
- **Base de datos primaria:** PostgreSQL 16.
- **Extensiones requeridas:** pgvector (búsqueda semántica de papers y perfiles), pg_trgm (búsqueda de texto fuzzy), unaccent (búsqueda sin acentos).
- **Cache y broker:** Redis 7.
- **Almacenamiento de archivos:** sistema de archivos local del VPS bajo `/var/intellectclone/storage/`. PDFs de papers, exportaciones, backups temporales.

### Frontend
- **Framework:** Next.js 15 (App Router) con TypeScript estricto.
- **UI components:** shadcn/ui sobre Tailwind CSS.
- **Estado del cliente:** Zustand para estado global ligero, React Query para data fetching.
- **Visualizaciones:** Recharts para gráficos básicos, D3 para la red de colaboración.
- **Autenticación:** NextAuth.js v5 con provider de email + password en v1; preparar adapters para OAuth UAT en v2.

### Infraestructura
- **Contenedores:** Docker + Docker Compose.
- **Reverse proxy:** Nginx.
- **SSL:** Certbot (Let's Encrypt) automatizado.
- **Logs:** Docker logs centralizados, opcionalmente Loki + Grafana en fase posterior.
- **Backups:** script bash con rsync a almacenamiento externo, programado vía cron.

### Desarrollo
- **Gestor de paquetes Python:** uv (más rápido que pip, mejor lockfile).
- **Linter Python:** ruff.
- **Type checker Python:** mypy en modo estricto.
- **Linter JS/TS:** ESLint + Prettier.
- **Tests Python:** pytest + pytest-asyncio.
- **Tests JS/TS:** Vitest.
- **Pre-commit hooks:** ruff, mypy, prettier.

---

## Estructura de repositorio

```
intellectclone/
├── README.md                      # Visión general y arranque rápido
├── docs/
│   ├── 01_documento_conceptual.md
│   ├── 02_especificacion_operativa.md  (este documento)
│   ├── 03_modelo_de_datos.md
│   ├── 04_especificaciones_harvesters.md
│   ├── 05_perfilador_y_gemelo.md
│   ├── 06_simulador_mirrorfish.md
│   ├── 07_api_interna.md
│   └── 08_ui_componentes.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── nginx/
│   └── intellectclone.conf
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   └── restore.sh
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   ├── intellectclone/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── harvesters/
│   │   │   ├── base.py
│   │   │   ├── openalex.py
│   │   │   ├── vufind_uat.py
│   │   │   ├── riuat.py
│   │   │   └── snii_uat.py
│   │   ├── normalizer/
│   │   ├── perfilador/
│   │   ├── gemelo/
│   │   ├── simulador/
│   │   ├── llm/
│   │   ├── tasks/             # Celery tasks
│   │   └── utils/
│   └── tests/
└── frontend/
    ├── package.json
    ├── pnpm-lock.yaml
    ├── Dockerfile
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── src/
    │   ├── app/
    │   │   ├── (public)/
    │   │   │   ├── directorio/
    │   │   │   ├── persona/[id]/
    │   │   │   ├── explorador/
    │   │   │   └── acerca/
    │   │   ├── (privado)/
    │   │   │   ├── simulador/
    │   │   │   ├── simulaciones/
    │   │   │   └── admin/
    │   │   ├── api/
    │   │   └── layout.tsx
    │   ├── components/
    │   │   ├── ui/             # shadcn primitives
    │   │   ├── perfil/
    │   │   ├── red-colaboracion/
    │   │   └── simulador/
    │   ├── lib/
    │   └── stores/
    └── tests/
```

Esta estructura no es negociable en lo macro (división backend/frontend, separación de capas dentro del backend). En lo fino, Claude Code puede ajustar nombres de carpetas si tiene una mejor propuesta y la justifica.

---

## Plan de construcción por fases

Construir en orden estricto. No saltar fases ni paralelizar más allá de lo indicado.

### Fase A — Cimientos (semana 1)
1. Configurar repo Git con la estructura de carpetas.
2. Configurar entorno de desarrollo Python con uv y entorno frontend con pnpm.
3. Configurar pre-commit hooks (ruff, mypy, prettier).
4. Configurar `docker-compose.dev.yml` con PostgreSQL 16 + Redis levantados localmente.
5. Configurar Alembic para migraciones.
6. Configurar tests vacíos pero corriendo (pytest, vitest).
7. Configurar CI mínimo (GitHub Actions o equivalente, según preferencia del usuario).
8. **Punto de control con usuario:** demostrar repo arrancando localmente.

### Fase B — Modelo de datos y API base (semana 2)
1. Implementar modelos SQLAlchemy según `03_modelo_de_datos.md` (documento por crear en Fase 2 contigo).
2. Crear migraciones iniciales.
3. Crear endpoints CRUD básicos en FastAPI para personas, papers, dependencias, cuerpos académicos.
4. Crear pruebas unitarias para los modelos y endpoints CRUD.
5. **Punto de control con usuario:** demostrar API corriendo, crear/leer una persona dummy.

### Fase C — Cosechadores (semanas 3-4)
1. Implementar `BaseHarvester` con la interfaz común (definida en `04_especificaciones_harvesters.md`).
2. Implementar `OpenAlexHarvester` (la fuente más rica y estable).
3. Implementar `VuFindUATHarvester` (vía scraping HTML estructurado).
4. Implementar `RIUATHarvester` (intentar OAI-PMH, fallback a scraping HTML por handle).
5. Implementar `SNIIUATHarvester` (scraping de ASP.NET, lo más complejo, dejar al final).
6. Implementar normalizador y desambiguador de autores.
7. Configurar tareas Celery programadas para cosechas periódicas.
8. **Punto de control con usuario:** ejecutar cosecha completa, mostrar acumulado UAT v1 en base de datos.

### Fase D — Capa de gemelos (semanas 5-6)
1. Implementar capa de abstracción de LLMs (`llm/`).
2. Implementar perfilador según `05_perfilador_y_gemelo.md`.
3. Implementar generador de gemelo digital con esquema Pydantic estricto.
4. Implementar caching y versionado de gemelos.
5. Generar gemelos para una muestra de 10-20 investigadores piloto.
6. **Punto de control con usuario:** validar manualmente la calidad de los gemelos piloto antes de generar en masa.

### Fase E — Simulador (semana 7)
1. Implementar `Mirrorfish UAT` según `06_simulador_mirrorfish.md`.
2. Implementar selector de cohortes (filtros por SNII, área, dependencia, etc).
3. Implementar ejecutor paralelo con control de concurrencia y rate limits.
4. Implementar agregador de respuestas con análisis básico (postura, intensidad, citas).
5. Implementar persistencia de simulaciones (auditoría completa).
6. **Punto de control con usuario:** ejecutar primera simulación completa con escenario real.

### Fase F — UI v1 (semanas 8-10)
1. Layout base, navegación, autenticación básica con email + password.
2. Sección directorio: listado, búsqueda, filtros, perfil de persona.
3. Sección explorador: red de colaboración con D3, mapa de áreas.
4. Sección simulador: formulario de escenario, selector de cohorte, vista de resultados.
5. Vistas administrativas mínimas: gestión de usuarios, monitoreo de cosechas, gestión de simulaciones.
6. **Punto de control con usuario:** demo completa local de la UI v1.

### Fase G — Despliegue (semana 11)
1. Configurar Nginx en el VPS IONOS.
2. Configurar Certbot con dominio cuando esté disponible.
3. Configurar `docker-compose.yml` de producción.
4. Configurar backups automáticos.
5. Migrar datos del entorno de desarrollo al VPS o re-cosechar desde cero.
6. **Punto de control con usuario:** demo en producción.

### Fase H — Refinamiento y demo institucional (semana 12)
1. Pulido de UI con feedback del usuario.
2. Generación de documentación de usuario.
3. Preparación de demo para Rectoría y oficina de asesores.
4. Setup de monitoreo básico.
5. Cierre de v1.

Total: 12 semanas estimadas para v1 completa, con un humano dedicando varias horas por semana a revisar puntos de control. Si el usuario tiene más disponibilidad, las semanas se comprimen; si tiene menos, se expanden.

---

## Documentos por crear en Fase 2 (antes de empezar a construir)

Antes de que Claude Code arranque la Fase A, deben existir los siguientes documentos, que se crearán en sesiones posteriores conmigo (Claude.ai) en colaboración con el usuario:

- `03_modelo_de_datos.md` — Esquema completo de la base de datos. Personas, papers, coautorías, dependencias, cuerpos académicos, áreas, gemelos, simulaciones. Con diagrama ER y diccionario de campos.
- `04_especificaciones_harvesters.md` — Para cada harvester: fuente, frecuencia de cosecha, datos extraídos, formato de entrada/salida, manejo de errores y rate limits, tests de aceptación.
- `05_perfilador_y_gemelo.md` — Estructura del gemelo (esquema Pydantic), prompts del perfilador (migrados desde Google AI Studio), criterios de calidad, política de validación humana.
- `06_simulador_mirrorfish.md` — Protocolo de simulación, formato de prompts a gemelos, esquema de respuesta esperada, lógica de agregación, manejo de costos y límites.
- `07_api_interna.md` — Endpoints REST completos con OpenAPI, contratos de datos, autenticación, rate limits.
- `08_ui_componentes.md` — Wireframes de las pantallas principales, componentes de UI, flujos de usuario, criterios de UX.

Estos documentos los iremos generando en orden conforme avancemos. Claude Code no debe iniciar la fase B hasta que `03_modelo_de_datos.md` esté firmado por el usuario, y así sucesivamente.

---

## Convenciones de código

### Python
- Tipado estricto (mypy --strict). Sin excepciones.
- Funciones públicas con docstrings en estilo Google.
- Imports ordenados con ruff (isort interno).
- Sin lógica de negocio en endpoints FastAPI: los endpoints orquestan, los servicios ejecutan.
- Sin acceso directo a la base de datos desde endpoints: siempre por capa de repositorios o servicios.
- Errores de dominio levantan excepciones tipadas que la capa de API traduce a HTTP.
- Configuración por variables de entorno + Pydantic Settings, nunca por archivos `.py`.

### TypeScript
- Modo estricto (`strict: true`).
- Sin `any`. Si es absolutamente necesario, justificar con comentario.
- Componentes server-side por defecto en Next.js, client-side solo cuando hay interactividad.
- Hooks personalizados para lógica reutilizable.
- Esquemas Zod para validación de datos en cliente.

### Naming
- Tablas y columnas en `snake_case` español: `persona`, `cuerpo_academico`, `nivel_snii`.
- Modelos Python en `PascalCase` español-inglés: `class Persona`, `class CuerpoAcademico`.
- Schemas Pydantic con sufijo según uso: `PersonaCreate`, `PersonaRead`, `PersonaUpdate`.
- Endpoints REST en `kebab-case` español: `/api/personas`, `/api/cuerpos-academicos`.
- Componentes React en `PascalCase` inglés genérico: `PersonProfile`, `SimulationForm`.

### Logs
- Estructurados (JSON) en producción, legibles en desarrollo.
- Niveles: DEBUG (desarrollo), INFO (operación normal), WARNING (cosas raras pero recuperables), ERROR (fallos), CRITICAL (necesita intervención humana inmediata).
- Sin información personal identificable en logs salvo el ID de la persona.

### Seguridad
- Secretos en variables de entorno, jamás en repo.
- API keys de LLMs en `.env`, nunca en código.
- Sanitización de inputs en endpoints públicos.
- Rate limiting por IP en endpoints públicos.
- CSP, HSTS y demás headers de seguridad en Nginx.

---

## Política de costos de LLMs

Las APIs de LLMs son la única fuente de costo variable significativa. Política:

- Toda llamada a LLM debe registrarse: modelo, tokens consumidos, costo estimado, propósito (perfilado / simulación / otro).
- La UI de simulador debe mostrar costo estimado **antes** de ejecutar y requerir confirmación por encima de un umbral configurable (sugerencia v1: $5 USD por simulación).
- Existe un presupuesto mensual configurable. Cuando se alcance el 80%, alerta al admin. Cuando se alcance el 100%, las simulaciones nuevas se bloquean hasta el siguiente período o autorización manual.
- Los gemelos generados se cachean: regenerar un gemelo solo si los datos que lo originaron han cambiado materialmente.

---

## Política de privacidad y datos

- Solo datos públicos en v1. Cualquier dato no público requiere autorización explícita por escrito de la persona y/o de Rectoría según corresponda.
- Cada persona representada como gemelo debe poder, vía formulario público, solicitar revisar su perfil, corregirlo, o ser eliminada del sistema. La política de baja debe ser tan visible como la de alta.
- Los gemelos NO son etiquetados como representaciones literales del individuo. La UI debe comunicar que son aproximaciones inferidas a partir de obra pública.
- Las simulaciones se almacenan completas pero con acceso restringido por rol. No son públicas.

---

## Criterios de cierre de v1

V1 se considera terminada cuando se cumplen todos:

- Cosecha funcionando para las cuatro fuentes con cron programado.
- Acumulado UAT v1 con al menos 200 personas con perfil completo (idealmente 500+).
- Al menos 80% de esas personas tienen gemelo digital generado y validado por revisión humana en muestra del 5%.
- UI desplegada en VPS IONOS bajo dominio HTTPS.
- Capacidad de ejecutar simulación con cohorte de 100+ gemelos en menos de 5 minutos y costo menor a $2 USD.
- Documentación de usuario básica accesible desde la UI.
- Backups automáticos configurados y probados.
- Demo a Rectoría programada y ejecutada.

---

## Lo que NO se construye en v1

Este alcance está bloqueado para v1. Cualquier propuesta para incluir alguno de estos items se documenta en backlog para v2 sin debate:

- Login con cuentas UAT (Office 365 / Azure AD).
- Cosecha de fuentes internas UAT (SIIAA, plantilla docente).
- Modelo de personas que no tienen huella pública (alumnos sin tesis, administrativos).
- Simulaciones longitudinales (evolución temporal de posturas).
- Análisis estadístico avanzado de respuestas.
- API pública para terceros.
- Integraciones con Slack, Teams o similares.
- Multi-idioma más allá de español.
- App móvil nativa.
- Versiones embebibles (widgets para sitios externos).

---

## Comunicación con el usuario humano

Claude Code debe pausar y consultar al usuario en estos momentos, sin excepción:

1. Antes de cada punto de control marcado en el plan de fases.
2. Cuando una decisión no está cubierta por estos documentos y hay más de una opción razonable.
3. Cuando una API externa cambia su comportamiento de forma que afecta el diseño.
4. Cuando un costo estimado supera lo presupuestado para esa fase.
5. Cuando una librería propuesta tiene problemas de licencia.

Claude Code puede decidir sin consultar en:

- Decisiones de implementación interna que no afectan el contrato externo.
- Refactorizaciones que mantienen la interfaz pública.
- Optimizaciones de performance.
- Mejoras menores en la UI dentro del sistema de diseño.

---

## Cómo este documento evoluciona

Este documento es vivo. Cada vez que se descubra algo durante la construcción que requiera cambiar el plan, se actualiza este documento primero, se valida con el usuario, y luego se ejecuta el cambio en código. El documento es la fuente de verdad; el código es su consecuencia, no al revés.

---

*Fin de la especificación operativa. Versión 0.1 — pendiente de validación y de generación de los documentos 03 a 08.*
