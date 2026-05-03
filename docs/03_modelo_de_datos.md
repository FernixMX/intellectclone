# IntellectClone — Modelo de datos

**Documento técnico 03 — Modelo de datos completo**
**Versión 0.1 — validado contra PostgreSQL 16**
**Audiencia:** Claude Code + revisión humana de Fernando

---

## Cómo está estructurado este documento

Este documento es el plano de la base de datos de IntellectClone. Describe **qué entidades existen**, **qué relaciones tienen entre sí**, y **por qué cada decisión está donde está**. El SQL ejecutable correspondiente está en los archivos `001_extensions_and_enums.sql` y `002_tables.sql`. Si lees este documento sin ejecutar el SQL, entiendes el sistema. Si ejecutas el SQL sin leer el documento, tienes la base pero no sabes por qué.

El esquema fue **validado contra PostgreSQL 16** con las extensiones `pgvector`, `pg_trgm`, `unaccent` y `pgcrypto` activas. Todas las tablas, llaves foráneas, índices y triggers crean correctamente y aceptan datos de prueba realistas.

---

## Filosofía del diseño

Cinco principios guiaron las decisiones de modelado.

**Primero, separar lo cosechado de lo derivado.** Los papers, las personas, las dependencias son cosas que existen en el mundo y simplemente cosechamos. Los gemelos, las simulaciones y las respuestas son cosas que el sistema produce. Cada categoría tiene reglas diferentes de actualización, versionado y permanencia. El esquema refleja esa separación con bloques distintos.

**Segundo, versionar lo que cambia con el tiempo.** Las personas evolucionan: publican papers nuevos, cambian de dependencia, suben de nivel SNII. Los gemelos por lo tanto también evolucionan. La decisión de Fernando de hacer **versionado completo** del gemelo está reflejada en la tabla `gemelo` con un campo `version` y una bandera `es_version_actual`. Cada simulación queda atada a una versión específica del gemelo, lo que permite reproducir exactamente cómo respondió un gemelo en un momento dado, aunque después haya sido actualizado.

**Tercero, modelar las cohortes con el modelo híbrido.** Una simulación guarda **dos cosas a la vez**: los filtros que se aplicaron para construir la cohorte (intención) y la lista exacta de gemelos resueltos en ese momento (snapshot). Esto permite contestar dos preguntas distintas: "¿qué quería simular el usuario?" (filtros) y "¿qué gemelos exactos respondieron?" (lista). Las dos importan; ninguna basta por sí sola.

**Cuarto, pensar en performance desde el primer índice.** Los índices están elegidos para los queries que la UI va a ejecutar realmente: filtrar personas por nivel SNII, buscar gemelos por combinación de rasgos, encontrar coautores de un paper, hacer similitud semántica de perfiles. Hay un índice ivfflat sobre cada columna `vector(1536)` para búsqueda semántica con embeddings.

**Quinto, no temer al JSONB.** PostgreSQL maneja JSONB de forma extraordinariamente eficiente, y hay decisiones donde el costo de normalizar excede el beneficio. Los rasgos HEXACO (con su evidencia y justificación) viven en JSONB porque su estructura puede evolucionar sin migraciones; los niveles desnormalizados también existen como columnas enum para queries rápidos. Es lo mejor de ambos mundos.

---

## Visión general: las 16 tablas

El sistema se organiza en seis bloques temáticos.

**Bloque 1 — Estructura institucional UAT** define el universo organizacional: `dependencia` (facultades, centros, secretarías), `cuerpo_academico` (agrupaciones PRODEP), `area_conocimiento` (taxonomía jerárquica de disciplinas).

**Bloque 2 — Personas y sus relaciones** modela a los miembros de la comunidad UAT: `persona` con todos sus identificadores externos y métricas, `persona_area` con los pesos de expertise, `persona_dependencia_historico` para la evolución de la afiliación.

**Bloque 3 — Producción académica** contiene el conocimiento generado: `paper` para publicaciones indexadas, `coautoria` para la red persona-paper, `documento_corpus` para textos auxiliares (PDFs subidos, CVs, transcripciones).

