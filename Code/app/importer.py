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

from sqlalchemy.dialects.postgresql import insert

from .database import SessionLocal
from .models import Notice, RawNotice, Source
from .settings import RAW_ARCHIVE_DIR

DOE_EXPORT = "https://oeffentlichevergabe.de/api/notice-exports?pubDay={day}&format=csv.zip"
KEYWORDS = {
    "bestand": ("bestand", "umbau", "revitalisierung", "modernisierung", "denkmalschutz"),
    "sanierung": ("sanierung", "instandsetzung", "renovierung", "modernisierung"),
    "fassade": ("fassade", "fassaden", "gebäudehülle", "hülle"),
    "energie": ("energetisch", "energieeffizienz", "wärmeschutz"),
}


def rows_from_zip(archive: bytes) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        for name in bundle.namelist():
            if name.endswith(".csv"):
                tables[name.removesuffix(".csv")] = list(csv.DictReader(io.TextIOWrapper(bundle.open(name), encoding="utf-8")))
    return tables


def grouped(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    result: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        result[(row["noticeIdentifier"], row["noticeVersion"])].append(row)
    return result


def profile_tags(title: str, description: str) -> list[str]:
    haystack = f"{title} {description}".lower()
    return [tag for tag, words in KEYWORDS.items() if any(word in haystack for word in words)]


def first(rows: list[dict[str, str]], key: str, default: str | None = None) -> str | None:
    return next((row.get(key) for row in rows if row.get(key)), default)


def import_day(import_day: date) -> int:
    with urlopen(DOE_EXPORT.format(day=import_day.isoformat()), timeout=120) as response:
        archive = response.read()
    raw_dir = Path(RAW_ARCHIVE_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"doe-{import_day.isoformat()}-csv.zip").write_bytes(archive)
    tables = rows_from_zip(archive)
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
            title, description = first(purposes, "title"), first(purposes, "description", "")
            cpvs: list[str] = []
            for classification in classifications:
                if classification.get("classificationType") == "cpv":
                    cpvs.extend(filter(None, [classification.get("mainClassificationCode", ""), *classification.get("additionalClassificationCodes", "").split(",")]))
            payload = {name: values.get(key, []) for name, values in by_key.items()}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            raw_values = dict(source_code="doe", external_id=key[0], version=key[1], fetched_at=now, payload=payload, payload_hash=digest)
            session.execute(insert(RawNotice).values(**raw_values).on_conflict_do_nothing(index_elements=["source_code", "external_id", "version"]))
            value = first(purposes, "estimatedValue")
            notice_values = dict(
                source_code="doe", publication_number=key[0], version=key[1],
                publication_date=date.fromisoformat(item["publicationDate"][:10]), notice_type=item.get("noticeType"), form_type=item.get("formType"),
                title=title, description=description, buyer_name=first(orgs, "organisationName"), buyer_id=first(orgs, "organisationIdentifier"),
                city=first(places, "placePerformanceCity"), nuts_region=first(places, "placePerformanceCountrySubdivision"), country_code=first(places, "placePerformanceCountryCode"),
                procedure_type=first(procedures, "procedureType"), cpv_codes=sorted(set(cpvs)), tags=profile_tags(title or "", description or ""),
                estimated_value=value, currency=first(purposes, "estimatedValueCurrency"),
                # The DÖE CSV export has no reliable source-document URL. Do not invent one;
                # this field is populated when the eForms source-document parser is added.
                notice_url=None, raw_payload=payload, imported_at=now,
            )
            session.execute(insert(Notice).values(**notice_values).on_conflict_do_update(
                constraint="uq_notice_version", set_={name: value for name, value in notice_values.items() if name not in {"source_code", "publication_number", "version"}}
            ))
        session.query(Source).filter_by(code="doe").update({"last_successful_fetch": now})
    return len(notices)
