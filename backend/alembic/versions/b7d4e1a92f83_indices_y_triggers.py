"""indices_y_triggers

Agrega todos los índices de rendimiento y los triggers de updated_at
que no puede generar Alembic autogenerado (GIN, ivfflat, parciales,
compuestos con WHERE, función PL/pgSQL).

Revision ID: b7d4e1a92f83
Revises: 2f108123e640
Create Date: 2026-05-04 12:00:00.000000

"""

from alembic import op

revision: str = "b7d4e1a92f83"
down_revision: str | None = "2f108123e640"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Función auxiliar de trigger para updated_at
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =========================================================================
    # ÍNDICES — dependencia
    # =========================================================================
    op.execute("CREATE INDEX idx_dependencia_codigo ON dependencia (codigo)")
    op.execute("CREATE INDEX idx_dependencia_campus ON dependencia (campus)")
    op.execute("CREATE INDEX idx_dependencia_activa ON dependencia (activa)")

    op.execute("""
        CREATE TRIGGER trg_dependencia_updated_at
            BEFORE UPDATE ON dependencia
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — cuerpo_academico
    # =========================================================================
    op.execute("CREATE INDEX idx_cuerpo_academico_dependencia ON cuerpo_academico (dependencia_id)")
    op.execute("CREATE INDEX idx_cuerpo_academico_estatus ON cuerpo_academico (estatus)")
    op.execute(
        "CREATE INDEX idx_cuerpo_academico_nombre_trgm"
        " ON cuerpo_academico USING gin (nombre gin_trgm_ops)"
    )

    op.execute("""
        CREATE TRIGGER trg_cuerpo_academico_updated_at
            BEFORE UPDATE ON cuerpo_academico
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — area_conocimiento
    # =========================================================================
    op.execute("CREATE INDEX idx_area_conocimiento_parent ON area_conocimiento (parent_id)")
    op.execute("CREATE INDEX idx_area_conocimiento_nivel ON area_conocimiento (nivel)")
    op.execute("CREATE INDEX idx_area_conocimiento_codigo ON area_conocimiento (codigo)")

    op.execute("""
        CREATE TRIGGER trg_area_conocimiento_updated_at
            BEFORE UPDATE ON area_conocimiento
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — persona
    # =========================================================================
    op.execute("CREATE INDEX idx_persona_dependencia ON persona (dependencia_id)")
    op.execute("CREATE INDEX idx_persona_cuerpo_academico ON persona (cuerpo_academico_id)")
    op.execute("CREATE INDEX idx_persona_tipo ON persona (tipo)")
    op.execute(
        "CREATE INDEX idx_persona_nivel_snii ON persona (nivel_snii) WHERE nivel_snii IS NOT NULL"
    )
    op.execute("CREATE INDEX idx_persona_activa ON persona (activa)")
    op.execute("CREATE INDEX idx_persona_orcid ON persona (orcid) WHERE orcid IS NOT NULL")
    op.execute(
        "CREATE INDEX idx_persona_openalex ON persona (openalex_id) WHERE openalex_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_persona_nombre_trgm"
        " ON persona USING gin (nombre_normalizado gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX idx_persona_embedding"
        " ON persona USING ivfflat (embedding_perfil vector_cosine_ops)"
        " WITH (lists = 100)"
    )

    op.execute("""
        CREATE TRIGGER trg_persona_updated_at
            BEFORE UPDATE ON persona
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — persona_area
    # =========================================================================
    op.execute("CREATE INDEX idx_persona_area_area ON persona_area (area_id)")
    op.execute("CREATE INDEX idx_persona_area_peso ON persona_area (peso DESC)")

    # =========================================================================
    # ÍNDICES — paper
    # =========================================================================
    op.execute("CREATE INDEX idx_paper_doi ON paper (doi) WHERE doi IS NOT NULL")
    op.execute(
        "CREATE INDEX idx_paper_openalex ON paper (openalex_id) WHERE openalex_id IS NOT NULL"
    )
    op.execute("CREATE INDEX idx_paper_año ON paper (año)")
    op.execute("CREATE INDEX idx_paper_titulo_trgm ON paper USING gin (titulo gin_trgm_ops)")
    op.execute("CREATE INDEX idx_paper_conceptos ON paper USING gin (conceptos)")
    op.execute(
        "CREATE INDEX idx_paper_embedding"
        " ON paper USING ivfflat (embedding_contenido vector_cosine_ops)"
        " WITH (lists = 100)"
    )

    op.execute("""
        CREATE TRIGGER trg_paper_updated_at
            BEFORE UPDATE ON paper
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — coautoria
    # =========================================================================
    op.execute("CREATE INDEX idx_coautoria_persona ON coautoria (persona_id)")
    op.execute("CREATE INDEX idx_coautoria_paper ON coautoria (paper_id)")
    op.execute(
        "CREATE INDEX idx_coautoria_primer_autor ON coautoria (persona_id)"
        " WHERE es_primer_autor = TRUE"
    )

    # =========================================================================
    # ÍNDICES — documento_corpus
    # =========================================================================
    op.execute("CREATE INDEX idx_documento_corpus_persona ON documento_corpus (persona_id)")
    op.execute(
        "CREATE INDEX idx_documento_corpus_paper ON documento_corpus (paper_id)"
        " WHERE paper_id IS NOT NULL"
    )
    op.execute("CREATE INDEX idx_documento_corpus_estado ON documento_corpus (estado)")

    op.execute("""
        CREATE TRIGGER trg_documento_corpus_updated_at
            BEFORE UPDATE ON documento_corpus
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — gemelo
    # =========================================================================
    # Índice parcial único: garantiza que solo haya una versión actual por persona
    op.execute(
        "CREATE UNIQUE INDEX idx_gemelo_actual_unico"
        " ON gemelo (persona_id)"
        " WHERE es_version_actual = TRUE"
    )
    op.execute("CREATE INDEX idx_gemelo_persona ON gemelo (persona_id)")
    op.execute("CREATE INDEX idx_gemelo_estado ON gemelo (estado)")
    op.execute(
        "CREATE INDEX idx_gemelo_version_actual ON gemelo (es_version_actual)"
        " WHERE es_version_actual = TRUE"
    )
    op.execute(
        "CREATE INDEX idx_gemelo_score_veracidad ON gemelo (score_veracidad DESC NULLS LAST)"
    )
    op.execute(
        "CREATE INDEX idx_gemelo_embedding"
        " ON gemelo USING ivfflat (embedding_gemelo vector_cosine_ops)"
        " WITH (lists = 100)"
    )
    # Índice compuesto para filtrado rápido de cohortes por rasgos HEXACO
    op.execute(
        "CREATE INDEX idx_gemelo_rasgos_combo"
        " ON gemelo (nivel_extraversion, nivel_responsabilidad, nivel_apertura)"
        " WHERE es_version_actual = TRUE"
    )

    op.execute("""
        CREATE TRIGGER trg_gemelo_updated_at
            BEFORE UPDATE ON gemelo
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — gemelo_corpus_uso
    # =========================================================================
    op.execute("CREATE INDEX idx_gemelo_corpus_uso_gemelo ON gemelo_corpus_uso (gemelo_id)")
    op.execute(
        "CREATE INDEX idx_gemelo_corpus_uso_paper ON gemelo_corpus_uso (paper_id)"
        " WHERE paper_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX idx_gemelo_corpus_uso_documento ON gemelo_corpus_uso (documento_id)"
        " WHERE documento_id IS NOT NULL"
    )

    # =========================================================================
    # ÍNDICES — simulacion
    # =========================================================================
    op.execute("CREATE INDEX idx_simulacion_creada_por ON simulacion (creada_por)")
    op.execute("CREATE INDEX idx_simulacion_estado ON simulacion (estado)")
    op.execute("CREATE INDEX idx_simulacion_created ON simulacion (created_at DESC)")

    op.execute("""
        CREATE TRIGGER trg_simulacion_updated_at
            BEFORE UPDATE ON simulacion
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — respuesta_simulacion
    # =========================================================================
    op.execute("CREATE INDEX idx_respuesta_simulacion ON respuesta_simulacion (simulacion_id)")
    op.execute("CREATE INDEX idx_respuesta_gemelo ON respuesta_simulacion (gemelo_id)")
    op.execute("CREATE INDEX idx_respuesta_persona ON respuesta_simulacion (persona_id)")
    op.execute(
        "CREATE INDEX idx_respuesta_postura ON respuesta_simulacion (simulacion_id, postura)"
    )
    op.execute(
        "CREATE INDEX idx_respuesta_embedding"
        " ON respuesta_simulacion"
        " USING ivfflat (embedding_respuesta vector_cosine_ops)"
        " WITH (lists = 100)"
    )

    # =========================================================================
    # ÍNDICES — usuario_sistema
    # =========================================================================
    op.execute("CREATE INDEX idx_usuario_email ON usuario_sistema (email)")
    op.execute("CREATE INDEX idx_usuario_rol ON usuario_sistema (rol)")
    op.execute(
        "CREATE INDEX idx_usuario_persona ON usuario_sistema (persona_id)"
        " WHERE persona_id IS NOT NULL"
    )

    op.execute("""
        CREATE TRIGGER trg_usuario_updated_at
            BEFORE UPDATE ON usuario_sistema
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — cosecha
    # =========================================================================
    op.execute("CREATE INDEX idx_cosecha_fuente_estado ON cosecha (fuente, estado)")
    op.execute("CREATE INDEX idx_cosecha_created ON cosecha (created_at DESC)")

    op.execute("""
        CREATE TRIGGER trg_cosecha_updated_at
            BEFORE UPDATE ON cosecha
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # =========================================================================
    # ÍNDICES — auditoria
    # =========================================================================
    op.execute("CREATE INDEX idx_auditoria_usuario ON auditoria (usuario_id)")
    op.execute("CREATE INDEX idx_auditoria_entidad ON auditoria (entidad_tipo, entidad_id)")
    op.execute("CREATE INDEX idx_auditoria_created ON auditoria (created_at DESC)")
    op.execute("CREATE INDEX idx_auditoria_accion ON auditoria (accion)")

    # =========================================================================
    # ÍNDICES — persona_dependencia_historico
    # =========================================================================
    op.execute(
        "CREATE INDEX idx_persona_dep_hist_persona ON persona_dependencia_historico (persona_id)"
    )
    op.execute(
        "CREATE INDEX idx_persona_dep_hist_actual"
        " ON persona_dependencia_historico (persona_id, es_actual)"
        " WHERE es_actual = TRUE"
    )


def downgrade() -> None:
    # =========================================================================
    # Drop triggers primero (antes de los índices)
    # =========================================================================
    op.execute("DROP TRIGGER IF EXISTS trg_cosecha_updated_at ON cosecha")
    op.execute("DROP TRIGGER IF EXISTS trg_usuario_updated_at ON usuario_sistema")
    op.execute("DROP TRIGGER IF EXISTS trg_simulacion_updated_at ON simulacion")
    op.execute("DROP TRIGGER IF EXISTS trg_gemelo_updated_at ON gemelo")
    op.execute("DROP TRIGGER IF EXISTS trg_documento_corpus_updated_at ON documento_corpus")
    op.execute("DROP TRIGGER IF EXISTS trg_paper_updated_at ON paper")
    op.execute("DROP TRIGGER IF EXISTS trg_persona_updated_at ON persona")
    op.execute("DROP TRIGGER IF EXISTS trg_area_conocimiento_updated_at ON area_conocimiento")
    op.execute("DROP TRIGGER IF EXISTS trg_cuerpo_academico_updated_at ON cuerpo_academico")
    op.execute("DROP TRIGGER IF EXISTS trg_dependencia_updated_at ON dependencia")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    # =========================================================================
    # Drop índices — persona_dependencia_historico
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_persona_dep_hist_actual")
    op.execute("DROP INDEX IF EXISTS idx_persona_dep_hist_persona")

    # =========================================================================
    # Drop índices — auditoria
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_auditoria_accion")
    op.execute("DROP INDEX IF EXISTS idx_auditoria_created")
    op.execute("DROP INDEX IF EXISTS idx_auditoria_entidad")
    op.execute("DROP INDEX IF EXISTS idx_auditoria_usuario")

    # =========================================================================
    # Drop índices — cosecha
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_cosecha_created")
    op.execute("DROP INDEX IF EXISTS idx_cosecha_fuente_estado")

    # =========================================================================
    # Drop índices — usuario_sistema
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_usuario_persona")
    op.execute("DROP INDEX IF EXISTS idx_usuario_rol")
    op.execute("DROP INDEX IF EXISTS idx_usuario_email")

    # =========================================================================
    # Drop índices — respuesta_simulacion
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_respuesta_embedding")
    op.execute("DROP INDEX IF EXISTS idx_respuesta_postura")
    op.execute("DROP INDEX IF EXISTS idx_respuesta_persona")
    op.execute("DROP INDEX IF EXISTS idx_respuesta_gemelo")
    op.execute("DROP INDEX IF EXISTS idx_respuesta_simulacion")

    # =========================================================================
    # Drop índices — simulacion
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_simulacion_created")
    op.execute("DROP INDEX IF EXISTS idx_simulacion_estado")
    op.execute("DROP INDEX IF EXISTS idx_simulacion_creada_por")

    # =========================================================================
    # Drop índices — gemelo_corpus_uso
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_gemelo_corpus_uso_documento")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_corpus_uso_paper")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_corpus_uso_gemelo")

    # =========================================================================
    # Drop índices — gemelo
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_gemelo_rasgos_combo")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_embedding")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_score_veracidad")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_version_actual")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_estado")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_persona")
    op.execute("DROP INDEX IF EXISTS idx_gemelo_actual_unico")

    # =========================================================================
    # Drop índices — documento_corpus
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_documento_corpus_estado")
    op.execute("DROP INDEX IF EXISTS idx_documento_corpus_paper")
    op.execute("DROP INDEX IF EXISTS idx_documento_corpus_persona")

    # =========================================================================
    # Drop índices — coautoria
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_coautoria_primer_autor")
    op.execute("DROP INDEX IF EXISTS idx_coautoria_paper")
    op.execute("DROP INDEX IF EXISTS idx_coautoria_persona")

    # =========================================================================
    # Drop índices — paper
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_paper_embedding")
    op.execute("DROP INDEX IF EXISTS idx_paper_conceptos")
    op.execute("DROP INDEX IF EXISTS idx_paper_titulo_trgm")
    op.execute("DROP INDEX IF EXISTS idx_paper_año")
    op.execute("DROP INDEX IF EXISTS idx_paper_openalex")
    op.execute("DROP INDEX IF EXISTS idx_paper_doi")

    # =========================================================================
    # Drop índices — persona_area
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_persona_area_peso")
    op.execute("DROP INDEX IF EXISTS idx_persona_area_area")

    # =========================================================================
    # Drop índices — persona
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_persona_embedding")
    op.execute("DROP INDEX IF EXISTS idx_persona_nombre_trgm")
    op.execute("DROP INDEX IF EXISTS idx_persona_openalex")
    op.execute("DROP INDEX IF EXISTS idx_persona_orcid")
    op.execute("DROP INDEX IF EXISTS idx_persona_activa")
    op.execute("DROP INDEX IF EXISTS idx_persona_nivel_snii")
    op.execute("DROP INDEX IF EXISTS idx_persona_tipo")
    op.execute("DROP INDEX IF EXISTS idx_persona_cuerpo_academico")
    op.execute("DROP INDEX IF EXISTS idx_persona_dependencia")

    # =========================================================================
    # Drop índices — area_conocimiento
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_area_conocimiento_codigo")
    op.execute("DROP INDEX IF EXISTS idx_area_conocimiento_nivel")
    op.execute("DROP INDEX IF EXISTS idx_area_conocimiento_parent")

    # =========================================================================
    # Drop índices — cuerpo_academico
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_cuerpo_academico_nombre_trgm")
    op.execute("DROP INDEX IF EXISTS idx_cuerpo_academico_estatus")
    op.execute("DROP INDEX IF EXISTS idx_cuerpo_academico_dependencia")

    # =========================================================================
    # Drop índices — dependencia
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_dependencia_activa")
    op.execute("DROP INDEX IF EXISTS idx_dependencia_campus")
    op.execute("DROP INDEX IF EXISTS idx_dependencia_codigo")
