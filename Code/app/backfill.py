"""Idempotent normalization backfills from retained raw source payloads."""
import argparse

from sqlalchemy import select

from .clustering import assign_notice_cluster
from .database import SessionLocal
from .importer import eforms_metadata
from .models import Notice
from .taxonomy import classify


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


def backfill_classification() -> int:
    """Classify all retained notices; safe to run on every deployment."""
    changed = 0
    with SessionLocal.begin() as session:
        for notice in session.scalars(select(Notice)).all():
            services, objects, reasons = classify(notice.title, notice.description, notice.cpv_codes)
            if (notice.service_categories, notice.object_types, notice.classification_reasons) != (services, objects, reasons):
                notice.service_categories = services
                notice.object_types = objects
                notice.classification_reasons = reasons
                changed += 1
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["doe", "all"], default="all")
    args = parser.parse_args()
    if args.source == "doe":
        print(f"Backfilled {backfill_doe_procedure_identifiers()} DÖE procedure identifiers")
    else:
        procedure_count = backfill_doe_procedure_identifiers()
        classification_count = backfill_classification()
        print(f"Backfilled {procedure_count} DÖE procedure identifiers and classified {classification_count} notices")


if __name__ == "__main__":
    main()
