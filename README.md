# IntellectClone

> Plataforma institucional de gemelos digitales de la comunidad académica de la Universidad Autónoma de Tamaulipas

[![Estado](https://img.shields.io/badge/estado-en%20construcci%C3%B3n-orange)]()
[![Versi%C3%B3n](https://img.shields.io/badge/versi%C3%B3n-v1--dev-blue)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)]()
[![Python](https://img.shields.io/badge/Python-3.12-3776AB)]()
[![Next.js](https://img.shields.io/badge/Next.js-15-000000)]()

---

## Qué es

IntellectClone es una plataforma que crea **réplicas digitales** (gemelos) de los miembros de la comunidad académica UAT a partir de su producción intelectual pública. Cada gemelo es un agente con personalidad, valores, intereses y forma de razonar reconstruidos a partir de su huella académica usando modelos psicométricos validados (HEXACO, valores universales de Schwartz).

Esos gemelos alimentan a Mirrorfish, sistema de simulación que permite a la Oficina de Asesores y Rectoría UAT lanzar escenarios y ver cómo reaccionaría la comunidad antes de tomar decisiones institucionales.

## Por qué

Hoy, cuando Rectoría necesita anticipar la reacción de la comunidad académica ante una iniciativa, tiene tres opciones imperfectas: preguntar a un círculo cercano (sesgado), levantar una encuesta (lento), o adivinar (riesgoso). IntellectClone introduce una cuarta: simular contra réplicas digitales construidas con datos públicos.

## Para quién

Uso interno restringido a personal autorizado UAT:

- **Rectoría y Oficina de Asesores** — usuarios estratégicos.
- **Secretarías y direcciones académicas** — usuarios operativos.
- **Investigadores** — pueden validar su propio perfil y solicitar baja.

## Estado del proyecto

En construcción. Versión v1 en desarrollo, con roadmap declarado hasta v1.5.

| Fase | Descripción | Estado |
|---|---|---|
| Diseño | Documentación técnica completa | ✅ Completada |
| Fase A | Cimientos del repo | ⏳ En curso |
| Fase B | Modelo de datos y API base | ⏳ Pendiente |
| Fase C | Cosechadores | ⏳ Pendiente |
| Fase D | Capa de gemelos (perfilador) | ⏳ Pendiente |
| Fase E | UI v1 | ⏳ Pendiente |
| Fase F | Despliegue VPS IONOS | ⏳ Pendiente |
| Fase G | Demo institucional | ⏳ Pendiente |

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Celery + Redis
- **Base de datos:** PostgreSQL 16 con pgvector, pg_trgm, unaccent
- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- **LLMs:** Claude (default), Gemini, OpenAI (configurables)
- **Infraestructura:** Docker Compose, Nginx, Certbot, VPS Linux

## Estructura del repositorio

```
intellectclone/
├── CLAUDE.md                      # Instrucciones maestras para Claude Code
├── README.md                      # Este archivo
├── docs/                          # Documentación técnica completa
│   ├── 01_documento_conceptual.md
│   ├── 02_especificacion_operativa.md
│   ├── 03_modelo_de_datos.md
│   ├── 04_especificaciones_harvesters.md
│   ├── 05_perfilador_y_gemelo.md
│   ├── 06_contrato_exportacion_mirrorfish.md
│   ├── 06bis_ruta_absorcion_mirrorfish_v15.md
│   ├── 07_api_interna.md
│   ├── 08_seleccion_modelos_y_presupuesto.md
│   └── CHANGELOG_alcance_v1.md
├── design/                        # Archivos de Claude Design (HTML/CSS/JSX)
│   ├── prompt_claude_design.md    # Prompt usado para generar el design system
│   └── ...                        # Componentes y pantallas generados
├── sql/                           # Esquema PostgreSQL inicial
│   ├── 001_extensions_and_enums.sql
│   └── 002_tables.sql
├── backend/                       # Código Python (creado en Fase A)
├── frontend/                      # Código Next.js (creado en Fase A)
├── docker-compose.dev.yml         # Stack de desarrollo (creado en Fase A)
├── docker-compose.yml             # Stack de producción (creado en Fase F)
└── scripts/                       # Scripts auxiliares
```

## Filosofía del proyecto

Cinco principios que guían cada decisión:

1. **Fidelidad sobre fluidez** — un gemelo creíble que dice cosas torpes vale más que uno articulado que inventa.
2. **Transparencia radical** — cada respuesta de un gemelo es auditable y trazable a sus fuentes.
3. **Datos públicos por defecto** — solo se cosecha información pública.
4. **Validación humana antes de uso institucional** — gemelos no validados nunca alimentan simulaciones.
5. **Diseño para la transición** — v1 está pensado para evolucionar hacia v1.5 con simulador interno.

## Privacidad y uso institucional

- Sistema de uso interno UAT, no producto público.
- Autenticación obligatoria para todo acceso.
- Logs de auditoría completos sobre acciones sensibles.
- Política de baja: cualquier persona retratada puede solicitar exclusión.

## Cómo arrancar (en desarrollo)

> Estas instrucciones se completarán cuando Fase A esté terminada.

```bash
# Clonar
git clone <repo-url> intellectclone
cd intellectclone

# Instrucciones específicas de levantamiento — pendientes hasta Fase A
```

## Documentación

Toda la documentación técnica está en `docs/`. Léela en orden si llegas nuevo al proyecto:

1. [Documento Conceptual](docs/01_documento_conceptual.md) — qué es, para qué, alcance.
2. [Especificación Operativa](docs/02_especificacion_operativa.md) — stack, plan de fases, convenciones.
3. [Modelo de Datos](docs/03_modelo_de_datos.md) — esquema PostgreSQL.
4. [Especificaciones de Harvesters](docs/04_especificaciones_harvesters.md) — cosecha de fuentes externas.
5. [Perfilador y Gemelo](docs/05_perfilador_y_gemelo.md) — el cerebro del sistema.
6. [Contrato de Exportación a Mirrorfish](docs/06_contrato_exportacion_mirrorfish.md) — integración externa.
7. [Ruta de Absorción de Mirrorfish v1.5](docs/06bis_ruta_absorcion_mirrorfish_v15.md) — roadmap.
8. [API Interna](docs/07_api_interna.md) — endpoints REST de la UI.
9. [Selección de Modelos y Presupuesto](docs/08_seleccion_modelos_y_presupuesto.md) — gestión de LLMs.

## Equipo

- **Fernando** — dueño del producto, arquitecto de decisiones, validador.
- **Claude.ai** — arquitecto de diseño, maquetador, redactor de documentación técnica.
- **Claude Code** — constructor del sistema, ejecutor del plan operativo.

## Licencia

Por definir antes de despliegue público.

---

*IntellectClone — un proyecto institucional de la Universidad Autónoma de Tamaulipas*