**Bloque 4 — Gemelos digitales** es el corazón conceptual del sistema: `gemelo` con todas sus versiones (HEXACO + idiolecto + system prompt + score de veracidad + posturas temáticas), `gemelo_corpus_uso` que rastrea con qué textos exactos se construyó cada versión.

**Bloque 5 — Simulación (Mirrorfish UAT)** captura el uso del sistema: `simulacion` con su escenario y cohorte híbrida, `respuesta_simulacion` con el output crudo de cada gemelo más su análisis (postura, intensidad, sentimiento, embedding).

**Bloque 6 — Sistema** contiene la infraestructura operativa: `usuario_sistema` para autenticación y permisos, `cosecha` para registrar cada corrida de los harvesters, `auditoria` para el log de acciones sensibles.

---

## La tabla más crítica: `gemelo`

Esta es la tabla que merece explicación detallada porque es donde la lógica de tu IntellectClone actual en Google AI Studio se traduce a estructura persistente. Toda la sofisticación del cerebro perfilador HEXACO + idiolecto que construiste vive aquí, expandida con linaje y versionado.

**Las seis dimensiones HEXACO** se almacenan de dos formas simultáneas. Como columnas JSONB completas (`rasgo_extraversion`, `rasgo_neuroticismo`, `rasgo_responsabilidad`, `rasgo_amabilidad`, `rasgo_apertura`, `rasgo_honestidad_humildad`) que contienen objeto con `nivel`, `evidencia` (lista de citas textuales) y `justificacion` (prosa). Y como columnas enum desnormalizadas (`nivel_extraversion`, `nivel_neuroticismo`, etc.) que son `'muy_bajo' | 'bajo' | 'medio' | 'alto' | 'muy_alto'` para queries rápidos en filtrado de cohortes.

Esta dualidad es deliberada: el JSONB preserva la riqueza analítica del perfilador (evidencia textual, justificación interpretativa); el enum permite filtrar 700 personas por "alto en apertura y bajo en neuroticismo" en milisegundos sin tocar JSON.

**El idiolecto** es un único campo JSONB con la estructura que ya diseñaste: `longitud_promedio_frase` (numérico), `riqueza_lexica` (0..1), `ngrams_top` (lista), `firma_linguistica` (texto), `modus_operandi` (texto). Sin desnormalizar porque rara vez se filtra por estos.

**Las posturas temáticas** son el campo nuevo más interesante. No existían en tu sistema actual. La estructura propuesta es una lista de objetos: `[{ "tema": "evaluación docente", "postura": "crítica del énfasis en publicaciones", "intensidad": "media", "evidencia": [...] }, ...]`. Esto permitirá en v2 que los gemelos tengan opiniones específicas sobre temas relevantes a la UAT, además de personalidad estable.

**El system prompt** es el texto que se inyecta literalmente al LLM cuando el gemelo participa en una simulación. Se construye a partir de los rasgos + idiolecto + posturas. Es lo que se manda a Claude/Gemini como instrucción cuando se le pide al gemelo que responda algo.

**Los tres scores de calidad** miden cosas distintas y todas importantes:

- `score_veracidad` (de tu sistema actual): qué tan confiable es lo inferido por el perfilador.
- `score_completitud` (nuevo): qué tan completo está el corpus que alimentó al gemelo (un investigador con 3 papers genera un gemelo menos completo que uno con 47).
- `score_consistencia` (nuevo): qué tan internamente coherente es el perfil (señales contradictorias bajan este score).

**El linaje** registra qué modelo se usó (`gemini-2.5-flash`, `claude-opus-4-7`), qué versión del prompt perfilador, cuántos tokens se consumieron, cuánto costó, cuánto tardó. Crítico para tres cosas: control de costos, auditoría reproducible, y mejora del sistema (saber qué configuraciones generan mejores gemelos).

