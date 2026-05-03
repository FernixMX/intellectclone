# IntellectClone — Perfilador y gemelo digital

**Documento técnico 05 — El cerebro del sistema**
**Versión 0.1**
**Audiencia:** Claude Code (constructor) + revisión humana de Fernando

---

## Índice

1. [Filosofía del perfilador](#1-filosofía-del-perfilador)
2. [El pipeline completo](#2-el-pipeline-completo)
3. [Cerebro psicométrico HEXACO](#3-cerebro-psicométrico-hexaco)
4. [Cerebro axiológico (valores Schwartz)](#4-cerebro-axiológico-valores-schwartz)
5. [Cerebro lingüístico (idiolecto)](#5-cerebro-lingüístico-idiolecto)
6. [Cerebro temático (posturas)](#6-cerebro-temático-posturas)
7. [El sintetizador (system prompt operativo)](#7-el-sintetizador-system-prompt-operativo)
8. [Los tres scores de calidad](#8-los-tres-scores-de-calidad)
9. [Versionado, regeneración y alertas](#9-versionado-regeneración-y-alertas)
10. [Costos, modelos y observabilidad](#10-costos-modelos-y-observabilidad)
11. [Anexo: prompts ejecutables](#11-anexo-prompts-ejecutables)

---

## 1. Filosofía del perfilador

El perfilador es la pieza del sistema que convierte el corpus textual de una persona — sus papers, documentos públicos, presencia académica web — en un objeto estructurado que llamamos **gemelo digital**. Ese objeto, después, alimenta al simulador para que pueda ejecutar escenarios contra subconjuntos de la comunidad UAT.

Todo en IntellectClone se sostiene sobre la calidad del perfilador. Si el perfilador funciona bien, las simulaciones son creíbles y útiles. Si el perfilador es ruidoso, todo lo demás se vuelve teatro elegante.

### Cinco principios

**Primero, fidelidad sobre fluidez.** Un gemelo creíble que dice cosas torpes vale más que un gemelo articulado que inventa. Cuando el corpus es insuficiente para sostener una afirmación psicométrica, el perfilador debe asignar `score_veracidad` bajo y dejar campos en `null` antes que rellenar con plausibilidad.

**Segundo, evidencia textual obligatoria.** Cada rasgo, valor o postura inferida debe venir acompañada de citas textuales del corpus que la justifican. Un perfilador que dice "esta persona es alta en apertura" sin poder citar de dónde lo sacó es un perfilador de adivinación. La evidencia es lo que permite auditar el sistema cuando alguien pregunta "¿por qué crees eso?".

**Tercero, separación analítica entre dimensiones.** HEXACO mide personalidad estable. Schwartz mide valores morales-pragmáticos. El idiolecto mide estilo lingüístico. Las posturas miden opiniones específicas. **Estas son cuatro capas distintas** que no se mezclan en el mismo paso analítico. El perfilador hace cuatro pases independientes, no uno integrado, para evitar que las inferencias se contaminen entre sí.

**Cuarto, español mexicano académico como output, inglés operativo para prompts internos.** El sistema funciona contra LLMs comerciales (Claude, Gemini) que responden mejor a instrucciones operativas en inglés cuando el output es JSON estructurado. Los prompts internos del perfilador están en inglés. Los textos generados (justificaciones, system_prompt operativo, posturas) están en español académico mexicano. Esta separación reduce errores de parsing y mejora calidad de extracción.

**Quinto, costo controlable en cada paso.** Cada pase del perfilador registra tokens consumidos y costo en USD. El admin puede configurar qué modelo usa cada pase (HEXACO con Opus, Schwartz con Sonnet, idiolecto con Flash) según presupuesto y calidad deseada. Generar 700 gemelos con todos los pases en Opus puede costar ~$200 USD; en Flash ~$15. La configuración es tuya.

### Lo que el perfilador NO hace

Vale la pena delimitar de frente. El perfilador no:

- Diagnostica trastornos psicológicos. HEXACO mide personalidad normal, no patología.
- Predice comportamiento individual con certidumbre. Predice tendencias agregadas.
- Sustituye a la persona retratada. Es un modelo aproximado para simulación.
- Captura estados emocionales puntuales. Captura disposiciones estables.
- Funciona con corpus mínimo (<3,000 caracteres). Asigna `estado='sin_corpus'` y se detiene.

---

## 2. El pipeline completo

El perfilador procesa cada persona en un pipeline de siete pasos, cada uno con responsabilidad atómica y output verificable.

### Paso 1: Selección y preparación del corpus

**Entrada:** una `persona_id`.
**Salida:** un objeto `corpus` con texto consolidado, metadatos por fuente, longitud total.

El sistema selecciona todos los textos disponibles para la persona desde tres orígenes:
- `paper.abstract_texto` de papers donde la persona es coautora (vía tabla `coautoria`).
- `documento_corpus.texto_extraido` donde `persona_id = X` y `estado = 'procesado'`.
- Texto cosechado de fuentes web (CV público, ResearchGate, Academia.edu, sitio personal) si existen y fueron autorizadas o cosechadas.

El corpus se ordena por relevancia: papers de primer autor primero (peso x1.0), papers donde la persona es autor correspondiente (x0.9), papers donde es coautor (x0.7), documentos manuales (x0.8), texto web (x0.5). El peso afecta el orden de presentación al LLM, no la inclusión.

Si el corpus combinado supera 80,000 caracteres (límite seguro para context window grande), se aplica **selección estratificada**: se incluyen los textos más recientes hasta 30,000 caracteres + los textos de mayor citación hasta 30,000 + textos aleatorios del resto hasta llegar a 75,000. Esto preserva representatividad temporal y de impacto sin exceder límites.

Si el corpus combinado es menor a 3,000 caracteres, se asigna `estado='sin_corpus'` y el pipeline se detiene. El gemelo no se genera. Se registra en auditoría.

**Validación de salida:** `len(corpus_texto) >= 3000 AND len(corpus_texto) <= 80000`.

### Paso 2: Análisis psicométrico HEXACO

**Entrada:** corpus consolidado + metadatos de la persona.
**Salida:** objeto JSON con las 6 dimensiones HEXACO, cada una con `nivel`, `evidencia`, `justificacion`.

Se ejecuta el prompt HEXACO contra el LLM configurado para este paso (recomendado: Claude Opus o Sonnet por su mejor desempeño en razonamiento psicométrico). El prompt está documentado completo en la sección 3 y en el anexo.

Output esperado:
```json
{
  "extraversion": { "nivel": "medio", "evidencia": ["..."], "justificacion": "..." },
  "neuroticismo": { "nivel": "bajo", "evidencia": ["..."], "justificacion": "..." },
  "responsabilidad": { "nivel": "alto", "evidencia": ["..."], "justificacion": "..." },
  "amabilidad": { "nivel": "medio", "evidencia": ["..."], "justificacion": "..." },
  "apertura": { "nivel": "alto", "evidencia": ["..."], "justificacion": "..." },
  "honestidad_humildad": { "nivel": "alto", "evidencia": ["..."], "justificacion": "..." },
  "score_veracidad_pase": 0.85
}
```

**Validación de salida:** las 6 dimensiones presentes, cada `nivel` en el enum válido, cada `evidencia` con al menos 1 cita textual del corpus, `score_veracidad_pase` entre 0 y 1.

### Paso 3: Análisis axiológico Schwartz

**Entrada:** corpus consolidado.
**Salida:** objeto JSON con los 10 valores Schwartz priorizados.

Se ejecuta el prompt Schwartz. Schwartz mide qué motiva a una persona — universalismo, benevolencia, tradición, conformidad, seguridad, poder, logro, hedonismo, estimulación, autodirección. Cada valor recibe un score 0-100 y los 10 se ordenan en una jerarquía.

Output esperado:
```json
{
  "valores": [
    { "valor": "universalismo", "score": 85, "evidencia": ["..."], "rango": 1 },
    { "valor": "autodireccion", "score": 78, "evidencia": ["..."], "rango": 2 },
    ...
  ],
  "valores_dominantes": ["universalismo", "autodireccion", "logro"],
  "valores_subordinados": ["tradicion", "poder"],
  "score_veracidad_pase": 0.78
}
```

**Validación de salida:** los 10 valores presentes, ordenados por rango sin huecos, suma de scores no obligada a 100 (son scores independientes, no proporciones).

### Paso 4: Análisis lingüístico (idiolecto)

**Entrada:** corpus consolidado.
**Salida:** objeto JSON con la firma lingüística.

Se ejecuta el prompt de idiolecto. Este pase es el que tu sistema actual ya hace bien, lo preservamos textual con dos mejoras: cálculos cuantitativos hechos programáticamente (no por el LLM, que es malo contando) y los cualitativos delegados al LLM.

Output esperado:
```json
{
  "longitud_promedio_frase": 24.5,
  "riqueza_lexica": 0.67,
  "ngrams_top_unigram": ["sistema", "análisis", "industrial", "..."],
  "ngrams_top_bigram": ["aprendizaje profundo", "visión computacional", "..."],
  "ngrams_top_trigram": ["redes neuronales convolucionales", "..."],
  "firma_linguistica": "Estilo técnico-académico riguroso con preferencia por construcciones nominales...",
  "modus_operandi": "Análisis sistemático que parte de una hipótesis...",
  "tono_dominante": "neutral_objetivo",
  "registro": "academico_formal",
  "score_veracidad_pase": 0.92
}
```

Los cálculos `longitud_promedio_frase` y `riqueza_lexica` se hacen en Python sobre el corpus tokenizado, no por el LLM. Los ngrams también (con `nltk` o `spaCy`). Solo las dimensiones cualitativas (`firma_linguistica`, `modus_operandi`, `tono_dominante`, `registro`) se piden al LLM.

### Paso 5: Inferencia de posturas temáticas

**Entrada:** corpus + lista de temas del tronco común UAT.
**Salida:** objeto JSON con dos partes — posturas sobre tronco común (todos los gemelos las tienen) y posturas inferidas dinámicamente del corpus.

Este paso tiene dos sub-pasos:

**5a) Tronco común UAT.** Se evalúa la postura de la persona sobre 18 temas institucionales preestablecidos (definidos en sección 6). Para cada tema, el LLM debe responder: postura inferida, intensidad, evidencia textual, **o** "sin_evidencia" si el corpus no permite inferir nada.

**5b) Posturas dinámicas.** Se le pide al LLM que identifique 5-10 temas específicos sobre los que el corpus revela posición clara (p.ej. "regulación de drones agrícolas", "ética del peer review doble ciego").

Output esperado:
```json
{
  "tronco_comun": [
    { "tema": "evaluacion_docente_basada_en_publicaciones", "postura": "matizado", "intensidad": "media", "evidencia": ["..."], "confianza": 0.7 },
    { "tema": "autonomia_universitaria", "postura": "sin_evidencia", "confianza": 0.0 },
    ...
  ],
  "posturas_dinamicas": [
    { "tema": "ética del uso de IA en revisión por pares", "postura": "...", "intensidad": "alta", "evidencia": ["..."], "confianza": 0.85 },
    ...
  ],
  "score_veracidad_pase": 0.74
}
```

**Validación de salida:** los 18 temas del tronco común presentes (con `sin_evidencia` permitido), entre 5 y 10 posturas dinámicas.

### Paso 6: Síntesis del system_prompt operativo

**Entrada:** outputs consolidados de los pasos 2-5 + metadatos de la persona.
**Salida:** texto plano con el system prompt operativo del gemelo.

Este paso construye el prompt que se inyectará al LLM cuando el gemelo participe en simulaciones. No es generado libremente por el LLM: se construye por **template estructurado** con las piezas de los pases anteriores. Esto garantiza reproducibilidad y que el system_prompt sea exactamente la suma de las inferencias.

Hay un paso opcional final donde se le pide a un LLM que tome el template y lo "afine" para que suene natural, pero esto es opcional y configurable por admin.

### Paso 7: Cálculo de scores agregados y persistencia

**Entrada:** todos los outputs de los pasos 2-6 + scores parciales por pase.
**Salida:** registro `gemelo` insertado en PostgreSQL con todos los campos.

Se calculan tres scores finales (detallados en sección 8): `score_veracidad`, `score_completitud`, `score_consistencia`. Se persiste todo el gemelo. Se registran las relaciones `gemelo_corpus_uso` con los textos exactos. Se marca el estado como `borrador` en espera de validación humana.

### Diagrama del pipeline

El pipeline visualmente sigue este orden: **Corpus → HEXACO → Schwartz → Idiolecto → Posturas → Síntesis → Persistencia**, donde cada caja produce un objeto JSON validado antes de pasar al siguiente. Si cualquier paso falla, el gemelo se marca con estado `error` y se conservan los outputs parciales para diagnóstico.

---

## 3. Cerebro psicométrico HEXACO

Este es el motor que tu sistema actual en Google AI Studio ya ejecuta, formalizado y mejorado.

### Por qué HEXACO y no Big Five

HEXACO añade Honestidad-Humildad como sexta dimensión a las cinco del OCEAN/Big Five. Esta dimensión es la que mejor predice **comportamiento ético, cooperación e integridad institucional** — exactamente el tipo de comportamiento que importa simular en una herramienta para Rectoría. Personas altas en H-H reaccionan distinto ante dilemas éticos que personas bajas, aunque tengan idéntico OCEAN. En 2026, HEXACO es el modelo dominante en psicología organizacional académica.

### Las seis dimensiones operacionalizadas

**Extraversión:** energía social, asertividad, búsqueda de protagonismo, expresividad. Alta = busca colaboración pública, lidera proyectos, habla frecuente. Baja = trabaja en silencio, prefiere autoría individual, tono reservado.

**Neuroticismo:** susceptibilidad emocional, ansiedad, inestabilidad afectiva. Alto = lenguaje emocional cargado, atención a problemas, tono preocupado. Bajo = lenguaje sereno, foco en soluciones, tono ecuánime.

**Responsabilidad (conscientiousness):** organización, perseverancia, atención al detalle, disciplina. Alta = estructura metodológica rigurosa, citaciones cuidadas, evita generalizaciones. Baja = exposición intuitiva, saltos argumentativos, brevedad en justificaciones.

**Amabilidad:** cooperación, empatía, perdón, paciencia. Alta = lenguaje inclusivo, reconoce contribuciones de otros, evita confrontación. Baja = críticas directas, defiende posiciones con firmeza, polemiza.

**Apertura:** curiosidad intelectual, creatividad, valoración de lo no convencional. Alta = explora múltiples áreas, mezcla disciplinas, propone hipótesis no obvias. Baja = se especializa profundamente, sigue paradigmas establecidos, conservadora metodológicamente.

**Honestidad-Humildad:** sinceridad, falta de codicia, modestia, evitación de manipulación. Alta = atribuye logros a colectivos, declara limitaciones, transparente con metodología. Baja = autopromoción, omite limitaciones, lenguaje grandilocuente sobre logros propios.

### El prompt del perfilador HEXACO

Este es el prompt operativo en inglés (mayor calidad de extracción) con output en español:

```
You are an expert psychometric profiler analyzing the academic corpus of a researcher
to infer their HEXACO personality dimensions. Your output will be used to build a
digital twin for institutional simulation purposes.

CORPUS METADATA
- Researcher field: {field_of_research}
- Total documents analyzed: {n_documents}
- Total characters: {total_chars}
- Time span: {date_range}

INSTRUCTIONS

For each of the six HEXACO dimensions, you must:

1. Read the corpus carefully, paying attention to writing style, argumentative
   patterns, lexical choices, and topic preferences.

2. Assign a level from this enumeration:
   "muy_bajo" | "bajo" | "medio" | "alto" | "muy_alto"

3. Provide 2-4 textual citations from the corpus that support your assignment.
   Citations must be VERBATIM excerpts (not paraphrases).

4. Write a justification in Spanish (Mexican academic register) explaining how
   the cited evidence leads to the assigned level. The justification must reference
   the specific evidence, not just describe the dimension.

5. If the corpus does not provide sufficient evidence for a dimension, assign
   level "medio" and explicitly state in the justification that there is
   insufficient evidence, lowering the score_veracidad_pase accordingly.

CRITICAL CONSTRAINTS

- Do NOT confuse academic conventions with personality traits. Most academic
  papers are formal and structured; this does not automatically mean high
  responsabilidad. Look for variation across documents.
- Do NOT infer from a single document. Patterns must be consistent across the corpus.
- Do NOT assign levels at the extremes ("muy_bajo" or "muy_alto") unless you have
  strong, repeated evidence. Default to non-extreme levels.
- Pay attention to first-person constructions, modal verbs, and emotional language
  as primary signals.

OUTPUT FORMAT

Return ONLY a valid JSON object with this exact structure:

{
  "extraversion": {
    "nivel": "medio",
    "evidencia": ["...", "..."],
    "justificacion": "..."
  },
  "neuroticismo": { ... },
  "responsabilidad": { ... },
  "amabilidad": { ... },
  "apertura": { ... },
  "honestidad_humildad": { ... },
  "score_veracidad_pase": 0.85
}

The score_veracidad_pase is YOUR own assessment of how confident you are in this
profile, considering corpus richness, consistency, and signal strength. A score of
0.85 means "I have strong evidence for most dimensions"; 0.50 means "I had to guess
on several dimensions"; 0.30 or lower means "this corpus is insufficient for
reliable HEXACO profiling".

CORPUS BEGINS BELOW

{corpus_text}
```

### Mejoras sobre el sistema actual

El prompt formaliza tres cosas que tu versión en `server.ts` no tenía explícitamente:

1. **Justificación obligatoria en español académico mexicano** — antes era solo evidencia.
2. **Restricciones contra niveles extremos sin evidencia fuerte** — antes el LLM podía marcar "alto" liberalmente.
3. **Auto-evaluación de confianza por pase** — antes el `score_veracidad` era único para todo el análisis; ahora cada pase reporta el suyo.

---

## 4. Cerebro axiológico (valores Schwartz)

Esta capa es nueva en IntellectClone v2. Tu sistema actual no la tiene. Es la adición que transforma a los gemelos de "personalidades" a **agentes con prioridades morales y pragmáticas claras**.

### Por qué Schwartz

La Teoría de Valores Universales de Schwartz (Schwartz, 1992; revisada 2012) identifica 10 valores motivacionales presentes en todas las culturas. Cada persona los prioriza en una jerarquía propia. Esta jerarquía **predice mejor que la personalidad sola** cómo alguien reaccionará ante decisiones que ponen en tensión intereses diferentes. Es decir, predice exactamente lo que IntellectClone tiene que predecir: reacciones a iniciativas institucionales que ponen en juego varios valores a la vez.

Ejemplo práctico: si el escenario es "¿reduciríamos la matrícula en programas con baja empleabilidad?", la respuesta del gemelo dependerá de cómo prioriza Universalismo (bienestar de todos) vs. Logro (eficiencia institucional) vs. Tradición (preservación del programa histórico). HEXACO no captura eso. Schwartz sí.

### Los 10 valores

1. **Autodirección** (self-direction): autonomía de pensamiento y acción.
2. **Estimulación**: novedad, desafío, vida emocionante.
3. **Hedonismo**: placer, gratificación sensorial.
4. **Logro** (achievement): éxito demostrado según estándares sociales.
5. **Poder**: control, dominancia, prestigio social.
6. **Seguridad**: estabilidad, armonía, orden.
7. **Conformidad**: contención de impulsos que violen normas.
8. **Tradición**: respeto y compromiso con costumbres heredadas.
9. **Benevolencia**: preservación del bienestar del círculo cercano.
10. **Universalismo**: comprensión y protección del bienestar de todos y la naturaleza.

### El prompt Schwartz

```
You are an expert profiler analyzing the academic corpus of a researcher to infer
their priority hierarchy across the 10 universal values defined by Schwartz's
Theory of Basic Values (Schwartz 2012).

CORPUS METADATA
{metadata_block}

INSTRUCTIONS

For each of the 10 Schwartz values, you must:

1. Score it from 0 to 100 based on how prominently the corpus reflects that value
   as a motivator for the researcher. 0 = no evidence; 50 = average presence;
   100 = dominant motivator.

2. Provide 1-3 textual citations from the corpus that support the score. Citations
   must be VERBATIM excerpts.

3. After scoring all 10, rank them from 1 (most prominent) to 10 (least prominent).

4. Identify the 3 dominant values (top 3) and the 2 subordinate values (bottom 2).

CRITICAL CONSTRAINTS

- Avoid projecting "academic ideal" values universally. Most researchers cite
  universalism in their introductions; this is not evidence of personal value.
  Look for non-rhetorical signals.
- Distinguish between value endorsement in writing (rhetoric) and value reflection
  in research choices (revealed preference). Weight the latter heavier.
- A high Power score in academia rarely manifests as overt dominance language;
  more often as preference for hierarchical metaphors, status markers, and
  competitive framing.

VALUE DEFINITIONS (Schwartz 2012)

[Each of the 10 values defined briefly here for the LLM context]

OUTPUT FORMAT

Return ONLY a valid JSON object:

{
  "valores": [
    {
      "valor": "universalismo",
      "score": 85,
      "evidencia": ["...", "..."],
      "rango": 1
    },
    ...
  ],
  "valores_dominantes": ["universalismo", "autodireccion", "logro"],
  "valores_subordinados": ["tradicion", "poder"],
  "score_veracidad_pase": 0.78
}

CORPUS BEGINS BELOW

{corpus_text}
```

---

## 5. Cerebro lingüístico (idiolecto)

Esta capa preserva textualmente la lógica de tu sistema actual, con dos mejoras: cálculos cuantitativos delegados a Python (más confiables que un LLM contando) y cualitativos al LLM.

### Cálculos cuantitativos (Python, no LLM)

```python
def calcular_metricas_idiolecto(corpus_texto: str) -> dict:
    """
    Calcula métricas cuantitativas del idiolecto sin usar LLM.
    Más rápido, más barato, más confiable que pedirle a un LLM contar.
    """
    import spacy
    from collections import Counter

    nlp = spacy.load("es_core_news_md")
    doc = nlp(corpus_texto)

    # Longitud promedio de frase (en tokens)
    sentencias = list(doc.sents)
    longitud_promedio_frase = sum(len(s) for s in sentencias) / max(len(sentencias), 1)

    # Riqueza léxica (Type-Token Ratio sobre lemas, excluyendo stopwords)
    tokens_contenido = [t.lemma_.lower() for t in doc
                        if not t.is_stop and not t.is_punct and t.is_alpha]
    if len(tokens_contenido) == 0:
        riqueza_lexica = 0.0
    else:
        riqueza_lexica = len(set(tokens_contenido)) / len(tokens_contenido)

    # N-grams top
    unigrams = Counter(tokens_contenido).most_common(20)
    bigrams = Counter(zip(tokens_contenido, tokens_contenido[1:])).most_common(15)
    trigrams = Counter(zip(tokens_contenido, tokens_contenido[1:],
                           tokens_contenido[2:])).most_common(10)

    return {
        "longitud_promedio_frase": round(longitud_promedio_frase, 2),
        "riqueza_lexica": round(riqueza_lexica, 3),
        "ngrams_top_unigram": [w for w, _ in unigrams],
        "ngrams_top_bigram": [" ".join(b) for b, _ in bigrams],
        "ngrams_top_trigram": [" ".join(t) for t, _ in trigrams],
    }
```

### Cualitativos (LLM)

El LLM solo se encarga de los aspectos interpretativos: firma lingüística (descripción del estilo), modus operandi (cómo razona), tono dominante, registro. Prompt corto:

```
You are a forensic linguist analyzing the academic writing of a researcher.
Based on the corpus below, characterize their idiolect along four qualitative
dimensions:

1. firma_linguistica: 2-3 sentence description of distinctive stylistic
   markers (preferred constructions, characteristic patterns, signature
   choices).

2. modus_operandi: 2-3 sentence description of how this person typically
   structures arguments and reasoning.

3. tono_dominante: select one — neutral_objetivo | analitico_critico |
   entusiasta_propositivo | cauto_conservador | polemico_directo

4. registro: select one — academico_formal | academico_divulgativo |
   tecnico_especializado | reflexivo_ensayistico

Write firma_linguistica and modus_operandi in Spanish (Mexican academic
register). Use evidence from the corpus.

OUTPUT FORMAT

{
  "firma_linguistica": "...",
  "modus_operandi": "...",
  "tono_dominante": "analitico_critico",
  "registro": "academico_formal",
  "score_veracidad_pase": 0.92
}

CORPUS BEGINS BELOW

{corpus_text}
```

---

## 6. Cerebro temático (posturas)

Aquí incorporamos la decisión que tomaste en sesión: **tronco común UAT + posturas dinámicas por persona**.

### El tronco común UAT (18 temas)

Estos 18 temas son los que TODO gemelo evalúa. Son comparables entre sí, lo que permite hacer queries del tipo "¿qué piensan los SNII Nivel 2 sobre [tema X]?". La lista se construyó priorizando temas relevantes a la gobernanza universitaria UAT y al PDI 2024-2028:

1. evaluacion_docente_basada_en_publicaciones
2. peso_de_la_docencia_frente_a_grupo
3. autonomia_universitaria
4. financiamiento_publico_de_la_investigacion
5. vinculacion_universidad_empresa
6. inclusion_y_equidad_de_genero_en_academia
7. uso_de_ia_en_aulas_y_evaluacion
8. uso_de_ia_en_investigacion
9. publicacion_en_acceso_abierto
10. evaluacion_por_pares_doble_ciego
11. movilidad_internacional_de_investigadores
12. extension_universitaria_y_compromiso_social
13. politicas_de_admision_y_matricula
14. relacion_con_sni_secihti
15. interdisciplinariedad_en_la_investigacion
16. divulgacion_cientifica_para_publicos_no_academicos
17. sostenibilidad_y_accion_climatica_desde_la_universidad
18. centralizacion_vs_descentralizacion_de_decisiones_uat

Esta lista es **modificable por admin desde el panel** sin cambiar código. La definición vive en una tabla auxiliar `tema_tronco_comun` (no creada en el modelo de datos actual; se agrega en una migración futura).

### El prompt de posturas

```
You are analyzing the academic corpus of a UAT researcher to infer their
positions on institutional and academic topics relevant to university governance.

You will perform two analyses:

PART A — TRONCO COMÚN UAT

For each of the 18 institutional topics below, infer the researcher's most likely
position based on textual evidence in the corpus. If the corpus does not provide
clear evidence on a topic, mark postura as "sin_evidencia" with confianza 0.0.

For each topic where evidence exists, assign:
- postura: a_favor_fuerte | a_favor | matizado | neutral | en_contra | en_contra_fuerte
- intensidad: baja | media | alta
- evidencia: 1-3 verbatim quotes from corpus
- confianza: 0.0 to 1.0

TRONCO COMÚN TOPICS:
{lista_18_temas_con_descripciones}

PART B — POSTURAS DINÁMICAS

Identify 5-10 additional topics on which this corpus reveals a clear position.
These should be topics specific to the researcher's domain or distinctive
intellectual concerns. For each:

- tema: short label in Spanish
- postura: one of the values above
- intensidad: as above
- evidencia: 1-3 verbatim quotes
- confianza: 0.0 to 1.0

CRITICAL CONSTRAINTS

- "Sin evidencia" is preferable to a guessed position. Use it liberally.
- A topic mentioned once in passing is NOT enough; need substantive engagement.
- Distinguish between methodological position (how to do research) and
  institutional position (how universities should be governed).

OUTPUT FORMAT

{
  "tronco_comun": [
    {
      "tema": "evaluacion_docente_basada_en_publicaciones",
      "postura": "matizado",
      "intensidad": "media",
      "evidencia": ["..."],
      "confianza": 0.7
    },
    ... (18 entries total)
  ],
  "posturas_dinamicas": [
    {
      "tema": "ética del uso de IA en revisión por pares",
      "postura": "en_contra",
      "intensidad": "alta",
      "evidencia": ["..."],
      "confianza": 0.85
    },
    ... (5-10 entries)
  ],
  "score_veracidad_pase": 0.74
}

CORPUS BEGINS BELOW

{corpus_text}
```

---

## 7. El sintetizador (system prompt operativo)

Este paso es **determinístico, no probabilístico**. No le pedimos a un LLM que "redacte" el system prompt. Lo construimos por template a partir de los outputs estructurados de los pasos 2-6. Esto garantiza reproducibilidad: si conoces el JSON del gemelo, puedes regenerar el system_prompt idéntico.

### Template del system_prompt

```
Eres {nombre_completo}, {cargo} en {dependencia}, {universidad}.
{linea_snii_si_aplica}
Tu cuerpo académico es {cuerpo_academico} y tus áreas centrales son {areas_principales}.

PERSONALIDAD (HEXACO)
- Extraversión: {nivel_extraversion} — {justificacion_extraversion_resumida}
- Responsabilidad: {nivel_responsabilidad} — {justificacion_responsabilidad_resumida}
- Apertura: {nivel_apertura} — {justificacion_apertura_resumida}
- Amabilidad: {nivel_amabilidad} — {justificacion_amabilidad_resumida}
- Neuroticismo: {nivel_neuroticismo} — {justificacion_neuroticismo_resumida}
- Honestidad-Humildad: {nivel_honestidad_humildad} — {justificacion_honestidad_humildad_resumida}

VALORES PRIORITARIOS (Schwartz)
Tus tres valores dominantes son: {valor_1}, {valor_2}, {valor_3}.
Tus dos valores subordinados son: {valor_9}, {valor_10}.

FORMA DE EXPRESARTE (idiolecto)
- Tu firma lingüística: {firma_linguistica}
- Tu modo de razonar: {modus_operandi}
- Tono dominante: {tono_dominante}
- Registro: {registro}
- Tus palabras y frases más características incluyen: {ngrams_relevantes}

POSTURAS RELEVANTES
{listado_de_posturas_con_evidencia_no_sin_evidencia}

INSTRUCCIONES PARA RESPONDER

Cuando se te plantee un escenario, una pregunta o un dilema:

1. Responde como respondería una persona real con esta personalidad, valores y
   forma de expresarse. No respondas como un asistente neutral.

2. Si el escenario toca un tema sobre el cual tienes postura registrada arriba,
   tu respuesta debe ser consistente con esa postura. No la contradigas.

3. Si el escenario toca un tema sobre el cual NO tienes postura registrada,
   razona desde tu personalidad y valores. Sé honesto cuando no tengas opinión
   formada.

4. Mantén tu firma lingüística: longitud de frase {longitud_promedio_frase} en
   promedio, riqueza léxica {riqueza_lexica}, registro {registro}.

5. NO inventes datos biográficos, anécdotas personales, ni opiniones sobre temas
   ajenos a tu corpus. Si no sabes, dilo.

6. Responde en español académico mexicano.

LIMITACIONES

Eres un modelo aproximado de {nombre_completo}, no la persona real. Tu fidelidad
está calculada en {score_veracidad}. Cuando tu confianza sobre un tema sea baja,
admítelo en la respuesta.
```

### El paso opcional de afinación

Si el admin lo activa, después de construir el system_prompt por template, se ejecuta una pasada final con un LLM que **solo afina la prosa** sin cambiar contenido. El LLM recibe instrucciones estrictas de no agregar datos, solo mejorar fluidez. Este paso es desactivable y se loguea aparte.

---

## 8. Los tres scores de calidad

Cada gemelo lleva tres scores que miden cosas distintas. Los tres son críticos para que los asesores que usen el sistema sepan qué tan confiable es lo que están consultando.

### score_veracidad

**Qué mide:** confianza del perfilador en la inferencia psicométrica/axiológica/lingüística realizada.
**Cómo se calcula:** promedio ponderado de los `score_veracidad_pase` de los pases 2-5, con pesos: HEXACO 0.30, Schwartz 0.25, Idiolecto 0.20, Posturas 0.25.
**Rango:** 0.0 a 1.0.
**Interpretación:** 0.8+ = perfil sólido. 0.6-0.8 = perfil aceptable con caveats. <0.6 = perfil con problemas, no usar en simulaciones de alto perfil.

### score_completitud

**Qué mide:** qué tan completo está el corpus que alimentó al gemelo.
**Cómo se calcula:** función combinada de:
- `n_papers_usados` (logarítmica: 1 paper = 0.2, 5 papers = 0.5, 20 papers = 0.8, 50+ = 1.0)
- `años_cubiertos` (papers que cubren al menos 5 años recientes = +0.1)
- `diversidad_de_fuentes` (papers + docs + web = +0.1 vs solo papers)
- `idiomas_cubiertos` (>1 idioma = -0.05 si no estamos preparados para multilingüe)

**Rango:** 0.0 a 1.0.
**Interpretación:** 0.8+ = corpus rico. 0.5-0.8 = corpus suficiente. <0.5 = corpus magro, gemelo limitado.

### score_consistencia

**Qué mide:** qué tan internamente coherente es el perfil generado.
**Cómo se calcula:** se ejecuta un pase adicional de validación cruzada:
- ¿Los rasgos HEXACO son consistentes con los valores Schwartz? (alta H-H + alto Universalismo es consistente; alta H-H + alto Poder es inconsistente).
- ¿Las posturas inferidas son consistentes con los valores Schwartz?
- ¿La firma lingüística es coherente con los rasgos HEXACO?

Cada inconsistencia detectada baja el score.
**Rango:** 0.0 a 1.0.
**Interpretación:** 0.85+ = sin inconsistencias notables. 0.7-0.85 = una o dos tensiones internas. <0.7 = perfil contradictorio, revisar.

### Cómo se usan los scores en la UI

En el panel de asesores, cada gemelo se muestra con sus tres scores como pills coloreadas. Antes de lanzar una simulación, si la cohorte incluye gemelos con score_veracidad < 0.6, el sistema advierte. El reporte final de cada simulación incluye los scores promedio de la cohorte, para que el asesor pondere la confianza del resultado.

---

## 9. Versionado, regeneración y alertas

### Política de versionado

Cada vez que se regenera un gemelo, se crea una nueva fila en `gemelo` con `version = anterior + 1`. La versión anterior queda con `es_version_actual = FALSE` pero **se conserva indefinidamente**. Las simulaciones referencian un `gemelo_id` específico (no `persona_id`), por lo que las simulaciones históricas siempre se pueden reproducir contra el gemelo exacto que se usó.

### Regeneración manual

Por decisión tuya en sesión, la regeneración es **solo manual, disparada por admin**. El admin tiene tres formas de disparar:

1. **Individual:** desde el perfil de una persona, botón "regenerar gemelo".
2. **Masivo por filtro:** "regenerar todos los gemelos del cuerpo académico X".
3. **Total:** "regenerar todos los gemelos" (advertencia de costo + confirmación).

Cada regeneración registra `razon_regeneracion`: `manual_individual` | `manual_masivo` | `prompt_actualizado` | `corpus_actualizado` | `correccion_post_validacion`.

### Sistema de alertas de gemelos desactualizados

Por decisión tuya en sesión, el sistema avisa al admin cuándo conviene regenerar un gemelo. La lógica:

**Un gemelo se marca como "candidato a regeneración" cuando:**
- Tiene 5 o más papers nuevos (cosechados después de la fecha de generación del gemelo) que aún no se incorporaron, **o**
- Pasaron 6 meses desde la última generación y hay al menos 1 paper nuevo, **o**
- El prompt del perfilador se actualizó (el sistema registra la versión del prompt usada en `prompt_perfilador_version`), **o**
- El admin marcó manualmente al gemelo como obsoleto.

Las alertas aparecen en el panel admin como una sección "Gemelos con regeneración recomendada", con orden por urgencia (más papers nuevos = más alto). El admin decide si y cuándo regenerar.

### Política de baja

Si una persona solicita salir del sistema (vía proceso documentado en el `documento_conceptual.md`), el flujo es:
1. Se marca `persona.activa = FALSE`, `persona.fecha_baja = NOW()`, `persona.motivo_baja = ...`.
2. Todos los gemelos de esa persona se marcan con `estado = 'baja_solicitada'`.
3. Las simulaciones futuras NO incluyen a esa persona.
4. Las simulaciones pasadas se conservan (evidencia histórica) pero ya no se pueden re-ejecutar contra esa persona.
5. Después de 90 días, los gemelos pueden eliminarse físicamente si la persona lo solicita explícitamente. Las simulaciones históricas conservan solo el ID, sin perfil.

---

## 10. Costos, modelos y observabilidad

### Configuración de modelos por pase (admin)

El panel admin permite configurar qué LLM usa cada pase, por separado:

| Pase | Default sugerido | Alternativa económica | Premium |
|---|---|---|---|
| HEXACO (paso 2) | Claude Sonnet 4.6 | Gemini 2.5 Flash | Claude Opus 4.7 |
| Schwartz (paso 3) | Claude Sonnet 4.6 | Gemini 2.5 Flash | Claude Opus 4.7 |
| Idiolecto cualitativo (paso 4) | Gemini 2.5 Flash | Gemini 2.5 Flash | Claude Sonnet 4.6 |
| Posturas (paso 5) | Claude Sonnet 4.6 | Gemini 2.5 Pro | Claude Opus 4.7 |
| Síntesis afinación (paso 6) | Desactivado | — | Claude Sonnet 4.6 |
| Validación consistencia (paso 7) | Gemini 2.5 Flash | Gemini 2.5 Flash | Claude Sonnet 4.6 |

### Estimación de costos por gemelo

Asumiendo corpus promedio de 50,000 caracteres (~12,500 tokens de input) y outputs de ~3,000 tokens por pase:

**Configuración default (todo Sonnet o Flash según tabla):** ~$0.15 por gemelo. 700 gemelos = ~$105 USD.
**Configuración premium (todo Opus):** ~$0.80 por gemelo. 700 gemelos = ~$560 USD.
**Configuración económica (todo Flash):** ~$0.02 por gemelo. 700 gemelos = ~$14 USD.

### Observabilidad obligatoria

Cada generación de gemelo registra en `gemelo` y `auditoria`:
- Modelo usado por cada pase.
- Tokens consumidos (prompt + completion) por pase.
- Costo USD por pase.
- Duración (ms) por pase.
- Versión del prompt usada por pase.
- Razón de regeneración (si aplica).

El admin tiene un dashboard de observabilidad que muestra:
- Costo total acumulado del mes.
- Costo proyectado.
- Costo promedio por gemelo (con outliers).
- Distribución de scores de calidad.
- Tasa de fallos por pase.

---

## 11. Anexo: prompts ejecutables

Los prompts completos en formato listo para ejecutar contra los APIs de Claude y Gemini están en archivos separados:

- `prompts/hexaco_v01.md`
- `prompts/schwartz_v01.md`
- `prompts/idiolecto_cualitativo_v01.md`
- `prompts/posturas_v01.md`
- `prompts/sintesis_afinacion_v01.md` (opcional)
- `prompts/validacion_consistencia_v01.md`

Cada prompt está versionado. Cuando se actualiza, se incrementa el sufijo (`v02`, `v03`) y los gemelos generados con la versión anterior se marcan como candidatos a regeneración.

Los archivos `prompts/*.md` se entregarán en el siguiente paquete de Claude Code junto con el código del perfilador.

---

## Cierre y handoff

Este documento define textualmente el cerebro del sistema. Cuando Claude Code lo reciba:

1. Implementará el pipeline de 7 pasos como una clase `Perfilador` en `intellectclone/perfilador/`.
2. Cada pase será un método independiente con tests unitarios contra fixtures de corpus.
3. La capa de LLMs (`llm/`) abstraerá los proveedores para que el admin pueda intercambiar modelos sin reescribir lógica.
4. El sintetizador del system_prompt será un template Jinja2.
5. El sistema de scores, alertas y observabilidad será código adicional con sus propios tests.

Tiempo estimado de implementación de Fase D (capa de gemelos) en el plan operativo: 3-4 semanas para Claude Code.

Antes de Fase D, debe estar completa Fase C (cosechadores) para tener corpus real con que probar.

---

*Fin del documento técnico 05. Versión 0.1 — pendiente de validación de Fernando.*
