# IntellectClone

**Plataforma de gemelos digitales de la comunidad académica de la UAT para simulación institucional**

Documento conceptual — Fase 1
Versión 0.1 — Borrador para revisión
Autor del proyecto: Fernando

---

## 1. Qué es IntellectClone

IntellectClone es una plataforma que crea réplicas digitales (gemelos) de personas reales de la comunidad UAT y permite consultar a esos gemelos como si fueran la propia comunidad. Cada gemelo es un agente con personalidad, intereses, sesgos y forma de razonar reconstruidos a partir de la huella pública del individuo: papers, áreas de investigación, redes de coautoría, dependencia institucional, trayectoria. La plataforma permite después lanzar preguntas o escenarios contra subconjuntos arbitrarios de gemelos y observar cómo reaccionarían, abriendo una herramienta de prospectiva, planeación y comprensión institucional que hoy no existe en ninguna universidad mexicana.

El nombre del producto integra dos ideas: el intelecto colectivo de la universidad (lo que la UAT sabe, piensa y produce a través de su gente) y el clonado fiel de cada individuo como agente computacional. No es un chatbot ni un asistente. Es un laboratorio de simulación social institucional.

---

## 2. Para quién es

IntellectClone tiene varios públicos, en orden de prioridad institucional:

**Rectoría y oficina de asesores** son los usuarios estratégicos. Para ellos la plataforma es una herramienta de toma de decisión: antes de lanzar una iniciativa, anunciar un cambio o responder a una crisis, pueden simular cómo reaccionaría la comunidad y ajustar la estrategia. Es el caso de uso que justifica la inversión.

**Secretarías y direcciones académicas** son los usuarios operativos. La Secretaría Académica, Investigación y Posgrado, las direcciones de facultad, pueden consultar la plataforma para entender redes de colaboración, identificar fortalezas por área, detectar huecos, planear convocatorias internas, alinear acciones al PDI 2024-2028.

**Investigadores y cuerpos académicos** son los usuarios consultivos. Pueden ver su propio perfil, validar que los datos son correctos, descubrir potenciales colaboradores, ubicarse dentro del mapa institucional. La transparencia hacia ellos es lo que hace al proyecto éticamente sostenible.

**Comunidad UAT en general** y **público externo** son audiencia secundaria. Acceso de solo lectura a perfiles y estadísticas agregadas. Esto refuerza la imagen pública de la UAT como universidad innovadora y posiciona al Rector Anaya Alvarado como impulsor de transformación digital institucional, alineado al espíritu del PDI.

---

## 3. Qué problema resuelve

Hoy, cuando Rectoría o la oficina de asesores necesitan anticipar una reacción de la comunidad, tienen tres opciones: preguntarle a un grupo pequeño de personas cercanas (sesgado), levantar una encuesta (lento y caro), o adivinar (riesgoso). Las tres son insuficientes para una universidad de la complejidad de la UAT.

IntellectClone introduce una cuarta opción: simular. No reemplaza el juicio humano ni la consulta real, pero da una primera lectura rápida, granular y segmentable, en horas en lugar de semanas. Permite explorar escenarios "qué pasaría si" antes de comprometerse con uno. Permite ver, antes de actuar, qué partes de la comunidad apoyarían una decisión y cuáles no, y por qué.

Más allá de la simulación, IntellectClone resuelve un problema secundario importante: la UAT no tiene hoy un mapa unificado y navegable de su propia producción intelectual. La información existe pero está fragmentada entre el portal de Producción Científica, el RIUAT, OpenAlex, Scopus, los CVUs de SECIHTI, y archivos internos. IntellectClone consolida todo esto en una sola fuente de verdad consultable por todos.

---

## 4. Alcance v1: prueba de concepto

La versión 1 de IntellectClone tiene un alcance deliberadamente acotado. La estrategia es demostrar que el sistema funciona con una población manejable, usando solo datos públicos, antes de extender a toda la comunidad UAT.

**Universo v1:** investigadores UAT con producción académica pública. Esto incluye principalmente, pero no exclusivamente, a los miembros del SNII vigentes (~500-700 personas según el portal SNII UAT) y a coautores UAT detectables vía OpenAlex aunque no estén en SNII. El número final lo definirá la cosecha real, pero estamos hablando de un universo de cientos, no miles.

**Fuentes v1:** OpenAlex como fuente bibliográfica primaria, VuFind UAT y RIUAT como fuentes locales complementarias, y el portal de Producción Científica UAT como fuente de metadatos institucionales (nivel SNII, cuerpo académico, dependencia). Solo datos públicos.

