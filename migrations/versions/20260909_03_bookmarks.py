"""Add global tender bookmarks and notes.

Revision ID: 20260909_03
Revises: 20260908_02
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = "20260909_03"
down_revision = "20260908_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("notice_cluster")}
    if "bookmarked_at" not in columns:
        op.add_column("notice_cluster", sa.Column("bookmarked_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_notice_cluster_bookmarked_at", "notice_cluster", ["bookmarked_at"])
    if "bookmark_note" not in columns:
        op.add_column("notice_cluster", sa.Column("bookmark_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_index("ix_notice_cluster_bookmarked_at", table_name="notice_cluster")
    op.drop_column("notice_cluster", "bookmark_note")
    op.drop_column("notice_cluster", "bookmarked_at")
