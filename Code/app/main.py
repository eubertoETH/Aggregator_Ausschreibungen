from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
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
    page: int = 1, page_size: int = 50,
):
    page_size = page_size if page_size in {25, 50, 75, 100} else 50
    radius = radius if radius in {*RADIUS_KM, 0} else 75
    page = max(page, 1)
    with SessionLocal() as session:
        rows = session.query(NoticeCluster, Notice).join(NoticeClusterMember, NoticeClusterMember.cluster_id == NoticeCluster.id).join(Notice, Notice.id == NoticeClusterMember.notice_id).all()
        clusters = build_cluster_views(rows)
        filtered = []
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
            filtered.append(item)
        total = len(filtered)
        page_count = max(1, (total + page_size - 1) // page_size)
        page = min(page, page_count)
        notices = filtered[(page - 1) * page_size:page * page_size]
        types = [row[0] for row in session.query(Notice.notice_type).distinct().order_by(Notice.notice_type).all() if row[0]]

    filters = {"q": q, "service": service, "object_type": object_type, "source": source, "source_mode": source_mode, "cpv": cpv, "region": region, "notice_type": notice_type, "scope": scope, "days": days, "radius": radius, "page_size": page_size}
    def page_url(target: int) -> str:
        params = [(key, str(value)) for key, value in filters.items() if key not in {"service", "object_type", "source"}]
        params.append(("page", str(target)))
        for key in ("service", "object_type", "source"):
            params.extend((key, value) for value in filters[key])
        return "?" + urlencode(params)
    return templates.TemplateResponse(request, "index.html", {
        "notices": notices, "total": total, "types": types, "filters": filters, "taxonomy": taxonomy_for_template(), "service_labels": service_labels(),
        "pagination": {"page": page, "page_count": page_count, "previous_url": page_url(page - 1) if page > 1 else None, "next_url": page_url(page + 1) if page < page_count else None, "links": [(number, page_url(number)) if number else (None, None) for number in _page_links(page, page_count)], "from": (page - 1) * page_size + 1 if total else 0, "to": min(page * page_size, total)},
    })


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
