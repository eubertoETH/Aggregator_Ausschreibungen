"""Add source-independent procurement clusters.

Revision ID: 20260908_01
Revises:
Create Date: 2026-09-08
"""
from alembic import op
import sqlalchemy as sa


revision = "20260908_01"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    bind = op.get_bind()

    # Existing production databases were created by the prototype's
    # metadata.create_all(). Fresh installations use the complete current
    # metadata once, then Alembic owns all subsequent changes.
    if not _has_table("source"):
        from app.database import Base
        from app import models  # noqa: F401

        Base.metadata.create_all(bind=bind)
        return

    columns = {column["name"] for column in sa.inspect(bind).get_columns("notice")}
    if "procedure_identifier" not in columns:
        op.add_column("notice", sa.Column("procedure_identifier", sa.String(length=128), nullable=True))
        op.create_index("ix_notice_procedure_identifier", "notice", ["procedure_identifier"])

    if not _has_table("notice_cluster"):
        op.create_table(
            "notice_cluster",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("identity_key", sa.String(length=192), nullable=False, unique=True),
            sa.Column("procedure_identifier", sa.String(length=128), nullable=True),
            sa.Column("match_rule_version", sa.String(length=32), nullable=False),
            sa.Column("conflict_status", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_notice_cluster_procedure_identifier", "notice_cluster", ["procedure_identifier"])
        op.create_index(
            "uq_notice_cluster_procedure_identifier",
            "notice_cluster",
            ["procedure_identifier"],
            unique=True,
            postgresql_where=sa.text("procedure_identifier IS NOT NULL"),
        )

    if not _has_table("notice_cluster_member"):
        op.create_table(
            "notice_cluster_member",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("cluster_id", sa.Integer(), sa.ForeignKey("notice_cluster.id", ondelete="CASCADE"), nullable=False),
            sa.Column("notice_id", sa.Integer(), sa.ForeignKey("notice.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("match_method", sa.String(length=64), nullable=False),
            sa.Column("match_confidence", sa.String(length=16), nullable=False),
            sa.Column("match_rule_version", sa.String(length=32), nullable=False),
            sa.Column("field_provenance", sa.dialects.postgresql.JSONB(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_notice_cluster_member_cluster_id", "notice_cluster_member", ["cluster_id"])
        op.create_index("ix_notice_cluster_member_notice_id", "notice_cluster_member", ["notice_id"])

    # Every legacy row is preserved as a safe singleton. Re-importing a DÖE
    # notice later promotes it to an exact procedure cluster when BT-04 exists.
    op.execute(
        """
        INSERT INTO notice_cluster (identity_key, procedure_identifier, match_rule_version, conflict_status, created_at)
        SELECT 'notice:' || id::text, NULL, 'legacy-singleton-v1', 'none', NOW()
        FROM notice
        ON CONFLICT (identity_key) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO notice_cluster_member
            (cluster_id, notice_id, match_method, match_confidence, match_rule_version, field_provenance, created_at)
        SELECT cluster.id, notice.id, 'source-singleton', 'not-applicable', 'legacy-singleton-v1', '{}'::jsonb, NOW()
        FROM notice
        JOIN notice_cluster AS cluster ON cluster.identity_key = 'notice:' || notice.id::text
        LEFT JOIN notice_cluster_member AS member ON member.notice_id = notice.id
        WHERE member.id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_table("notice_cluster_member")
    op.drop_table("notice_cluster")
    op.drop_index("ix_notice_procedure_identifier", table_name="notice")
    op.drop_column("notice", "procedure_identifier")
