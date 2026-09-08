"""Store transparent office-filter classification on notices.

Revision ID: 20260908_02
Revises: 20260908_01
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260908_02"
down_revision = "20260908_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("notice")}
    if "service_categories" not in columns:
        op.add_column("notice", sa.Column("service_categories", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"))
        op.create_index("ix_notice_service_categories_gin", "notice", ["service_categories"], postgresql_using="gin")
    if "object_types" not in columns:
        op.add_column("notice", sa.Column("object_types", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"))
        op.create_index("ix_notice_object_types_gin", "notice", ["object_types"], postgresql_using="gin")
    if "classification_reasons" not in columns:
        op.add_column("notice", sa.Column("classification_reasons", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))


def downgrade() -> None:
    op.drop_index("ix_notice_object_types_gin", table_name="notice")
    op.drop_index("ix_notice_service_categories_gin", table_name="notice")
    op.drop_column("notice", "classification_reasons")
    op.drop_column("notice", "object_types")
    op.drop_column("notice", "service_categories")
