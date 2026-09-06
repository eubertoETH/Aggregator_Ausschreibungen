from datetime import date, datetime

from sqlalchemy import Computed, Date, DateTime, Index, String, Text, UniqueConstraint
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
    estimated_value: Mapped[str | None] = mapped_column(String(64))
    currency: Mapped[str | None] = mapped_column(String(8))
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
        Index("ix_notice_text_gin", "search_vector", postgresql_using="gin"),
    )
