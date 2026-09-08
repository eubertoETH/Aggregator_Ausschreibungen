"""Deterministic notice-cluster assignment.

Only the proven eForms procedure identifier is allowed to merge records from
different sources. Fuzzy candidates deliberately remain outside this module
until a reviewed rule and a human-review workflow exist.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import NoticeCluster, NoticeClusterMember

EXACT_PROCEDURE_RULE = "exact-procedure-v1"


def _procedure_key(procedure_identifier: str) -> str:
    return f"procedure:{procedure_identifier.strip().lower()}"


def assign_notice_cluster(session: Session, notice_id: int, procedure_identifier: str | None, source_code: str | None = None) -> None:
    """Attach a source notice to its exact procedure cluster or safe singleton."""
    now = datetime.now(timezone.utc)
    procedure_identifier = procedure_identifier.strip() if procedure_identifier else None
    identity_key = _procedure_key(procedure_identifier) if procedure_identifier else f"notice:{notice_id}"
    cluster = session.scalar(select(NoticeCluster).where(NoticeCluster.identity_key == identity_key))
    if cluster is None:
        cluster = NoticeCluster(
            identity_key=identity_key,
            procedure_identifier=procedure_identifier,
            match_rule_version=EXACT_PROCEDURE_RULE,
            conflict_status="none",
            created_at=now,
        )
        session.add(cluster)
        session.flush()

    member = session.scalar(select(NoticeClusterMember).where(NoticeClusterMember.notice_id == notice_id))
    provenance = {field: source_code for field in ("title", "description", "buyer_name", "city", "nuts_region", "cpv_codes", "deadlines", "notice_url") if source_code}
    if member is None:
        session.add(
            NoticeClusterMember(
                cluster_id=cluster.id,
                notice_id=notice_id,
                match_method="exact-procedure" if procedure_identifier else "source-singleton",
                match_confidence="high" if procedure_identifier else "not-applicable",
                match_rule_version=EXACT_PROCEDURE_RULE,
                field_provenance=provenance,
                created_at=now,
            )
        )
        return

    if member.cluster_id != cluster.id:
        member.cluster_id = cluster.id
        member.match_method = "exact-procedure"
        member.match_confidence = "high"
        member.match_rule_version = EXACT_PROCEDURE_RULE
    if provenance:
        member.field_provenance = provenance