**El versionado** funciona así: cada vez que el corpus de un investigador cambia significativamente o se quiere regenerar el perfil, se inserta una nueva fila con `version = anterior + 1`. La versión anterior queda con `es_version_actual = FALSE` y la nueva con `TRUE`. Un índice parcial garantiza que solo puede haber una versión actual por persona. Las simulaciones referencian un `gemelo_id` específico, no un `persona_id`, así que una simulación de marzo siempre se puede reproducir contra el gemelo exacto que se usó.

**La validación humana** es donde la persona retratada (vía `usuario_sistema.persona_id`) aprueba o solicita correcciones. Solo los gemelos en estado `validado` o `publicado` deberían usarse en simulaciones de alto perfil.

---

## La tabla más subestimada: `gemelo_corpus_uso`

Esta tabla es pequeña y aparentemente trivial, pero hace algo enorme: **registra exactamente qué textos se usaron para construir cada versión del gemelo**. Si el gemelo v3 de la Dra. X se generó con 47 papers + 2 documentos manuales, esta tabla tiene 49 filas que conectan ese gemelo con esos 49 textos. Si dos años después alguien pregunta "¿con qué se construyó este gemelo en marzo de 2026?", la respuesta es exacta y reproducible.

Esto es lo que permite, en última instancia, defender el sistema ante cualquier escrutinio académico o institucional. No es magia: cada gemelo tiene un linaje textual auditable.

---

## Las decisiones que probablemente quieras revisar

Hay cinco decisiones de diseño donde tomé una postura razonable pero válida discutir:

**Una: dimensión de los embeddings.** Usé `vector(1536)` que es la dimensión de `text-embedding-3-small` de OpenAI. Si decides usar un modelo de embeddings diferente (los de Gemini, los de Cohere, los de Voyage), hay que ajustar. La buena noticia: cambiar la dimensión es una migración simple si se hace antes de tener datos masivos.

**Dos: cardinalidad del enum `nivel_rasgo`.** Lo dejé en 5 niveles (`muy_bajo, bajo, medio, alto, muy_alto`). Tu sistema actual usa 3 (`alto, medio, bajo`). Si prefieres mantenerlo en 3 para no inventar precisión que no tienes, lo cambio. Mi argumento para 5: a futuro, cuando incorpores múltiples documentos por persona, podrás distinguir mejor.

**Tres: foreign key con ON DELETE RESTRICT en `respuesta_simulacion`.** Decidí que si alguien intenta borrar un gemelo o una persona que tiene respuestas guardadas en simulaciones, la operación falla. La alternativa sería CASCADE (borrar también las respuestas históricas) o SET NULL (preservar las respuestas pero sin saber a quién pertenecían). Elegí RESTRICT porque las respuestas son evidencia histórica y borrarlas accidentalmente sería catastrófico. La política de baja del sistema debe entonces gestionar esto explícitamente: cuando una persona pide baja, sus simulaciones pasadas se conservan pero su gemelo no se vuelve a usar.

**Cuatro: posturas temáticas como JSONB en `gemelo`.** Lo modelé como un campo dentro de la tabla principal. Una alternativa sería sacarlo a una tabla `postura_tematica` con muchas filas. Mi decisión: cuando hay menos de ~20 posturas por gemelo (que es el caso esperable), JSONB es más simple, más rápido para leer junto con el resto del perfil, y soporta queries con operadores `@>`, `?`, `?|` muy bien. Si en v3 las posturas crecen mucho, se migra.

**Cinco: la tabla `area_conocimiento` como árbol vs. múltiples taxonomías separadas.** La modelé como un solo árbol jerárquico con campo `parent_id` y `sistema_origen` para distinguir si el código viene de CONACYT, OECD, OpenAlex. Una alternativa sería tener tres tablas separadas. Mi decisión: árbol único es más simple para queries de "todas las áreas hijas de X" y los sistemas se distinguen por el campo origen. Si en v2 descubrimos que las taxonomías chocan (un mismo concepto con dos códigos distintos), refactorizamos.

---

## Cómo este modelo conecta con tu sistema actual

Tu IntellectClone en Google AI Studio tiene tres colecciones en Firestore: `perfiles`, `documentos`, `analizar_resultados`. La traducción a IntellectClone v2 es:

