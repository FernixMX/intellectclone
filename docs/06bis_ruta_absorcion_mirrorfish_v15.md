# IntellectClone — Ruta de absorción de Mirrorfish (plan v1.5)

**Documento técnico 06-bis — Plan de fusión del simulador**
**Versión 0.1**
**Audiencia:** Claude Code (constructor) + Fernando (decisiones de roadmap)

---

## Cómo leer este documento

Este documento define el **plan formal** para que IntellectClone absorba al sistema Mirrorfish externo y lo convierta en un módulo interno propio en una versión futura cercana, identificada como **v1.5**.

No es un anexo opcional ni una "puerta abierta". Es plan declarado: v1 se diseña sabiendo que en pocos meses vendrá v1.5 con módulo de simulación interno que reemplaza al Mirrorfish externo. Las decisiones técnicas de v1 deben respetar ese horizonte.

Si el plan se posterga o cancela, no se pierde nada: el v1 sigue funcionando con Mirrorfish externo. Pero diseñar v1 ignorando v1.5 sí sería costoso después.

---

## 1. La decisión declarada

**Cronología:** v1.5 se construye tan pronto como Mirrorfish externo demuestre las funcionalidades que IntellectClone necesita absorber, idealmente en los meses siguientes al lanzamiento de v1.

**Tipo de transición:** reemplazo total. El módulo interno sustituye completamente al Mirrorfish externo. La coexistencia no es objetivo.

**Fuente del módulo interno:** la lógica del Mirrorfish actual (Node/TypeScript con Google AI Studio y Firebase) se migra a Python para vivir dentro del stack de IntellectClone. Los prompts y la lógica de simulación se preservan; el código exacto se reescribe en el lenguaje del sistema.

**Justificación arquitectónica:** un solo sistema integrado es más fácil de mantener, más rápido de operar (sin tráfico API entre componentes), más coherente para los asesores que lo usan, y más defendible institucionalmente como herramienta UAT unificada.

---

## 2. Qué cambia entre v1 y v1.5

### Lo que se mantiene idéntico

- El modelo de datos completo (las 16 tablas).
- El perfilador HEXACO + Schwartz + idiolecto + posturas.
- La cosecha de fuentes externas.
- La UI de directorio, perfiles, validación.
- El sistema de roles, autenticación, auditoría.
- Las tablas `simulacion` y `respuesta_simulacion` que ya viven en el modelo de datos desde v1 (estaban inactivas, en v1.5 se activan).

### Lo que se agrega en v1.5

- Un módulo `simulador/` en Python dentro del backend de IntellectClone.
- Endpoints REST internos `/api/simulaciones/*` para que la UI cree y consulte simulaciones.
- Pantallas de UI de simulador (composición de escenario, resultado, histórico).
- Lógica de orquestación: ejecución paralela de gemelos, agregador de respuestas, generación de síntesis ejecutiva.

### Lo que se quita en v1.5

- La API de exportación de gemelos pública (`/export/v1/*`) **se deprecia pero NO se elimina inmediatamente**. Razón: durante un período de transición de algunos meses, ambos modos pueden coexistir mientras se migra. Después del período de gracia, se elimina.
- Los tokens de exportación se invalidan al final del período de gracia.
- Mirrorfish externo se desactiva. Su servidor o instancia se apaga (esto es decisión tuya operativa, no técnica).

### Lo que NO cambia para los usuarios

Los asesores que usen IntellectClone en v1.5 no perciben ruptura: las simulaciones siguen funcionando, los gemelos son los mismos, los resultados son comparables. Lo único que perciben es que ahora todo vive en un solo lugar y la UI tiene secciones nuevas de simulador integrado en lugar de "exportar a Mirrorfish".

---

## 3. Decisiones de v1 que ya consideran v1.5

Estas son las decisiones específicas que tomamos en el diseño de v1 **sabiendo** que viene v1.5. Documentarlas aquí permite que Claude Code las respete sin tener que adivinar las razones.

### Decisión 1: las tablas `simulacion` y `respuesta_simulacion` quedan en el modelo de datos de v1

Aunque v1 no las usa (no hay simulador interno), las tablas existen en el esquema PostgreSQL desde el día uno. En v1.5 se activan sin migración.

**Implicación para Claude Code:** no eliminar estas tablas del SQL inicial. Construir su esqueleto de modelo SQLAlchemy, aunque no haya endpoints que las usen en v1.

### Decisión 2: el perfilador genera ya el `system_prompt` operativo completo

Este es el campo que el simulador (externo o interno) inyecta al LLM cuando un gemelo participa en simulación. En v1 lo consume Mirrorfish externo vía API; en v1.5 lo consume el módulo interno directo de la base de datos.

**Implicación para Claude Code:** la lógica de generación del `system_prompt` debe estar bien hecha desde v1. No tomar atajos.

### Decisión 3: la abstracción de LLMs vive en una capa propia desde v1

