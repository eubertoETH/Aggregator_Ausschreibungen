"""TED Search API connector for German places of performance.

The connector stores each search result and its original eForms XML before it
normalizes anything. It is deliberately independent from the DÖE connector.
"""
import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from sqlalchemy.dialects.postgresql import insert

from .clustering import assign_notice_cluster
from .database import SessionLocal
from .importer import eforms_metadata, local_name, profile_tags
from .models import Notice, RawNotice, Source
from .settings import RAW_ARCHIVE_DIR, TED_COUNTRY_CODE
from .taxonomy import classify

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"
TED_FIELDS = [
    "publication-number",
    "procedure-identifier",
    "notice-type",
    "form-type",
    "notice-title",
    "buyer-name",
    "links",
]


def _fetch(request: Request | str, attempts: int = 3) -> bytes:
    error: OSError | None = None
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=90) as response:
                return response.read()
        except (OSError, URLError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    assert error is not None
    raise error


def _localized(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if not isinstance(value, dict):
        return None
    values = {str(key).lower(): item for key, item in value.items()}
    for language in ("deu", "eng"):
        item = values.get(language)
        if isinstance(item, str) and item.strip():
            return item.strip()
    return next((item.strip() for item in values.values() if isinstance(item, str) and item.strip()), None)


def _first_text(element: ElementTree.Element, name: str) -> str | None:
    return next((child.text.strip() for child in element.iter() if local_name(child) == name and child.text and child.text.strip()), None)


def _ted_fields(xml: str, result: dict) -> dict:
    root = ElementTree.fromstring(xml)
    metadata = eforms_metadata(xml)
    project = next((element for element in root.iter() if local_name(element) == "ProcurementProject"), root)
    location = next((element for element in root.iter() if local_name(element) == "RealizedLocation"), root)
    cpvs = [
        element.text.strip()
        for element in root.iter()
        if local_name(element) == "ItemClassificationCode"
        and element.text
        and element.attrib.get("listID", "").lower() in {"", "cpv"}
    ]
    amount = next((element for element in root.iter() if local_name(element) in {"EstimatedOverallContractAmount", "EstimatedValue"}), None)
    amount_value = _first_text(amount, "Amount") if amount is not None else None
    amount_currency = next(
        (child.attrib.get("currencyID") for child in amount.iter() if local_name(child) == "Amount" and child.attrib.get("currencyID")),
        None,
    ) if amount is not None else None
    links = result.get("links") or {}
    html = links.get("htmlDirect") or links.get("html") or {}
    return {
        "procedure_identifier": metadata["procedure_identifier"] or result.get("procedure-identifier"),
        "version": metadata.get("version") or "1",
        "title": _localized(result.get("notice-title")) or _first_text(project, "Name"),
        "description": _first_text(project, "Description") or "",
        "buyer_name": _localized(result.get("buyer-name")),
        "buyer_id": None,
        "city": _first_text(location, "CityName"),
        "nuts_region": _first_text(location, "CountrySubentityCode"),
        "country_code": _first_text(location, "IdentificationCode"),
        "procedure_type": _first_text(root, "ProcedureCode"),
        "cpv_codes": sorted(set(cpvs)),
        "estimated_value": amount_value,
        "currency": amount_currency,
        "submission_deadline": metadata["submission_deadline"],
        "participation_deadline": metadata["participation_deadline"],
        "notice_url": html.get("DEU") or html.get("deu") or next(iter(html.values()), None) or metadata["notice_url"],
    }


def _search_day(import_day: date) -> list[dict]:
    query = f"publication-date = {import_day:%Y%m%d} AND place-of-performance-country-lot = {TED_COUNTRY_CODE}"
    notices: list[dict] = []
    page = 1
    while True:
        body = json.dumps({"query": query, "fields": TED_FIELDS, "page": page, "limit": 250, "scope": "ACTIVE"}).encode("utf-8")
        request = Request(TED_SEARCH_URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
        response = json.loads(_fetch(request))
        batch = response.get("notices") or []
        notices.extend(batch)
        if not batch or len(notices) >= int(response.get("totalNoticeCount") or 0):
            return notices
        page += 1


def _xml_link(result: dict) -> str | None:
    xml = (result.get("links") or {}).get("xml") or {}
    return xml.get("MUL") or xml.get("mul") or next(iter(xml.values()), None)


def _safe_file_name(publication_number: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", publication_number)


def import_ted_day(import_day: date) -> int:
    results = _search_day(import_day)
    raw_dir = Path(RAW_ARCHIVE_DIR) / "ted" / import_day.isoformat()
    raw_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    with SessionLocal.begin() as session:
        session.execute(insert(Source).values(code="ted", name="Tenders Electronic Daily").on_conflict_do_nothing(index_elements=["code"]))
        for result in results:
            publication_number = result["publication-number"]
            xml_url = _xml_link(result)
            if not xml_url:
                raise RuntimeError(f"TED notice {publication_number} has no XML link")
            xml = _fetch(xml_url).decode("utf-8")
            (raw_dir / f"{_safe_file_name(publication_number)}.xml").write_text(xml, encoding="utf-8")
            fields = _ted_fields(xml, result)
            version = str(fields["version"])
            payload = {"search": result, "eforms_xml": xml}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            session.execute(insert(RawNotice).values(
                source_code="ted", external_id=publication_number, version=version, fetched_at=now, payload=payload, payload_hash=digest
            ).on_conflict_do_update(
                constraint="uq_raw_notice_version", set_={"fetched_at": now, "payload": payload, "payload_hash": digest}
            ))
            title, description, cpvs = fields["title"] or "", fields["description"] or "", fields["cpv_codes"]
            services, objects, reasons = classify(title, description, cpvs)
            notice_values = dict(
                source_code="ted", publication_number=publication_number, version=version,
                procedure_identifier=fields["procedure_identifier"], publication_date=import_day,
                notice_type=result.get("notice-type"), form_type=result.get("form-type"),
                title=title, description=description, buyer_name=fields["buyer_name"], buyer_id=fields["buyer_id"],
                city=fields["city"], nuts_region=fields["nuts_region"], country_code=fields["country_code"],
                procedure_type=fields["procedure_type"], cpv_codes=cpvs,
                tags=profile_tags(title, description, cpvs), service_categories=services, object_types=objects, classification_reasons=reasons,
                estimated_value=fields["estimated_value"], currency=fields["currency"],
                submission_deadline=fields["submission_deadline"], participation_deadline=fields["participation_deadline"],
                notice_url=fields["notice_url"], raw_payload=payload, imported_at=now,
            )
            notice_id = session.execute(insert(Notice).values(**notice_values).on_conflict_do_update(
                constraint="uq_notice_version", set_={name: value for name, value in notice_values.items() if name not in {"source_code", "publication_number", "version"}}
            ).returning(Notice.id)).scalar_one()
            assign_notice_cluster(session, notice_id, fields["procedure_identifier"], source_code="ted")
        session.query(Source).filter_by(code="ted").update({"last_successful_fetch": now})
    return len(results)
