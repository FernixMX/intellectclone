-- =============================================================================
-- IntellectClone — Esquema PostgreSQL
-- Archivo 001: extensiones y tipos enum
-- Versión 0.1
-- =============================================================================
-- Este archivo configura el entorno de la base de datos antes de crear tablas.
-- Debe ejecutarse PRIMERO, contra una base de datos vacía.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Extensiones
-- -----------------------------------------------------------------------------

-- pgvector: búsqueda semántica con embeddings (papers similares, perfiles afines)
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm: búsqueda fuzzy de nombres y títulos
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- unaccent: búsqueda sin acentos (Cárdenas vs Cardenas)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- pgcrypto: para gen_random_uuid() — UUIDs como primary keys
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- Tipos enumerados
-- -----------------------------------------------------------------------------

-- Tipo de persona dentro de la comunidad UAT
CREATE TYPE tipo_persona AS ENUM (
    'investigador',     -- con producción académica indexada
    'docente',          -- profesor sin producción indexada significativa
    'estudiante',       -- estudiante de posgrado con tesis pública
    'directivo',        -- rectoría, secretaría, dirección
    'administrativo',   -- personal no académico
    'externo'           -- coautor externo a la UAT detectado en cosecha
);

-- Estado del proceso de generación del gemelo
CREATE TYPE estado_gemelo AS ENUM (
    'sin_corpus',       -- persona sin papers ni documentos suficientes
    'en_proceso',       -- el perfilador está corriendo
    'borrador',         -- generado, pendiente de validación
    'validado',         -- la persona retratada validó el perfil
    'publicado',        -- visible y usable para simulaciones
    'archivado',        -- versión anterior, reemplazada por una nueva
    'baja_solicitada',  -- la persona pidió ser eliminada
    'error'             -- la generación falló
);

-- Nivel asignado a cada rasgo HEXACO
CREATE TYPE nivel_rasgo AS ENUM (
    'muy_bajo',
    'bajo',
    'medio',
    'alto',
    'muy_alto'
);

-- Nivel SNII (Sistema Nacional de Investigadoras e Investigadores)
CREATE TYPE nivel_snii AS ENUM (
    'candidato',
    'nivel_1',
    'nivel_2',
    'nivel_3',
    'emerito'
);

-- Tipo de documento académico
CREATE TYPE tipo_paper AS ENUM (
    'articulo',         -- artículo en revista
    'capitulo',         -- capítulo de libro
    'libro',            -- libro completo
    'tesis_doctorado',
    'tesis_maestria',
    'tesis_licenciatura',
    'memoria_congreso', -- proceedings
    'reporte_tecnico',
    'preprint',
    'otro'
);

-- Tipo de documento auxiliar de corpus (no es paper indexado)
CREATE TYPE tipo_documento_corpus AS ENUM (
    'pdf_subido',       -- archivo subido manualmente por administrador
    'texto_subido',     -- texto plano subido
    'paper_extraido',   -- texto extraído de un paper cosechado
    'cv_publico',       -- CV público de la persona
    'entrevista',       -- transcripción de entrevista (futuro)
    'otro'
);

-- Estado de procesamiento de un documento
CREATE TYPE estado_documento AS ENUM (
    'pendiente',
    'procesando',
    'procesado',
    'error',
    'descartado'
);

-- Fuente de cosecha
CREATE TYPE tipo_fuente AS ENUM (
    'openalex',
    'vufind_uat',
    'riuat',
    'snii_uat',
    'crossref',
    'orcid',
    'manual'            -- carga manual por administrador
);

-- Estado de una corrida de cosecha
CREATE TYPE estado_cosecha AS ENUM (
    'programada',
    'en_curso',
    'completada',
    'completada_con_errores',
    'fallida',
    'cancelada'
);

-- Estado de una simulación
CREATE TYPE estado_simulacion AS ENUM (
    'borrador',         -- usuario está componiendo
    'en_cola',          -- esperando ejecución
    'en_curso',         -- ejecutándose contra los gemelos
    'agregando',        -- compiló respuestas, agregando síntesis
    'completada',
    'fallida',
    'cancelada'
);

-- Postura asignada a una respuesta de simulación
CREATE TYPE postura_respuesta AS ENUM (
    'a_favor_fuerte',
    'a_favor',
    'matizado',
    'neutral',
    'en_contra',
    'en_contra_fuerte',
    'no_aplica',        -- el gemelo se rehúsa a opinar
    'sin_clasificar'    -- aún no procesado por el agregador
);

-- Intensidad emocional/discursiva de una respuesta
CREATE TYPE intensidad_respuesta AS ENUM (
    'baja',
    'media',
    'alta'
);

-- Rol de un usuario del sistema
CREATE TYPE rol_usuario AS ENUM (
    'admin',            -- administrador técnico del sistema
    'rectoria',         -- Rector y staff directo
    'asesor',           -- Oficina de asesores
    'secretaria',       -- Secretaría académica, investigación, etc.
    'investigador',     -- investigador validando su propio perfil
    'lectura'           -- solo lectura, sin permisos de simulación
);

-- =============================================================================
-- Fin del archivo 001
-- =============================================================================
