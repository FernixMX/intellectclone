"""
Modelos SQLAlchemy: sistema (usuarios, cosechas, auditoría).
Tablas: UsuarioSistema, Cosecha, Auditoria
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from intellectclone.db.base import Base
from intellectclone.models.enums import EstadoCosecha, RolUsuario, TipoFuente

if TYPE_CHECKING:
    from intellectclone.models.persona import Persona
    from intellectclone.models.simulacion import Simulacion


class UsuarioSistema(Base):
    """Usuarios autenticados del sistema (operadores, no personas retratadas)."""

    __tablename__ = "usuario_sistema"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    # Autenticación
    password_hash: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    password_set_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    email_verificado: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)

    # Rol y permisos
    rol: Mapped[RolUsuario] = mapped_column(
        sa.Enum(RolUsuario, name="rol_usuario", create_type=False),
        nullable=False,
        default=RolUsuario.lectura,
    )

    # Vínculo con persona retratada (autovalidación)
    persona_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("persona.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Restricciones de presupuesto
    presupuesto_mensual_usd: Mapped[float | None] = mapped_column(sa.Numeric(10, 2), nullable=True)
    consumido_mes_usd: Mapped[float] = mapped_column(sa.Numeric(10, 4), nullable=False, default=0)

    # Estado
    activo: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    ultimo_login: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )

    metadatos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    persona: Mapped["Persona | None"] = relationship("Persona", back_populates="usuario_sistema")
    simulaciones: Mapped[list["Simulacion"]] = relationship(
        "Simulacion",
        back_populates="creador",
        foreign_keys="Simulacion.creada_por",
        primaryjoin="UsuarioSistema.id == Simulacion.creada_por",
    )
    cosechas_disparadas: Mapped[list["Cosecha"]] = relationship(
        "Cosecha", back_populates="disparador"
    )
    auditorias: Mapped[list["Auditoria"]] = relationship("Auditoria", back_populates="usuario")


class Cosecha(Base):
    """Cada corrida de un harvester (manual — R6: no hay schedulers automáticos)."""

    __tablename__ = "cosecha"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fuente: Mapped[TipoFuente] = mapped_column(
        sa.Enum(TipoFuente, name="tipo_fuente", create_type=False),
        nullable=False,
    )
    estado: Mapped[EstadoCosecha] = mapped_column(
        sa.Enum(EstadoCosecha, name="estado_cosecha", create_type=False),
        nullable=False,
        default=EstadoCosecha.programada,
    )

    # Tiempos
    programada_para: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    iniciada_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    completada_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    duracion_ms: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)

    # Resultados
    registros_procesados: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    registros_nuevos: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    registros_actualizados: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    registros_descartados: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    errores_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    # Configuración
    configuracion: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )

    # Errores y log
    log_resumen: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    errores: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Disparada por
    disparada_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuario_sistema.id", ondelete="SET NULL"),
        nullable=True,
    )
    disparada_manual: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    disparador: Mapped["UsuarioSistema | None"] = relationship(
        "UsuarioSistema", back_populates="cosechas_disparadas"
    )


class Auditoria(Base):
    """Registro de acciones sensibles del sistema."""

    __tablename__ = "auditoria"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuario_sistema.id", ondelete="SET NULL"),
        nullable=True,
    )
    accion: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    entidad_tipo: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    entidad_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_origen: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    usuario: Mapped["UsuarioSistema | None"] = relationship(
        "UsuarioSistema", back_populates="auditorias"
    )
