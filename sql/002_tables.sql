-- =============================================================================
-- IntellectClone — Esquema PostgreSQL
-- Archivo 002: tablas principales
-- Versión 0.1
-- =============================================================================
-- Crea las 14 tablas del sistema, con sus llaves foráneas, índices y triggers
-- de updated_at automático. Debe ejecutarse DESPUÉS de 001_extensions_and_enums.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Función auxiliar: trigger para mantener updated_at
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- BLOQUE 1: Estructura institucional UAT
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: dependencia
-- Facultades, unidades académicas, centros, secretarías de la UAT
-- -----------------------------------------------------------------------------
CREATE TABLE dependencia (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo          VARCHAR(50) UNIQUE NOT NULL,            -- 'FCAV', 'FIANS', etc.
    nombre          VARCHAR(255) NOT NULL,                  -- 'Facultad de Comercio y Administración Victoria'
    nombre_corto    VARCHAR(100),                           -- 'Comercio Victoria'
    tipo            VARCHAR(50) NOT NULL,                   -- 'facultad' | 'centro' | 'secretaria' | 'instituto' | 'rectoria'
    campus          VARCHAR(100),                           -- 'Victoria' | 'Tampico' | 'Reynosa' | etc.
    sitio_web       VARCHAR(500),
    descripcion     TEXT,
    activa          BOOLEAN NOT NULL DEFAULT TRUE,
    metadatos       JSONB NOT NULL DEFAULT '{}'::jsonb,     -- expansión libre
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dependencia_codigo ON dependencia (codigo);
CREATE INDEX idx_dependencia_campus ON dependencia (campus);
CREATE INDEX idx_dependencia_activa ON dependencia (activa);

CREATE TRIGGER trg_dependencia_updated_at
    BEFORE UPDATE ON dependencia
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- Tabla: cuerpo_academico
-- Cuerpos académicos UAT (consolidado, en consolidación, en formación)
-- -----------------------------------------------------------------------------
CREATE TABLE cuerpo_academico (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo              VARCHAR(50) UNIQUE,                 -- código PRODEP si aplica
    nombre              VARCHAR(500) NOT NULL,
    estatus             VARCHAR(50),                        -- 'consolidado' | 'en_consolidacion' | 'en_formacion'
    dependencia_id      UUID REFERENCES dependencia (id) ON DELETE SET NULL,
    lineas_generacion   TEXT[],                             -- líneas de generación y aplicación del conocimiento
    fecha_registro      DATE,                               -- fecha de registro PRODEP
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    metadatos           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cuerpo_academico_dependencia ON cuerpo_academico (dependencia_id);
CREATE INDEX idx_cuerpo_academico_estatus ON cuerpo_academico (estatus);
CREATE INDEX idx_cuerpo_academico_nombre_trgm ON cuerpo_academico USING gin (nombre gin_trgm_ops);

CREATE TRIGGER trg_cuerpo_academico_updated_at
    BEFORE UPDATE ON cuerpo_academico
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- Tabla: area_conocimiento
-- Taxonomía de áreas de conocimiento (CONACYT/SNII, OECD Fields of Science)
-- -----------------------------------------------------------------------------
CREATE TABLE area_conocimiento (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo          VARCHAR(50) UNIQUE NOT NULL,            -- '1.0', '1.1', '1.1.1' (jerárquico)
    nombre          VARCHAR(255) NOT NULL,
    descripcion     TEXT,
    nivel           SMALLINT NOT NULL,                      -- 1 = área, 2 = subárea, 3 = disciplina
    parent_id       UUID REFERENCES area_conocimiento (id) ON DELETE SET NULL,
    sistema_origen  VARCHAR(50),                            -- 'CONACYT' | 'OECD' | 'OPENALEX'
    metadatos       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_area_conocimiento_parent ON area_conocimiento (parent_id);
CREATE INDEX idx_area_conocimiento_nivel ON area_conocimiento (nivel);
CREATE INDEX idx_area_conocimiento_codigo ON area_conocimiento (codigo);

CREATE TRIGGER trg_area_conocimiento_updated_at
    BEFORE UPDATE ON area_conocimiento
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- BLOQUE 2: Personas y sus relaciones institucionales
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: persona
-- El miembro de la comunidad académica (real, identificable)
-- -----------------------------------------------------------------------------
CREATE TABLE persona (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identidad básica
    nombre_completo         VARCHAR(255) NOT NULL,
    nombre_normalizado      VARCHAR(255) NOT NULL,          -- sin acentos, lowercase, para matching
    primer_nombre           VARCHAR(100),
    apellido_paterno        VARCHAR(100),
    apellido_materno        VARCHAR(100),

    -- Tipo de membresía
    tipo                    tipo_persona NOT NULL DEFAULT 'investigador',

    -- Identificadores externos (para desambiguación cross-fuente)
    orcid                   VARCHAR(19) UNIQUE,             -- '0000-0000-0000-0000'
    openalex_id             VARCHAR(50) UNIQUE,             -- 'A1234567890'
    scopus_id               VARCHAR(50) UNIQUE,
    cvu_conacyt             VARCHAR(20) UNIQUE,             -- CVU del SNII
    google_scholar_id       VARCHAR(50),

    -- Pertenencia institucional (snapshot actual; histórico va en otra tabla)
    dependencia_id          UUID REFERENCES dependencia (id) ON DELETE SET NULL,
    cuerpo_academico_id     UUID REFERENCES cuerpo_academico (id) ON DELETE SET NULL,
    cargo                   VARCHAR(255),                   -- 'Profesor de Tiempo Completo', 'Investigador Titular', etc.

    -- Estatus académico
    nivel_snii              nivel_snii,
    snii_vigente_hasta      DATE,                           -- fecha de vigencia del nivel SNII
    grado_maximo            VARCHAR(100),                   -- 'doctorado', 'maestria', 'licenciatura'
    grado_disciplina        VARCHAR(255),                   -- disciplina del grado más alto

    -- Métricas bibliométricas (recalculadas periódicamente desde papers)
    total_publicaciones     INTEGER NOT NULL DEFAULT 0,
    total_citas             INTEGER NOT NULL DEFAULT 0,
    indice_h                INTEGER NOT NULL DEFAULT 0,
    indice_i10              INTEGER NOT NULL DEFAULT 0,
    primera_publicacion     DATE,
    ultima_publicacion      DATE,

    -- Datos de contacto público
    email_publico           VARCHAR(255),
    sitio_web               VARCHAR(500),

    -- Estado en el sistema IntellectClone
    activa                  BOOLEAN NOT NULL DEFAULT TRUE,  -- false = removida, baja solicitada
    motivo_baja             TEXT,
    fecha_baja              TIMESTAMPTZ,

    -- Trazabilidad de origen
    fuente_principal        tipo_fuente,                    -- de dónde vino la primera vez

    -- Embedding semántico del perfil (para búsqueda y recomendación)
    embedding_perfil        vector(1536),                   -- dimensión OpenAI/text-embedding-3-small

    -- Metadatos extensibles
    metadatos               JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_persona_dependencia ON persona (dependencia_id);
CREATE INDEX idx_persona_cuerpo_academico ON persona (cuerpo_academico_id);
CREATE INDEX idx_persona_tipo ON persona (tipo);
CREATE INDEX idx_persona_nivel_snii ON persona (nivel_snii) WHERE nivel_snii IS NOT NULL;
CREATE INDEX idx_persona_activa ON persona (activa);
CREATE INDEX idx_persona_orcid ON persona (orcid) WHERE orcid IS NOT NULL;
CREATE INDEX idx_persona_openalex ON persona (openalex_id) WHERE openalex_id IS NOT NULL;
CREATE INDEX idx_persona_nombre_trgm ON persona USING gin (nombre_normalizado gin_trgm_ops);
CREATE INDEX idx_persona_embedding ON persona USING ivfflat (embedding_perfil vector_cosine_ops) WITH (lists = 100);

CREATE TRIGGER trg_persona_updated_at
    BEFORE UPDATE ON persona
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- Tabla: persona_area
-- Relación muchos-a-muchos: una persona tiene varias áreas de expertise,
-- con peso (qué tan central es esa área en su trabajo)
-- -----------------------------------------------------------------------------
CREATE TABLE persona_area (
    persona_id          UUID NOT NULL REFERENCES persona (id) ON DELETE CASCADE,
    area_id             UUID NOT NULL REFERENCES area_conocimiento (id) ON DELETE CASCADE,
    peso                NUMERIC(4,3) NOT NULL DEFAULT 1.0,  -- 0..1, qué tan central es para la persona
    fuente              VARCHAR(50),                        -- 'openalex_concepts' | 'snii_declarado' | 'inferido'
    paper_count         INTEGER NOT NULL DEFAULT 0,         -- papers de la persona en esta área
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (persona_id, area_id)
);

CREATE INDEX idx_persona_area_area ON persona_area (area_id);
CREATE INDEX idx_persona_area_peso ON persona_area (peso DESC);

-- =============================================================================
-- BLOQUE 3: Producción académica (papers y corpus)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: paper
-- Cada publicación académica indexada
-- -----------------------------------------------------------------------------
CREATE TABLE paper (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificadores únicos
    doi                     VARCHAR(255) UNIQUE,
    openalex_id             VARCHAR(50) UNIQUE,
    handle_riuat            VARCHAR(100),                   -- handle DSpace si vino de RIUAT

    -- Tipo
    tipo                    tipo_paper NOT NULL DEFAULT 'articulo',

    -- Datos bibliográficos
    titulo                  TEXT NOT NULL,
    titulo_normalizado      TEXT,                           -- para deduplicación
    abstract_texto          TEXT,
    año                     SMALLINT,
    fecha_publicacion       DATE,
    idioma                  VARCHAR(10),

    -- Venue
    revista                 VARCHAR(500),
    issn                    VARCHAR(20),
    editorial               VARCHAR(255),
    volumen                 VARCHAR(20),
    numero                  VARCHAR(20),
    paginas                 VARCHAR(50),

    -- Acceso
    open_access             BOOLEAN,
    url_pdf                 VARCHAR(1000),
    url_landing             VARCHAR(1000),
    license                 VARCHAR(50),

    -- Citaciones
    total_citas             INTEGER NOT NULL DEFAULT 0,
    citas_por_año           JSONB,                          -- {"2023": 12, "2024": 18, ...}

    -- Conceptos OpenAlex (denormalizado para búsqueda rápida)
    conceptos               TEXT[],                         -- ['machine learning', 'deep learning', ...]

    -- Embedding del título + abstract (para similitud semántica)
    embedding_contenido     vector(1536),

    -- Trazabilidad de cosecha
    fuente_origen           tipo_fuente,
    cosecha_id              UUID,                           -- referencia a tabla cosecha (definida más abajo)

    -- Metadatos extensibles (JSON crudo de la fuente, autores como string si no se desambiguaron, etc.)
    metadatos               JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_paper_doi ON paper (doi) WHERE doi IS NOT NULL;
CREATE INDEX idx_paper_openalex ON paper (openalex_id) WHERE openalex_id IS NOT NULL;
CREATE INDEX idx_paper_año ON paper (año);
CREATE INDEX idx_paper_titulo_trgm ON paper USING gin (titulo gin_trgm_ops);
CREATE INDEX idx_paper_conceptos ON paper USING gin (conceptos);
CREATE INDEX idx_paper_embedding ON paper USING ivfflat (embedding_contenido vector_cosine_ops) WITH (lists = 100);

CREATE TRIGGER trg_paper_updated_at
    BEFORE UPDATE ON paper
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- Tabla: coautoria
-- Relación muchos-a-muchos persona ↔ paper, con metadatos de la coautoría
-- -----------------------------------------------------------------------------
CREATE TABLE coautoria (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id              UUID NOT NULL REFERENCES persona (id) ON DELETE CASCADE,
    paper_id                UUID NOT NULL REFERENCES paper (id) ON DELETE CASCADE,

    -- Posición en la lista de autores (1 = primer autor, etc.)
    posicion                SMALLINT,
    total_autores           SMALLINT,                       -- total de autores en el paper

    -- Roles
    es_autor_correspondiente BOOLEAN NOT NULL DEFAULT FALSE,
    es_primer_autor          BOOLEAN NOT NULL DEFAULT FALSE,
    es_ultimo_autor          BOOLEAN NOT NULL DEFAULT FALSE,

    -- Afiliación declarada en ESE paper específico
    afiliacion_declarada    TEXT,                           -- texto crudo de afiliación tal como aparece

    -- Confianza en la asignación (en desambiguación automática)
    confianza_match         NUMERIC(4,3) NOT NULL DEFAULT 1.0,    -- 0..1
    metodo_match            VARCHAR(50),                          -- 'orcid' | 'openalex' | 'manual' | 'fuzzy'

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (persona_id, paper_id)
);

CREATE INDEX idx_coautoria_persona ON coautoria (persona_id);
CREATE INDEX idx_coautoria_paper ON coautoria (paper_id);
CREATE INDEX idx_coautoria_primer_autor ON coautoria (persona_id) WHERE es_primer_autor = TRUE;

-- -----------------------------------------------------------------------------
-- Tabla: documento_corpus
-- Documentos auxiliares que alimentan al perfilador (no son papers indexados)
-- -----------------------------------------------------------------------------
CREATE TABLE documento_corpus (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id              UUID NOT NULL REFERENCES persona (id) ON DELETE CASCADE,
    paper_id                UUID REFERENCES paper (id) ON DELETE SET NULL,  -- si fue extraído de un paper

    titulo                  VARCHAR(500),
    tipo                    tipo_documento_corpus NOT NULL,
    estado                  estado_documento NOT NULL DEFAULT 'pendiente',

    -- Contenido
    texto_extraido          TEXT,                           -- texto plano extraído
    longitud_caracteres     INTEGER,
    longitud_tokens_aprox   INTEGER,

    -- Archivo original (si se subió)
    archivo_path            VARCHAR(1000),                  -- path en filesystem del VPS
    archivo_nombre          VARCHAR(500),
    archivo_mime            VARCHAR(100),
    archivo_tamano_bytes    BIGINT,

    -- Procesamiento
    procesado_at            TIMESTAMPTZ,
    error_procesamiento     TEXT,

    metadatos               JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documento_corpus_persona ON documento_corpus (persona_id);
CREATE INDEX idx_documento_corpus_paper ON documento_corpus (paper_id) WHERE paper_id IS NOT NULL;
CREATE INDEX idx_documento_corpus_estado ON documento_corpus (estado);

CREATE TRIGGER trg_documento_corpus_updated_at
    BEFORE UPDATE ON documento_corpus
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- BLOQUE 4: Gemelos digitales (corazón de IntellectClone)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: gemelo
-- Cada versión del gemelo digital de una persona
-- HEREDA Y EXTIENDE la lógica del perfilador HEXACO + idiolecto del sistema actual
-- -----------------------------------------------------------------------------
CREATE TABLE gemelo (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id                  UUID NOT NULL REFERENCES persona (id) ON DELETE CASCADE,
    version                     INTEGER NOT NULL,                       -- 1, 2, 3...
    es_version_actual           BOOLEAN NOT NULL DEFAULT FALSE,         -- solo una true por persona
    estado                      estado_gemelo NOT NULL DEFAULT 'borrador',

    -- ----- Núcleo HEXACO (las 6 dimensiones del modelo psicométrico) -----
    -- Cada dimensión guarda nivel + evidencia + justificación
    -- Estructura JSONB: { "nivel": "alto", "evidencia": ["cita1", "cita2"], "justificacion": "..." }
    rasgo_extraversion          JSONB,
    rasgo_neuroticismo          JSONB,
    rasgo_responsabilidad       JSONB,
    rasgo_amabilidad            JSONB,
    rasgo_apertura              JSONB,
    rasgo_honestidad_humildad   JSONB,

    -- Niveles desnormalizados para queries rápidos (filtrar por extraversion=alto, etc.)
    nivel_extraversion          nivel_rasgo,
    nivel_neuroticismo          nivel_rasgo,
    nivel_responsabilidad       nivel_rasgo,
    nivel_amabilidad            nivel_rasgo,
    nivel_apertura              nivel_rasgo,
    nivel_honestidad_humildad   nivel_rasgo,

    -- ----- Idiolecto (estilo y firma lingüística) -----
    -- Estructura JSONB: { "longitud_promedio_frase": 24.5, "riqueza_lexica": 0.67,
    --                     "ngrams_top": [...], "firma_linguistica": "...", "modus_operandi": "..." }
    idiolecto                   JSONB,

    -- ----- Posturas temáticas (NUEVO: no existía en sistema actual) -----
    -- Lista de posturas inferidas sobre temas relevantes a la UAT
    -- Estructura: [{ "tema": "...", "postura": "...", "intensidad": "...", "evidencia": [...] }]
    posturas_tematicas          JSONB DEFAULT '[]'::jsonb,

    -- ----- System prompt operativo -----
    -- Texto que se inyecta al LLM cuando el gemelo participa en una simulación
    system_prompt               TEXT NOT NULL,

    -- ----- Score de veracidad y calidad -----
    score_veracidad             NUMERIC(4,3),                           -- 0..1, del perfilador
    score_completitud           NUMERIC(4,3),                           -- 0..1, qué tan completo está el corpus
    score_consistencia          NUMERIC(4,3),                           -- 0..1, qué tan internamente coherente

    -- ----- Linaje de generación -----
    modelo_perfilador           VARCHAR(100),                           -- 'gemini-2.5-flash', 'claude-opus-4-7', etc.
    prompt_perfilador_version   VARCHAR(20),                            -- '0.1', '0.2'
    tokens_consumidos           INTEGER,
    costo_generacion_usd        NUMERIC(10,4),
    duracion_generacion_ms      INTEGER,

    -- ----- Validación humana -----
    validado_por_persona        BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_validacion            TIMESTAMPTZ,
    comentarios_validacion      TEXT,

    -- ----- Embedding del perfil completo (para clustering y similitud) -----
    embedding_gemelo            vector(1536),

    -- ----- Razón de regeneración (si esta versión no es v1) -----
    razon_regeneracion          VARCHAR(255),                           -- 'corpus_actualizado' | 'prompt_mejorado' | 'manual'

    metadatos                   JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (persona_id, version)
);

-- Índice parcial: solo una versión actual por persona
CREATE UNIQUE INDEX idx_gemelo_actual_unico
    ON gemelo (persona_id)
    WHERE es_version_actual = TRUE;

CREATE INDEX idx_gemelo_persona ON gemelo (persona_id);
CREATE INDEX idx_gemelo_estado ON gemelo (estado);
CREATE INDEX idx_gemelo_version_actual ON gemelo (es_version_actual) WHERE es_version_actual = TRUE;
CREATE INDEX idx_gemelo_score_veracidad ON gemelo (score_veracidad DESC NULLS LAST);
CREATE INDEX idx_gemelo_embedding ON gemelo USING ivfflat (embedding_gemelo vector_cosine_ops) WITH (lists = 100);

-- Índices sobre rasgos para filtrado rápido en cohortes
CREATE INDEX idx_gemelo_rasgos_combo ON gemelo
    (nivel_extraversion, nivel_responsabilidad, nivel_apertura)
    WHERE es_version_actual = TRUE;

CREATE TRIGGER trg_gemelo_updated_at
    BEFORE UPDATE ON gemelo
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- Tabla: gemelo_corpus_uso
-- Qué papers y documentos se usaron para generar una versión específica del gemelo
-- (linaje completo: si reproduces el gemelo, sabes con qué textos se hizo)
-- -----------------------------------------------------------------------------
CREATE TABLE gemelo_corpus_uso (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gemelo_id           UUID NOT NULL REFERENCES gemelo (id) ON DELETE CASCADE,
    paper_id            UUID REFERENCES paper (id) ON DELETE SET NULL,
    documento_id        UUID REFERENCES documento_corpus (id) ON DELETE SET NULL,
    longitud_usada      INTEGER,                                -- caracteres efectivamente usados
    posicion_orden      SMALLINT,                               -- orden en el corpus combinado

    CHECK (
        (paper_id IS NOT NULL AND documento_id IS NULL) OR
        (paper_id IS NULL AND documento_id IS NOT NULL)
    )
);

CREATE INDEX idx_gemelo_corpus_uso_gemelo ON gemelo_corpus_uso (gemelo_id);
CREATE INDEX idx_gemelo_corpus_uso_paper ON gemelo_corpus_uso (paper_id) WHERE paper_id IS NOT NULL;
CREATE INDEX idx_gemelo_corpus_uso_documento ON gemelo_corpus_uso (documento_id) WHERE documento_id IS NOT NULL;

-- =============================================================================
-- BLOQUE 5: Simulación (Mirrorfish UAT)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: simulacion
-- Cada escenario lanzado contra una cohorte de gemelos
-- -----------------------------------------------------------------------------
CREATE TABLE simulacion (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Quién y cuándo
    creada_por                  UUID NOT NULL,                  -- referencia a usuario_sistema
    titulo                      VARCHAR(500) NOT NULL,
    descripcion                 TEXT,

    -- El escenario propiamente dicho
    escenario                   TEXT NOT NULL,                  -- la pregunta o situación
    contexto_adicional          TEXT,                           -- contexto opcional para el escenario

    -- Configuración de la simulación
    modelo_simulacion           VARCHAR(100),                   -- 'claude-opus-4-7', 'gemini-2.5-pro', etc.
    temperatura                 NUMERIC(3,2) DEFAULT 0.7,
    max_tokens_respuesta        INTEGER DEFAULT 2000,
    idioma_respuesta            VARCHAR(10) DEFAULT 'es',
    formato_esperado            VARCHAR(50) DEFAULT 'libre',    -- 'libre' | 'estructurado' | 'corto'

    -- ----- Cohorte (modelo HÍBRIDO: filtros + lista resuelta) -----
    -- Filtros aplicados al construir la cohorte
    filtros_cohorte             JSONB NOT NULL,                 -- { "nivel_snii": ["nivel_2", "nivel_3"], "areas": [...], ... }
    -- Lista de gemelo_ids resueltos en el momento de creación (snapshot)
    gemelos_seleccionados       UUID[] NOT NULL,                -- IDs específicos de gemelo (versión incluida)
    total_gemelos               INTEGER NOT NULL,

    -- Estado y métricas
    estado                      estado_simulacion NOT NULL DEFAULT 'borrador',
    progreso_porcentaje         SMALLINT NOT NULL DEFAULT 0,    -- 0..100

    -- Costos (estimados antes, reales después)
    costo_estimado_usd          NUMERIC(10,4),
    costo_real_usd              NUMERIC(10,4),
    tokens_consumidos_total     INTEGER,

    -- Tiempos
    iniciada_at                 TIMESTAMPTZ,
    completada_at               TIMESTAMPTZ,
    duracion_ms                 INTEGER,

    -- Síntesis agregada (resultado del agregador después de recolectar respuestas)
    -- Estructura: { "distribucion_posturas": {...}, "argumentos_principales": [...],
    --               "areas_mayor_disenso": [...], "citas_representativas": [...], ... }
    sintesis                    JSONB,
    sintesis_generada_at        TIMESTAMPTZ,

    -- Resumen ejecutivo en texto plano
    resumen_ejecutivo           TEXT,

    -- Acceso y compartición
    visibilidad                 VARCHAR(20) NOT NULL DEFAULT 'privada', -- 'privada' | 'compartida' | 'institucional'
    compartida_con              UUID[],                         -- otros usuarios autorizados

    error_mensaje               TEXT,

    metadatos                   JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_simulacion_creada_por ON simulacion (creada_por);
CREATE INDEX idx_simulacion_estado ON simulacion (estado);
CREATE INDEX idx_simulacion_created ON simulacion (created_at DESC);

CREATE TRIGGER trg_simulacion_updated_at
    BEFORE UPDATE ON simulacion
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- Tabla: respuesta_simulacion
-- Lo que cada gemelo respondió en una simulación dada
-- -----------------------------------------------------------------------------
CREATE TABLE respuesta_simulacion (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulacion_id               UUID NOT NULL REFERENCES simulacion (id) ON DELETE CASCADE,
    gemelo_id                   UUID NOT NULL REFERENCES gemelo (id) ON DELETE RESTRICT,
    persona_id                  UUID NOT NULL REFERENCES persona (id) ON DELETE RESTRICT,

    -- Respuesta cruda
    respuesta_texto             TEXT NOT NULL,

    -- Análisis de la respuesta (lo llena el agregador)
    postura                     postura_respuesta NOT NULL DEFAULT 'sin_clasificar',
    intensidad                  intensidad_respuesta,
    temas_tocados               TEXT[],                         -- ['evaluación docente', 'autonomía universitaria']
    citas_clave                 TEXT[],                         -- frases textuales relevantes
    sentimiento                 NUMERIC(4,3),                   -- -1..1 (negativo a positivo)

    -- Linaje de la ejecución
    tokens_prompt               INTEGER,
    tokens_completion           INTEGER,
    costo_usd                   NUMERIC(10,5),
    duracion_ms                 INTEGER,
    modelo_usado                VARCHAR(100),

    -- Errores
    error_mensaje               TEXT,

    -- Embedding de la respuesta para clustering y análisis
    embedding_respuesta         vector(1536),

    metadatos                   JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (simulacion_id, gemelo_id)
);

CREATE INDEX idx_respuesta_simulacion ON respuesta_simulacion (simulacion_id);
CREATE INDEX idx_respuesta_gemelo ON respuesta_simulacion (gemelo_id);
CREATE INDEX idx_respuesta_persona ON respuesta_simulacion (persona_id);
CREATE INDEX idx_respuesta_postura ON respuesta_simulacion (simulacion_id, postura);
CREATE INDEX idx_respuesta_embedding ON respuesta_simulacion USING ivfflat (embedding_respuesta vector_cosine_ops) WITH (lists = 100);

-- =============================================================================
-- BLOQUE 6: Sistema (usuarios, fuentes, cosechas, auditoría)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabla: usuario_sistema
-- Usuarios autenticados que pueden lanzar simulaciones, validar perfiles, etc.
-- (NO confundir con persona: usuario_sistema es operador, persona es retratado)
-- -----------------------------------------------------------------------------
CREATE TABLE usuario_sistema (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) UNIQUE NOT NULL,
    nombre              VARCHAR(255) NOT NULL,

    -- Autenticación (en v1, email + password)
    password_hash       VARCHAR(255),                       -- bcrypt
    password_set_at     TIMESTAMPTZ,
    email_verificado    BOOLEAN NOT NULL DEFAULT FALSE,

    -- Rol y permisos
    rol                 rol_usuario NOT NULL DEFAULT 'lectura',

    -- Si el usuario es a la vez una persona retratada (autovalidación)
    persona_id          UUID REFERENCES persona (id) ON DELETE SET NULL,

    -- Restricciones de presupuesto personal
    presupuesto_mensual_usd NUMERIC(10,2),
    consumido_mes_usd       NUMERIC(10,4) NOT NULL DEFAULT 0,

    -- Estado
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_login        TIMESTAMPTZ,

    metadatos           JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usuario_email ON usuario_sistema (email);
CREATE INDEX idx_usuario_rol ON usuario_sistema (rol);
CREATE INDEX idx_usuario_persona ON usuario_sistema (persona_id) WHERE persona_id IS NOT NULL;

CREATE TRIGGER trg_usuario_updated_at
    BEFORE UPDATE ON usuario_sistema
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Foreign key diferida de simulacion.creada_por
ALTER TABLE simulacion
    ADD CONSTRAINT fk_simulacion_creada_por
    FOREIGN KEY (creada_por) REFERENCES usuario_sistema (id) ON DELETE RESTRICT;

-- -----------------------------------------------------------------------------
-- Tabla: cosecha
-- Cada corrida de un harvester (programada o manual)
-- -----------------------------------------------------------------------------
CREATE TABLE cosecha (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fuente              tipo_fuente NOT NULL,
    estado              estado_cosecha NOT NULL DEFAULT 'programada',

    -- Tiempos
    programada_para     TIMESTAMPTZ,
    iniciada_at         TIMESTAMPTZ,
    completada_at       TIMESTAMPTZ,
    duracion_ms         INTEGER,

    -- Resultados
    registros_procesados    INTEGER NOT NULL DEFAULT 0,
    registros_nuevos        INTEGER NOT NULL DEFAULT 0,
    registros_actualizados  INTEGER NOT NULL DEFAULT 0,
    registros_descartados   INTEGER NOT NULL DEFAULT 0,
    errores_count           INTEGER NOT NULL DEFAULT 0,

    -- Configuración de la cosecha (qué se pidió, parámetros)
    configuracion       JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Errores y log
    log_resumen         TEXT,
    errores             JSONB,                              -- lista estructurada de errores

    -- Disparada por
    disparada_por       UUID REFERENCES usuario_sistema (id) ON DELETE SET NULL,
    disparada_manual    BOOLEAN NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cosecha_fuente_estado ON cosecha (fuente, estado);
CREATE INDEX idx_cosecha_created ON cosecha (created_at DESC);

CREATE TRIGGER trg_cosecha_updated_at
    BEFORE UPDATE ON cosecha
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Foreign key diferida de paper.cosecha_id
ALTER TABLE paper
    ADD CONSTRAINT fk_paper_cosecha
    FOREIGN KEY (cosecha_id) REFERENCES cosecha (id) ON DELETE SET NULL;

-- -----------------------------------------------------------------------------
-- Tabla: auditoria
-- Registro de acciones sensibles del sistema
-- -----------------------------------------------------------------------------
CREATE TABLE auditoria (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id          UUID REFERENCES usuario_sistema (id) ON DELETE SET NULL,
    accion              VARCHAR(100) NOT NULL,              -- 'login', 'simulacion_creada', 'gemelo_validado', etc.
    entidad_tipo        VARCHAR(50),                        -- 'simulacion' | 'gemelo' | 'persona' | 'usuario'
    entidad_id          UUID,
    detalle             JSONB,
    ip_origen           INET,
    user_agent          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auditoria_usuario ON auditoria (usuario_id);
CREATE INDEX idx_auditoria_entidad ON auditoria (entidad_tipo, entidad_id);
CREATE INDEX idx_auditoria_created ON auditoria (created_at DESC);
CREATE INDEX idx_auditoria_accion ON auditoria (accion);

-- -----------------------------------------------------------------------------
-- Tabla: persona_dependencia_historico
-- Histórico de afiliaciones (una persona puede haber estado en varias dependencias)
-- -----------------------------------------------------------------------------
CREATE TABLE persona_dependencia_historico (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id          UUID NOT NULL REFERENCES persona (id) ON DELETE CASCADE,
    dependencia_id      UUID REFERENCES dependencia (id) ON DELETE SET NULL,
    cargo               VARCHAR(255),
    fecha_inicio        DATE,
    fecha_fin           DATE,
    es_actual           BOOLEAN NOT NULL DEFAULT FALSE,
    fuente              VARCHAR(50),                        -- de qué fuente vino la inferencia
    confianza           NUMERIC(4,3),
    metadatos           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_persona_dep_hist_persona ON persona_dependencia_historico (persona_id);
CREATE INDEX idx_persona_dep_hist_actual ON persona_dependencia_historico (persona_id, es_actual) WHERE es_actual = TRUE;

-- =============================================================================
-- Fin del archivo 002
-- =============================================================================
