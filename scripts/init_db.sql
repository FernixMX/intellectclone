-- =============================================================================
-- Script de inicialización de la base de datos de desarrollo.
-- Se ejecuta automáticamente al levantar el contenedor por primera vez.
-- Activa las extensiones requeridas por IntellectClone.
-- =============================================================================

-- pgvector: búsqueda semántica con embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm: búsqueda fuzzy de nombres y títulos
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- unaccent: búsqueda sin acentos (Cárdenas → Cardenas)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- pgcrypto: gen_random_uuid() para UUIDs como primary keys
CREATE EXTENSION IF NOT EXISTS pgcrypto;