**Funcionalidades v1:** cosecha automatizada y normalización del acumulado, generación de gemelos digitales para cada investigador, UI pública de consulta de perfiles y exploración de la red de colaboración, simulador básico que permite lanzar una pregunta a un subconjunto de gemelos y obtener respuestas estructuradas.

**Lo que NO incluye v1:** alumnos, catedráticos sin papers, personal administrativo, directivos. No incluye tampoco simulaciones a gran escala ni análisis estadísticos de respuestas. Tampoco autenticación institucional UAT (login con Office 365); v1 usa autenticación propia.

**Criterios de éxito v1:** que Rectoría y la oficina de asesores puedan, desde la UI, lanzar una pregunta a "todos los investigadores UAT del área de ciencias sociales" y obtener un conjunto de respuestas creíbles que reflejen razonablemente la diversidad real de posturas en esa comunidad. Si esto se logra, se justifica la expansión a v2.

---

## 5. Visión de evolución

**v2** extiende el universo a catedráticos sin papers públicos, usando fuentes UAT internas si para entonces se ha conseguido acceso al SIIAA o equivalente. Incorpora también la modelación de cuerpos académicos como entidades compuestas (un cuerpo académico es un agente colectivo que emerge de sus integrantes).

**v3** incorpora alumnos de posgrado, modelados a partir de sus tesis y publicaciones derivadas en RIUAT. Aquí los gemelos son más arquetípicos que individuales por la falta de huella pública abundante.

**v4** completa la comunidad con personal administrativo y directivos, modelados principalmente como arquetipos (rol + dependencia + trayectoria pública), no como individuos profundamente perfilados.

**v5+** abre el simulador a casos de uso avanzados: simulaciones longitudinales (cómo evolucionaría una postura comunitaria a lo largo del tiempo), simulaciones contrafactuales, análisis de impacto de decisiones pasadas, etc.

Esta es la visión de tres a cinco años. La v1 es la palanca para llegar ahí, no el destino.

---

## 6. Principios de diseño

Hay cinco principios que van a guiar todas las decisiones técnicas. No son negociables porque cada uno responde a un riesgo identificado.

**Primero, fidelidad sobre fluidez.** Un gemelo creíble que dice cosas torpes vale más que un gemelo articulado que inventa. Si los datos no alcanzan para representar fielmente a alguien, el gemelo debe negarse a opinar antes que fabricar una opinión.

**Segundo, transparencia radical.** Cada respuesta de un gemelo debe ser auditable. El sistema debe poder responder, para cualquier output, "esto se generó así, con estos datos, usando este prompt, tal día". Sin esto el proyecto pierde legitimidad institucional al primer cuestionamiento.

**Tercero, datos públicos por defecto.** Cosechamos solo lo público. Los datos institucionales internos solo entran si hay autorización explícita y un convenio formal. Esto protege a la institución, a las personas y al proyecto.

**Cuarto, consentimiento del retratado cuando sea posible.** Cualquier persona representada como gemelo debe poder ver su propio perfil, corregirlo y, si lo solicita, salir del sistema. La política de baja debe ser tan fácil como la de alta.

**Quinto, diseño para la transición.** El sistema se construye desde cero pero pensando en que IntellectClone existió antes en Google AI Studio. Toda la lógica del perfilador y del generador de agentes que ya funciona allá debe ser portable, no reescribible. Los prompts, las heurísticas y los esquemas son activos a preservar.

---

## 7. Arquitectura conceptual

El sistema se organiza en cuatro capas que se construyen sobre el VPS Linux IONOS y se comunican por contratos claros.

**Capa de cosecha (harvesters).** Procesos automatizados que corren periódicamente y van a las fuentes externas a traer datos. Hay un harvester por fuente: OpenAlex, VuFind UAT, RIUAT, portal SNII UAT. Cada harvester sabe cómo hablar con su fuente y entrega datos en un formato común. Los harvesters son reemplazables: si mañana queremos cosechar Scopus, agregamos un harvester nuevo sin tocar el resto del sistema.

**Capa de almacenamiento (datos).** Una base de datos relacional consolidada que contiene el acumulado UAT en forma normalizada: personas, dependencias, cuerpos académicos, áreas de conocimiento, papers, coautorías, proyectos. Esta base es la fuente única de verdad. Tanto la UI como IntellectClone leen de aquí.

