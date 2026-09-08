from datetime import date, datetime

from sqlalchemy import Computed, Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Source(Base):
    __tablename__ = "source"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    last_successful_fetch: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RawNotice(Base):
    __tablename__ = "raw_notice"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_code: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSONB)
    payload_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("source_code", "external_id", "version", name="uq_raw_notice_version"),)


class Notice(Base):
    __tablename__ = "notice"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_code: Mapped[str] = mapped_column(String(32), default="doe")
    publication_number: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(32))
    # eForms BT-04. DÖE calls it ContractFolderID; TED exposes it as
    # procedure-identifier. It is the exact, cross-source cluster key.
    procedure_identifier: Mapped[str | None] = mapped_column(String(128), index=True)
    publication_date: Mapped[date | None] = mapped_column(Date, index=True)
    notice_type: Mapped[str | None] = mapped_column(String(64), index=True)
    form_type: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    buyer_name: Mapped[str | None] = mapped_column(String(512), index=True)
    buyer_id: Mapped[str | None] = mapped_column(String(256))
    city: Mapped[str | None] = mapped_column(String(256), index=True)
    nuts_region: Mapped[str | None] = mapped_column(String(32), index=True)
    country_code: Mapped[str | None] = mapped_column(String(8), index=True)
    procedure_type: Mapped[str | None] = mapped_column(String(64), index=True)
    cpv_codes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    service_categories: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    object_types: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    classification_reasons: Mapped[dict] = mapped_column(JSONB, default=dict)
    estimated_value: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(8))
    submission_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    participation_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    notice_url: Mapped[str | None] = mapped_column(String(512))
    raw_payload: Mapped[dict] = mapped_column(JSONB)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('german', coalesce(title, '') || ' ' || coalesce(description, ''))", persisted=True),
    )
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("source_code", "publication_number", "version", name="uq_notice_version"),
        Index("ix_notice_search", "publication_date", "notice_type", "nuts_region"),
        Index("ix_notice_cpv_gin", "cpv_codes", postgresql_using="gin"),
        Index("ix_notice_tags_gin", "tags", postgresql_using="gin"),
        Index("ix_notice_service_categories_gin", "service_categories", postgresql_using="gin"),
        Index("ix_notice_object_types_gin", "object_types", postgresql_using="gin"),
        Index("ix_notice_text_gin", "search_vector", postgresql_using="gin"),
    )


class NoticeCluster(Base):
    """One procurement procedure as shown to users, independent of source."""

    __tablename__ = "notice_cluster"
    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable internal key: procedure:<BT-04> for proven matches, otherwise a
    # provisional notice:<id>. It lets legacy records be backfilled safely.
    identity_key: Mapped[str] = mapped_column(String(192), unique=True)
    procedure_identifier: Mapped[str | None] = mapped_column(String(128), index=True)
    match_rule_version: Mapped[str] = mapped_column(String(32), default="exact-procedure-v1")
    conflict_status: Mapped[str] = mapped_column(String(32), default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        Index(
            "uq_notice_cluster_procedure_identifier",
            "procedure_identifier",
            unique=True,
            postgresql_where=text("procedure_identifier IS NOT NULL"),
        ),
    )


class NoticeClusterMember(Base):
    """Provenance-bearing membership of a source notice in one cluster."""

    __tablename__ = "notice_cluster_member"
    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("notice_cluster.id", ondelete="CASCADE"), index=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("notice.id", ondelete="CASCADE"), unique=True, index=True)
    match_method: Mapped[str] = mapped_column(String(64))
    match_confidence: Mapped[str] = mapped_column(String(16))
    match_rule_version: Mapped[str] = mapped_column(String(32))
    field_provenance: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
