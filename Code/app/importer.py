"""DÖE CSV import. Keeps the raw daily archive on disk and each source row in PostgreSQL."""
import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

from sqlalchemy.dialects.postgresql import insert

from .clustering import assign_notice_cluster
from .database import SessionLocal
from .models import Notice, RawNotice, Source
from .settings import RAW_ARCHIVE_DIR

DOE_EXPORT = "https://oeffentlichevergabe.de/api/notice-exports?pubDay={day}&format={format}"
KEYWORDS = {
    "bestand": ("bestand", "umbau", "revitalisierung", "modernisierung", "denkmalschutz"),
    "sanierung": ("sanierung", "instandsetzung", "renovierung", "modernisierung"),
    "fassade": ("fassade", "fassaden", "gebäudehülle", "hülle"),
    "energie": ("energetisch", "energieeffizienz", "wärmeschutz"),
}
PROFILE_CPV_PREFIXES = ("712", "7132", "714", "7153", "7154")


def rows_from_zip(archive: bytes) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        for name in bundle.namelist():
            if name.endswith(".csv"):
                tables[name.removesuffix(".csv")] = list(csv.DictReader(io.TextIOWrapper(bundle.open(name), encoding="utf-8")))
    return tables


def eforms_from_zip(archive: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        return {name: bundle.read(name).decode("utf-8") for name in bundle.namelist() if name.endswith(".xml")}


def local_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].split(":")[-1]


def deadline(period: ElementTree.Element) -> datetime | None:
    values = {local_name(child): (child.text or "").strip() for child in period.iter()}
    end_date, end_time = values.get("EndDate"), values.get("EndTime")
    if not end_date or not end_time:
        return None
    return datetime.fromisoformat(f"{end_date[:10]}T{end_time}")


def eforms_metadata(xml: str | None) -> dict[str, datetime | str | None]:
    if not xml:
        return {"submission_deadline": None, "participation_deadline": None, "notice_url": None, "procedure_identifier": None}
    root = ElementTree.fromstring(xml)
    metadata: dict[str, datetime | str | None] = {"submission_deadline": None, "participation_deadline": None, "notice_url": None, "procedure_identifier": None}
    for element in root.iter():
        name = local_name(element)
        if name == "TenderSubmissionDeadlinePeriod":
            metadata["submission_deadline"] = deadline(element)
        elif name == "ParticipationRequestReceptionPeriod":
            metadata["participation_deadline"] = deadline(element)
        elif name == "CallForTendersDocumentReference" and not metadata["notice_url"]:
            metadata["notice_url"] = next((child.text.strip() for child in element.iter() if local_name(child) == "URI" and child.text), None)
        elif name == "ContractFolderID" and not metadata["procedure_identifier"] and element.text:
            metadata["procedure_identifier"] = element.text.strip()
    return metadata


def grouped(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    result: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        result[(row["noticeIdentifier"], row["noticeVersion"])].append(row)
    return result


def profile_tags(title: str, description: str, cpv_codes: list[str]) -> list[str]:
    haystack = f"{title} {description}".lower()
    tags = [tag for tag, words in KEYWORDS.items() if any(word in haystack for word in words)]
    if any(code.startswith(PROFILE_CPV_PREFIXES) for code in cpv_codes):
        tags.append("architektur / planung")
    return tags


def first(rows: list[dict[str, str]], key: str, default: str | None = None) -> str | None:
    return next((row.get(key) for row in rows if row.get(key)), default)


def import_day(import_day: date) -> int:
    with urlopen(DOE_EXPORT.format(day=import_day.isoformat(), format="csv.zip"), timeout=120) as response:
        archive = response.read()
    with urlopen(DOE_EXPORT.format(day=import_day.isoformat(), format="eforms.zip"), timeout=120) as response:
        eforms_archive = response.read()
    raw_dir = Path(RAW_ARCHIVE_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"doe-{import_day.isoformat()}-csv.zip").write_bytes(archive)
    (raw_dir / f"doe-{import_day.isoformat()}-eforms.zip").write_bytes(eforms_archive)
    tables = rows_from_zip(archive)
    eforms = eforms_from_zip(eforms_archive)
    notices = tables.get("notice", [])
    by_key = {name: grouped(rows) for name, rows in tables.items()}
    now = datetime.now(timezone.utc)
    with SessionLocal.begin() as session:
        session.execute(insert(Source).values(code="doe", name="Datenservice Öffentlicher Einkauf").on_conflict_do_nothing(index_elements=["code"]))
        for item in notices:
            key = (item["noticeIdentifier"], item["noticeVersion"])
            purposes = by_key.get("purpose", {}).get(key, [])
            orgs = by_key.get("organisation", {}).get(key, [])
            places = by_key.get("placeOfPerformance", {}).get(key, [])
            classifications = by_key.get("classification", {}).get(key, [])
            procedures = by_key.get("procedure", {}).get(key, [])
            xml = eforms.get(f"{key[0]}-{key[1]}.xml")
            metadata = eforms_metadata(xml)
            title, description = first(purposes, "title"), first(purposes, "description", "")
            cpvs: list[str] = []
            for classification in classifications:
                if classification.get("classificationType") == "cpv":
                    cpvs.extend(filter(None, [classification.get("mainClassificationCode", ""), *classification.get("additionalClassificationCodes", "").split(",")]))
            payload = {"csv": {name: values.get(key, []) for name, values in by_key.items()}, "eforms_xml": xml}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            raw_values = dict(source_code="doe", external_id=key[0], version=key[1], fetched_at=now, payload=payload, payload_hash=digest)
            session.execute(insert(RawNotice).values(**raw_values).on_conflict_do_update(
                constraint="uq_raw_notice_version", set_={"fetched_at": now, "payload": payload, "payload_hash": digest}
            ))
            value = first(purposes, "estimatedValue")
            notice_values = dict(
                source_code="doe", publication_number=key[0], version=key[1], procedure_identifier=metadata["procedure_identifier"],
                publication_date=date.fromisoformat(item["publicationDate"][:10]), notice_type=item.get("noticeType"), form_type=item.get("formType"),
                title=title, description=description, buyer_name=first(orgs, "organisationName"), buyer_id=first(orgs, "organisationIdentifier"),
                city=first(places, "placePerformanceCity"), nuts_region=first(places, "placePerformanceCountrySubdivision"), country_code=first(places, "placePerformanceCountryCode"),
                procedure_type=first(procedures, "procedureType"), cpv_codes=sorted(set(cpvs)), tags=profile_tags(title or "", description or "", cpvs),
                estimated_value=value, currency=first(purposes, "estimatedValueCurrency"),
                submission_deadline=metadata["submission_deadline"], participation_deadline=metadata["participation_deadline"],
                notice_url=metadata["notice_url"], raw_payload=payload, imported_at=now,
            )
            notice_id = session.execute(insert(Notice).values(**notice_values).on_conflict_do_update(
                constraint="uq_notice_version", set_={name: value for name, value in notice_values.items() if name not in {"source_code", "publication_number", "version"}}
            ).returning(Notice.id)).scalar_one()
            assign_notice_cluster(session, notice_id, metadata["procedure_identifier"])
        session.query(Source).filter_by(code="doe").update({"last_successful_fetch": now})
    return len(notices)