**Capa de gemelos (IntellectClone propiamente).** Toma a una persona del acumulado y construye su gemelo digital: un perfil estructurado tipo persona ficticia, con personalidad, valores, intereses, sesgos cognitivos, estilo de razonamiento. Este perfil se almacena junto con la persona y se actualiza cuando hay datos nuevos. La capa de gemelos también ofrece una API: "dame el gemelo de la persona X" o "dame todos los gemelos de la facultad Y".

**Capa de simulación (Mirrorfish UAT).** Recibe un escenario o pregunta, selecciona los gemelos del subconjunto pedido por el usuario, lanza el escenario a cada gemelo, recoge las respuestas individuales, las analiza y devuelve tanto las respuestas en bruto como una síntesis agregada (qué tendencias hay, qué disensos, qué consensos).

**Capa de presentación (UI).** Aplicación web que es la cara de la plataforma. Tiene tres secciones principales: directorio (consultar personas, cuerpos académicos, dependencias), explorador (red de colaboración, mapas, estadísticas), simulador (lanzar escenarios y ver resultados). Distintos roles ven distintas secciones.

Las cinco capas se comunican entre sí por interfaces internas claras, lo que permite que cada una se desarrolle, pruebe y reemplace de forma independiente.

---

## 8. Stack tecnológico recomendado

Esta es mi recomendación. La justifico y luego tú decides.

**Sistema operativo del VPS:** Ubuntu 24.04 LTS. Es lo más estándar, mejor documentado y más fácil de encontrar quien lo administre después de ti.

**Lenguaje principal:** Python 3.12. Razones: la mayoría de las librerías de cosecha académica están en Python (pyalex para OpenAlex, sickle para OAI-PMH, scrapy/playwright para scraping), las librerías de LLMs están en Python como ciudadano de primera clase, y FastAPI es uno de los mejores frameworks web modernos. Cualquier persona técnica que herede el proyecto sabe Python.

**Framework web backend:** FastAPI. Moderno, rápido, con documentación automática (Swagger), tipado estricto, async nativo. Perfecto para servir tanto la UI como las APIs internas.

**Base de datos:** PostgreSQL 16. Es la opción más sólida para este caso: soporta JSON nativo (ideal para guardar perfiles de gemelos), tiene búsqueda full-text excelente, escala bien, y permite extensiones como pgvector para cuando metamos embeddings de papers para búsqueda semántica. Gratis y madura.

**Frontend:** Next.js 15 con React. Es el estándar actual para UIs académicas modernas, tiene server-side rendering (clave para SEO de los perfiles de investigador), excelente experiencia de desarrollador, y se despliega trivialmente en el mismo VPS o en Vercel si separamos. Combinado con Tailwind CSS y shadcn/ui da una UI institucional moderna sin tener que diseñar componentes desde cero.

**LLMs:** acceso multi-proveedor. Claude (Anthropic) como modelo primario para razonamiento y generación de gemelos por su calidad y contexto largo, Gemini para tareas de cosecha estructurada por su API gratuita generosa, OpenAI como respaldo. La capa de LLMs debe estar abstraída: cambiar de modelo no debe requerir reescribir el sistema.

**Orquestación de cosecha:** Celery + Redis para tareas asíncronas y programadas. Permite que la cosecha corra en background sin afectar la UI.

**Despliegue:** Docker Compose en el VPS. Cinco contenedores principales (web, worker, db, redis, nginx) que se levantan con un comando. Esto hace el sistema reproducible: si mañana migras a otro servidor, te llevas el docker-compose.yml y listo.

