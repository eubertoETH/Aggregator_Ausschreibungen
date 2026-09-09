from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_

from .cluster_views import build_cluster_views
from .database import SessionLocal
from .geo import RADIUS_KM, matches_nuts_radius
from .importer import import_day
from .models import Notice, NoticeCluster, NoticeClusterMember
from .report import write_daily_report
from .taxonomy import CORE_SERVICE_CODES, service_labels, taxonomy_for_template
from .ted_importer import import_ted_day
from .workflow import STATUS_LABELS

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Ausschreibungsaggregator")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
PROFILE_TAGS = ["architektur / planung", "bestand", "sanierung", "fassade", "energie"]


def _page_links(current: int, count: int) -> list[int | None]:
    candidates = {1, count, *range(max(1, current - 2), min(count, current + 2) + 1)}
    result: list[int | None] = []
    previous = 0
    for item in sorted(candidates):
        if item - previous > 1:
            result.append(None)
        result.append(item)
        previous = item
    return result


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request, q: str = "", service: list[str] = Query(default=[]), object_type: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]), source_mode: str = "any", cpv: str = "", region: str = "",
    notice_type: str = "", scope: str = "profile", days: int = 30, radius: int = 75,
    status: list[str] = Query(default=[]), status_configured: bool = False, bookmarked: bool = False,
    below_threshold: bool = False,
    page: int = 1, page_size: int = 50,
):
    page_size = page_size if page_size in {25, 50, 75, 100} else 50
    radius = radius if radius in {*RADIUS_KM, 0} else 75
    page = max(page, 1)
    with SessionLocal() as session:
        rows = session.query(NoticeCluster, Notice).join(NoticeClusterMember, NoticeClusterMember.cluster_id == NoticeCluster.id).join(Notice, Notice.id == NoticeClusterMember.notice_id).all()
        clusters = build_cluster_views(rows)
        bookmark_count = sum(item.bookmarked for item in clusters)
        candidates = []
        needle = q.lower().strip()
        for item in clusters:
            text = " ".join(filter(None, [item.title, item.description, item.buyer_name, item.city, item.procedure_identifier, *[notice.publication_number for notice in item.notices]])).lower()
            if scope == "profile" and not (set(item.tags) & set(PROFILE_TAGS) or set(item.service_categories) & CORE_SERVICE_CODES):
                continue
            if needle and needle not in text:
                continue
            if service and not (set(item.service_categories) & set(service)):
                continue
            if object_type and not (set(item.object_types) & set(object_type)):
                continue
            item_sources = set(item.source_codes)
            if source and ((source_mode == "both" and not {"doe", "ted"}.issubset(item_sources)) or (source_mode != "both" and not item_sources & set(source))):
                continue
            if cpv and not any(code.startswith(cpv) for code in item.cpv_codes):
                continue
            if region and not (item.nuts_region or "").upper().startswith(region.upper()):
                continue
            if notice_type and item.notice_type != notice_type:
                continue
            if days and (not item.publication_date or item.publication_date < date.today() - timedelta(days=days)):
                continue
            if not matches_nuts_radius(item.nuts_region, radius or None):
                continue
            if bookmarked and not item.bookmarked:
                continue
            # This is deliberately only an explicit source signal. Missing or
            # estimated contract values must not be used to guess a threshold.
            if below_threshold and not item.is_below_threshold:
                continue
            candidates.append(item)
        active_statuses = status if status_configured else ["more_than_7", "one_to_7"]
        filtered = [item for item in candidates if item.status in active_statuses]
        status_counts = Counter(item.status for item in candidates)
        total = len(filtered)
        page_count = max(1, (total + page_size - 1) // page_size)
        page = min(page, page_count)
        notices = filtered[(page - 1) * page_size:page * page_size]
        types = [row[0] for row in session.query(Notice.notice_type).distinct().order_by(Notice.notice_type).all() if row[0]]

    filters = {"q": q, "service": service, "object_type": object_type, "source": source, "source_mode": source_mode, "cpv": cpv, "region": region, "notice_type": notice_type, "scope": scope, "days": days, "radius": radius, "status": active_statuses, "status_configured": True, "bookmarked": bookmarked, "below_threshold": below_threshold, "page_size": page_size}
    list_values = {"service", "object_type", "source", "status"}

    def filters_url(updated: dict, target: int = 1) -> str:
        params = [
            (key, str(value).lower() if isinstance(value, bool) else str(value))
            for key, value in updated.items() if key not in list_values
        ]
        params.append(("page", str(target)))
        for key in list_values:
            params.extend((key, value) for value in updated[key])
        return "?" + urlencode(params)

    def page_url(target: int) -> str:
        return filters_url(filters, target)

    def without_filter(key: str, value: str | None = None) -> str:
        updated = {name: items[:] if isinstance(items, list) else items for name, items in filters.items()}
        if value is not None:
            updated[key] = [item for item in updated[key] if item != value]
        elif key == "radius":
            updated[key] = 0
        elif key == "days":
            updated[key] = 0
        elif key == "scope":
            updated[key] = "all"
        elif key == "source_mode":
            updated[key] = "any"
        elif key in {"bookmarked", "below_threshold"}:
            updated[key] = False
        else:
            updated[key] = ""
        return filters_url(updated)
    object_labels = {"existing": "Bestand", "new_build": "Neubau", "mixed": "Mischprojekt"}
    active_filters: list[dict[str, str]] = []
    if q: active_filters.append({"label": f"Suche: {q}", "url": without_filter("q")})
    if scope == "profile": active_filters.append({"label": "Profiltreffer", "url": without_filter("scope")})
    if days: active_filters.append({"label": f"Veröffentlicht: {days} Tage", "url": without_filter("days")})
    if radius: active_filters.append({"label": f"Radius: {radius} km", "url": without_filter("radius")})
    for key, label in (("cpv", "CPV"), ("region", "NUTS"), ("notice_type", "Verfahren")):
        if filters[key]: active_filters.append({"label": f"{label}: {filters[key]}", "url": without_filter(key)})
    for item in service: active_filters.append({"label": service_labels().get(item, item), "url": without_filter("service", item)})
    for item in object_type: active_filters.append({"label": object_labels.get(item, item), "url": without_filter("object_type", item)})
    for item in source: active_filters.append({"label": item.upper(), "url": without_filter("source", item)})
    if source_mode == "both": active_filters.append({"label": "Nur DÖE + TED", "url": without_filter("source_mode")})
    if bookmarked: active_filters.append({"label": "Gemerkte Projekte", "url": without_filter("bookmarked")})
    if below_threshold: active_filters.append({"label": "Unterschwelle", "url": without_filter("below_threshold")})
    for item in active_statuses:
        active_filters.append({"label": STATUS_LABELS.get(item, item), "url": without_filter("status", item)})
    return templates.TemplateResponse(request, "index.html", {
        "notices": notices, "total": total, "types": types, "filters": filters, "taxonomy": taxonomy_for_template(), "service_labels": service_labels(), "active_filters": active_filters,
        "status_labels": STATUS_LABELS, "status_counts": status_counts, "bookmark_count": bookmark_count,
        "bookmark_toggle_url": filters_url({**filters, "bookmarked": not bookmarked}),
        "return_to": request.url.path + (f"?{request.url.query}" if request.url.query else ""),
        "pagination": {"page": page, "page_count": page_count, "previous_url": page_url(page - 1) if page > 1 else None, "next_url": page_url(page + 1) if page < page_count else None, "links": [(number, page_url(number)) if number else (None, None) for number in _page_links(page, page_count)], "from": (page - 1) * page_size + 1 if total else 0, "to": min(page * page_size, total)},
    })


@app.post("/clusters/{cluster_id}/bookmark")
def bookmark_cluster(
    cluster_id: int,
    action: str = Form(),
    note: str = Form(default=""),
    return_to: str = Form(default="/"),
) -> RedirectResponse:
    with SessionLocal.begin() as session:
        cluster = session.get(NoticeCluster, cluster_id)
        if not cluster:
            raise HTTPException(404)
        if action == "toggle":
            if cluster.bookmarked_at:
                cluster.bookmarked_at = None
                cluster.bookmark_note = None
            else:
                cluster.bookmarked_at = datetime.now(timezone.utc)
        elif action == "save":
            cluster.bookmarked_at = datetime.now(timezone.utc)
            cluster.bookmark_note = note.strip() or None
        elif action == "remove":
            cluster.bookmarked_at = None
            cluster.bookmark_note = None
        else:
            raise HTTPException(400, "Ungültige Merkliste-Aktion")
    parsed = urlparse(return_to)
    target = parsed.path if parsed.path == "/" else "/"
    if parsed.query and target == "/":
        target += f"?{parsed.query}"
    return RedirectResponse(target, status_code=303)


@app.get("/clusters/{cluster_id}", response_class=HTMLResponse)
def detail(request: Request, cluster_id: int):
    with SessionLocal() as session:
        rows = session.query(NoticeCluster, Notice).join(NoticeClusterMember, NoticeClusterMember.cluster_id == NoticeCluster.id).join(Notice, Notice.id == NoticeClusterMember.notice_id).filter(NoticeCluster.id == cluster_id).all()
        if not rows: raise HTTPException(404)
        cluster = build_cluster_views(rows)[0]
    return templates.TemplateResponse(request, "detail.html", {"notice": cluster})

@app.post("/imports/{day}")
def run_import(day: date): return {"imported": import_day(day), "day": day}
@app.post("/imports/ted/{day}")
def run_ted_import(day: date): return {"imported": import_ted_day(day), "day": day, "source": "ted"}
@app.post("/reports/daily", response_class=PlainTextResponse)
def run_report() -> str: return str(write_daily_report())
@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}
