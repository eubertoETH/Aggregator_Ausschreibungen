"""Idempotent normalization backfills from retained raw source payloads."""
import argparse

from sqlalchemy import select

from .clustering import assign_notice_cluster
from .database import SessionLocal
from .importer import eforms_metadata
from .models import Notice


def backfill_doe_procedure_identifiers() -> int:
    """Extract eForms BT-04 from existing DÖE raw payloads without redownload."""
    changed = 0
    with SessionLocal.begin() as session:
        notices = session.scalars(select(Notice).where(Notice.source_code == "doe", Notice.procedure_identifier.is_(None))).all()
        for notice in notices:
            xml = (notice.raw_payload or {}).get("eforms_xml")
            metadata = eforms_metadata(xml)
            procedure_identifier = metadata["procedure_identifier"]
            if procedure_identifier:
                notice.procedure_identifier = procedure_identifier
                changed += 1
            assign_notice_cluster(session, notice.id, procedure_identifier, source_code="doe")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["doe"], default="doe")
    args = parser.parse_args()
    if args.source == "doe":
        print(f"Backfilled {backfill_doe_procedure_identifiers()} DÖE procedure identifiers")


if __name__ == "__main__":
    main()