| Firestore actual | PostgreSQL v2 | Cambios |
|---|---|---|
| `perfiles` | `persona` + `usuario_sistema.persona_id` (si la persona también es usuario) | Se enriquece con identificadores externos, métricas bibliométricas, conexión a estructura institucional |
| `documentos` | `documento_corpus` (los subidos manualmente) + `paper` (los cosechados) | Se separa lo manual de lo cosechado, con la misma persona pudiendo tener ambos tipos |
| `analizar_resultados` | `gemelo` (versionado) + `gemelo_corpus_uso` (linaje) | Se versiona y se conecta a los textos exactos que lo originaron |

La lógica del perfilador (el prompt HEXACO en `server.ts`) se preserva textualmente en el sistema nuevo. Lo único que cambia es dónde se guarda el resultado y cómo se consulta.

---

## Estimación de tamaño y crecimiento

Para que tengas referencia de magnitud:

- **Personas v1 (investigadores SNII UAT):** ~700 filas. Con métricas, embeddings y todos los campos: ~5 MB.
- **Papers v1 (acumulado UAT estimado):** ~4,000 filas (los 3,771 mencionados en el portal + tesis RIUAT). Con abstracts y embeddings: ~80 MB.
- **Coautorías v1:** ~15,000 filas (multi-autoría es común). ~3 MB.
- **Gemelos v1:** ~700 filas, una versión por persona. Con embeddings: ~5 MB.
- **Simulaciones primer mes de uso:** estimación gruesa 50-100. Con respuestas (~100 por simulación promedio): ~10,000 respuestas, ~100 MB con embeddings.

**Total v1 estimado: ~200 MB.** Cabe holgadamente en el VPS IONOS sin pensar en sharding ni problemas de almacenamiento por años. Cuando v2 incorpore catedráticos sin papers (otros ~3,000) y el corpus crezca, hablamos de single-digit GB. Cuando v4 tenga toda la comunidad y simulaciones intensivas, puede llegar a decenas de GB. Sigue siendo cómodo en un VPS adecuadamente dimensionado.

---

## Lo que falta especificar (queda para documentos siguientes)

Este modelo de datos es completo pero no es todo. Hay piezas que necesitan documentos propios:

- **`04_especificaciones_harvesters.md`** definirá qué cosecha cada fuente y cómo poblar concretamente las tablas `paper`, `persona`, `coautoria`, `cuerpo_academico`. El modelo dice "puede haber muchos papers"; los harvesters dicen "así es como llegan".

- **`05_perfilador_y_gemelo.md`** definirá el pipeline completo de generación del gemelo: cómo se selecciona el corpus, qué prompts exactos se usan en cada paso, cómo se computa el `score_veracidad`, cómo se construye el `system_prompt` operativo. Aquí se rescata íntegramente la lógica del perfilador HEXACO de tu sistema actual.

- **`06_simulador_mirrorfish.md`** definirá cómo se ejecuta una simulación: cómo se construye el prompt del gemelo respondiendo a un escenario, cómo se ejecuta en paralelo con control de concurrencia y rate limits, cómo el agregador analiza las respuestas y produce la síntesis ejecutiva.

- **`07_api_interna.md`** definirá los endpoints REST que exponen este modelo a la UI.

Cada uno se hará en sesiones siguientes contigo.

---

## Cómo se desplegará

Cuando Claude Code arranque la implementación, este esquema se aplica con Alembic (migraciones de SQLAlchemy). El primer migration `0001_initial_schema.py` será generado a partir de los modelos SQLAlchemy correspondientes a estas tablas. Para development local, los archivos `.sql` adjuntos sirven para sembrar rápidamente una base PostgreSQL desde cero sin Alembic.

El orden de ejecución es estricto: `001_extensions_and_enums.sql` primero, `002_tables.sql` después. Si después se agrega `003_seed_data.sql` (datos semilla de áreas de conocimiento, dependencias UAT iniciales), va al final.

---

*Fin del documento de modelo de datos. Versión 0.1 — validada contra PostgreSQL 16. Pendiente de revisión de Fernando.*