**Reverse proxy y SSL:** Nginx + Certbot (Let's Encrypt) para HTTPS automático.

**Monitoreo básico:** Loki + Grafana para logs y métricas. No es lujo, es necesario cuando esto crezca.

**Backup:** rsync nocturno a almacenamiento externo. Imprescindible para un sistema institucional.

Este stack es deliberadamente conservador. Cada pieza es ampliamente conocida, bien documentada y mantenible por cualquier desarrollador competente. No hay magia ni dependencias exóticas.

---

## 9. Restricciones y riesgos

Vale la pena nombrar de frente lo que puede salir mal o lo que limita el alcance.

**Restricción de datos públicos.** El portal SNII UAT no es trivial de scrapear (ASP.NET con ViewState). El RIUAT tiene OAI-PMH actualmente caído. Esto significa que la cosecha v1 va a depender mucho de OpenAlex y VuFind, que son fuentes externas. Si OpenAlex cambia su política o VuFind cae, perdemos cobertura.

**Riesgo de fidelidad.** Construir un gemelo creíble de un investigador a partir solo de sus papers es un acto interpretativo. El gemelo del Dr. X no es el Dr. X; es una hipótesis razonable de cómo razonaría el Dr. X dado lo que publica. La UI debe comunicar esto claramente. Si alguna vez un usuario confunde la simulación con la realidad, es nuestro fracaso comunicativo.

**Riesgo reputacional.** Si un gemelo dice algo polémico que el investigador real no diría, hay riesgo. Mitigación: cada gemelo debe poder ser revisado por la persona retratada antes de estar disponible públicamente, y debe haber un canal de baja inmediato.

**Riesgo de alcance creciente (scope creep).** "Ya que estamos, agreguemos esto" es la principal amenaza para v1. Cualquier feature nueva propuesta durante v1 se documenta en backlog para v2 y no se implementa.

**Costo de LLMs.** Generar gemelos con Claude para 600 investigadores es costo manejable (estimación gruesa: $20-50 USD por la generación inicial completa). Correr simulaciones masivas sí puede acumular costo. La UI debe mostrar costo estimado antes de lanzar simulaciones grandes y requerir confirmación.

**Dependencia personal.** Hoy este proyecto vive en tu cabeza. Para que IntellectClone tenga vida más allá de ti, hay que documentar bien (este documento es paso uno) y, eventualmente, sumar al menos a una persona técnica más al proyecto. Esto no es problema técnico pero sí es restricción institucional.

---

## 10. Roadmap propuesto

Este es un boceto preliminar. Las fechas son ilusorias hasta que tengamos Fase 2 completa, pero da escala.

**Fase 1 — Definición conceptual.** Ya estamos terminándola. Salida: este documento, validado contigo.

**Fase 2 — Arquitectura detallada y modelo de datos.** Aquí diseñamos cada capa con detalle, definimos el esquema de base de datos, especificamos cada harvester, definimos la estructura del gemelo digital. Salida: documentos técnicos para handoff a Claude Code. Tiempo estimado: 2-3 sesiones contigo en Claude.ai.

**Fase 3 — Construcción de cosechadores y base de datos.** Claude Code construye los harvesters, la base de datos, los procesos de normalización. Salida: acumulado UAT v1 funcionando localmente. Tiempo estimado: 2-4 semanas de trabajo de Claude Code.

**Fase 4 — Construcción de IntellectClone (capa de gemelos).** Migración de la lógica de Google AI Studio a la capa de Python. Construcción del generador de gemelos. Pruebas con investigadores piloto. Salida: gemelos generables a demanda. Tiempo estimado: 3-4 semanas.

**Fase 5 — Construcción del simulador.** Capa de Mirrorfish UAT. Salida: simulación básica funcionando vía API. Tiempo estimado: 2-3 semanas.

**Fase 6 — UI pública.** Frontend Next.js con las tres secciones (directorio, explorador, simulador). Salida: aplicación web desplegada en el VPS IONOS. Tiempo estimado: 4-6 semanas.

**Fase 7 — Despliegue y demo institucional.** Configuración del servidor, despliegue, dominio, SSL, primer demo a Rectoría. Salida: v1 en producción. Tiempo estimado: 2 semanas.

Total estimado para v1 completa: cuatro a seis meses de trabajo, dependiendo del ritmo de iteración con Claude Code y de cuánto tiempo le dediques personalmente.

---

## 11. Próximos pasos inmediatos

Antes de avanzar a Fase 2, necesito dos cosas de tu lado:

Primero, una **validación de este documento**. Léelo con calma, marca lo que no te late, lo que falta, lo que sobra. Especialmente quiero que valides la sección de alcance v1, los principios de diseño y el stack tecnológico. Si algo de eso no te convence, mejor cambiarlo ahora que después.

Segundo, una **muestra de la lógica que ya tienes en Google AI Studio**. No el código completo, sino los prompts que usas para generar agentes y el formato de salida estructurada que ya te funciona. Sin verlo, en Fase 2 voy a estar adivinando cosas que tú ya resolviste. Si me lo compartes (puedes pegarlo aquí o adjuntarlo), la Fase 2 sale mucho mejor.

Con eso entramos a Fase 2: la arquitectura técnica detallada y el modelo de datos del gemelo.

---

*Fin del documento conceptual. Versión 0.1 — pendiente de validación.*