Tanto el perfilador (v1) como el simulador (v1.5) usarán LLMs. Si la capa de abstracción (`llm/`) está bien diseñada en v1, el simulador en v1.5 la reutiliza sin escribir cliente nuevo.

**Implicación para Claude Code:** cuando construya la capa `llm/` en v1, diseñarla pensando que múltiples consumidores la van a usar (perfilador, simulador, agregador). No hardcodear nada al perfilador.

### Decisión 4: el JSON exportado en v1 es la "interfaz interna" del gemelo en v1.5

El esquema JSON definido en `06_contrato_exportacion_mirrorfish.md` no es solo un contrato externo: es **la representación canónica del gemelo** que usará tanto la API de exportación (v1) como el módulo de simulación interno (v1.5). En v1.5 el módulo lee la base directo y construye este mismo objeto en memoria antes de pasarlo al LLM.

**Implicación para Claude Code:** la función `serialize_gemelo_to_json(gemelo_db)` que se construya para la API de exportación debe ser reutilizable. El simulador interno la llamará también.

### Decisión 5: las tablas `export_token` y la lógica de tokens son v1-only, no se planean para v1.5

Cuando Mirrorfish viva adentro, no hay tokens entre componentes. Los tokens son de la era de exportación.

**Implicación para Claude Code:** la tabla `export_token` y su lógica son código "desechable" en v1.5. No invertir tiempo excesivo en hacerla sofisticada (rotación automática, scopes complejos, etc.). Lo mínimo viable que garantice seguridad en v1, sabiendo que se va.

---

## 4. La migración del código actual de Mirrorfish

### Inventario de lo que hay que migrar

Por lo que vi en `server.ts` y los demás archivos, el Mirrorfish actual tiene estas piezas funcionales:

**Pieza 1: el flujo de creación de "agente" (ya existente en tu IntellectClone actual).** Esto NO se migra en v1.5 porque el perfilador de IntellectClone v1 ya lo reemplaza con HEXACO + Schwartz + idiolecto + posturas, mejor que el sistema actual.

**Pieza 2: la lógica de simulación contra escenarios.** Esto SÍ es lo que se migra. Los archivos críticos a inventariar antes de v1.5:
- El prompt o conjunto de prompts que tomas un agente (system_prompt) + un escenario y produces una respuesta.
- La lógica de orquestación si es que ejecuta múltiples agentes en paralelo.
- La lógica de agregación si es que consolida respuestas en una síntesis.
- Cualquier heurística específica que hayas calibrado con uso real.

**Pieza 3: la UI actual de Mirrorfish.** Esta probablemente NO se migra tal cual, porque IntellectClone v1.5 tendrá su propia UI integrada con el design system "Quirúrgico" ya definido. Las pantallas se rediseñan, lo único que sobrevive es el flujo lógico (qué hace cada pantalla).

### Plan de migración

Cuando llegue el momento de v1.5, el plan es:

**Paso 1: Auditoría de Mirrorfish actual.** Tú o un asistente revisan el código actual y catalogan: prompts usados, parámetros calibrados, tipos de salida, edge cases manejados. Esto se documenta en un archivo `mirrorfish_inventario.md`.

**Paso 2: Diseño del módulo `simulador/` en Python.** Se redacta un documento técnico (sería `08_simulador_interno.md` cuando llegue ese momento) que define la estructura del módulo: clases, interfaces, prompts, lógica de orquestación. Equivalente a lo que hicimos con el perfilador en `05_perfilador_y_gemelo.md`.

**Paso 3: Implementación.** Claude Code construye el módulo siguiendo el documento. Tiempo estimado: 2-3 semanas.

**Paso 4: Pruebas en paralelo.** Durante un periodo, el módulo interno y Mirrorfish externo coexisten. Se ejecutan los mismos escenarios contra ambos y se comparan resultados para validar que el módulo interno produce simulaciones equivalentes o mejores.

**Paso 5: Switch.** Cuando el módulo interno tenga paridad o supere a Mirrorfish externo, se hace el cambio: la UI de IntellectClone activa las pantallas de simulador interno, los asesores usan eso, Mirrorfish externo se desactiva.

**Paso 6: Cleanup.** Después del período de gracia (sugerido: 30 días tras el switch), la API de exportación se elimina, los tokens se revocan, el código de exportación se borra del repositorio.

---

## 5. Riesgos y mitigación

### Riesgo: el plan de v1.5 nunca se ejecuta

**Probabilidad:** media. Los planes de "lo hacemos pronto" en tecnología institucional con frecuencia se postergan indefinidamente.

**Mitigación:** las decisiones de v1 que considera v1.5 (sección 3) **no son costos hundidos** si v1.5 nunca llega. Las tablas inactivas no estorban, la abstracción de LLMs es buena práctica per se, el `system_prompt` bien hecho es valioso para Mirrorfish externo también. Es decir: si v1.5 llega, el sistema está listo; si no llega, no perdimos nada.

### Riesgo: Mirrorfish externo tiene funcionalidad que el módulo interno no replica

**Probabilidad:** baja, dado que Mirrorfish actual es funcionalmente compacto.

**Mitigación:** el paso 4 del plan (pruebas en paralelo) detecta gaps antes del switch. Si hay funcionalidad faltante, se construye antes de hacer el switch. No se hace cutover hasta paridad confirmada.

### Riesgo: el código actual de Mirrorfish encripta lógica difícil de migrar

**Probabilidad:** baja. El cerebro de Mirrorfish son los prompts (texto portable) y orquestación (estándar). El código exacto importa poco.

**Mitigación:** la migración no es port literal de código sino reescritura de la lógica con prompts preservados. Esto es más fácil que migrar código.

### Riesgo: la API de exportación queda como deuda técnica si v1.5 se posterga

**Probabilidad:** alta si v1.5 se retrasa más de 12 meses.

**Mitigación:** la API de exportación es código relativamente pequeño y bien definido (5 endpoints, esquema fijo, autenticación simple). Mantenerla 12-18 meses no es deuda significativa. Si v1.5 nunca llega, simplemente se queda como funcionalidad permanente y ya.

---

## 6. Cronograma indicativo

Esto es indicativo, no comprometedor. Las fechas dependen de cómo evolucione v1.

**Ahora — Mes 0:** terminando documentación y arrancando construcción de v1.

**Meses 1-3:** construcción de v1 (Fases A-G del plan operativo).

**Mes 4:** despliegue de v1 a producción en VPS IONOS, demo a Rectoría.

**Meses 5-6:** v1 en uso real por asesores y Rectoría con Mirrorfish externo. Recolección de feedback. Identificación de gaps.

**Mes 6 o 7:** decisión formal de iniciar v1.5. Auditoría de Mirrorfish actual. Documentación del módulo de simulador interno.

**Meses 7-9:** construcción de v1.5 (módulo simulador interno + UI de simulación).

**Meses 9-10:** pruebas en paralelo, calibración, comparación contra Mirrorfish externo.

**Mes 10 o 11:** switch. Mirrorfish externo se desactiva. v1.5 en producción.

**Mes 11+:** período de gracia. Eventual eliminación de API de exportación.

Total: aproximadamente un año desde el lanzamiento de v1 hasta el switch a v1.5.

---

## 7. Decisiones que se posponen a v1.5

Hay decisiones que no podemos tomar ahora porque dependen de cómo evolucione el uso. Quedan documentadas como pendientes:

- **¿El módulo interno hace simulaciones en streaming o en batch?** Streaming permite ver respuestas conforme se generan. Batch es más simple. Decidir cuando llegue v1.5 según UX deseada.

- **¿El módulo interno permite simulaciones longitudinales** (varios turnos de conversación con un gemelo)? Mirrorfish actual probablemente sea single-turn. v1.5 podría agregar multi-turn. Decidir según necesidad.

- **¿Hay caché de simulaciones idénticas?** Si dos asesores lanzan el mismo escenario contra la misma cohorte, ¿se reaprovecha? Decisión de optimización, no de arquitectura.

- **¿El módulo interno expone su propia API de exportación de simulaciones a otros sistemas?** Posibilidad para v2 o v3, no para v1.5.

---

## 8. Mensaje a Claude Code

Si estás leyendo esto al construir v1, ten estos cinco principios presentes:

**Uno.** Las tablas `simulacion` y `respuesta_simulacion` deben crearse aunque v1 no las use. Los modelos SQLAlchemy también. No las omitas.

**Dos.** La función que serializa un gemelo a JSON (para la API de exportación) debe ser reutilizable, no acoplada al endpoint REST. En v1.5 la usará también el módulo interno.

**Tres.** La capa `llm/` debe diseñarse para múltiples consumidores. El perfilador es uno; el simulador interno será otro. No hardcodes asunciones del perfilador en la abstracción.

**Cuatro.** El `system_prompt` operativo del gemelo es interfaz crítica. Trátalo con el rigor de una API pública: una vez que se establece, los cambios son breaking.

**Cinco.** No sobre-inviertas en la API de exportación. Es código transitorio. Hazla bien (segura, observable, con tests) pero no la conviertas en producto en sí mismo. Su misión es servir 6-12 meses y desaparecer.

---

## 9. Cierre

IntellectClone v1 se construye con visión de v1.5. La decisión de absorber Mirrorfish está declarada, no es contingente. El sistema es coherente: cosechar y perfilar en v1, agregar simulación interna en v1.5, terminar como una sola plataforma institucional UAT integrada.

El paso intermedio (v1 con Mirrorfish externo) no es un workaround; es la ruta más ordenada para llegar al sistema completo sin construirlo todo de golpe.

---

*Fin del documento técnico 06-bis. Versión 0.1 — pendiente de validación de Fernando.*
