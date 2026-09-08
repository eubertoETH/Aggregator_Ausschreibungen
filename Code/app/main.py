from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_

from .cluster_views import build_cluster_views
from .database import SessionLocal
from .importer import import_day
from .models import Notice, NoticeCluster, NoticeClusterMember
from .report import write_daily_report
from .ted_importer import import_ted_day

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Ausschreibungsaggregator")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
PROFILE_TAGS = ["architektur / planung", "bestand", "sanierung", "fassade", "energie"]


@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: str = "", tag: list[str] = Query(default=[]), cpv: str = "", region: str = "", notice_type: str = "", scope: str = "profile", days: int = 30, page: int = 1):
    with SessionLocal() as session:
        query = session.query(NoticeCluster, Notice).join(NoticeClusterMember, NoticeClusterMember.cluster_id == NoticeCluster.id).join(Notice, Notice.id == NoticeClusterMember.notice_id)
        if scope == "profile":
            query = query.filter(Notice.tags.overlap(PROFILE_TAGS))
        if q:
            needle = f"%{q}%"
            query = query.filter(or_(Notice.search_vector.op("@@")(func.websearch_to_tsquery("german", q)), Notice.buyer_name.ilike(needle), Notice.city.ilike(needle)))
        if tag:
            query = query.filter(Notice.tags.overlap(tag))
        if cpv:
            query = query.filter(Notice.cpv_codes.any(cpv))
        if region:
            query = query.filter(Notice.nuts_region.ilike(f"{region}%"))
        if notice_type:
            query = query.filter(Notice.notice_type == notice_type)
        if days:
            from datetime import timedelta
            query = query.filter(Notice.publication_date >= date.today() - timedelta(days=days))
        clusters = build_cluster_views(query.order_by(Notice.submission_deadline.asc().nullslast(), Notice.participation_deadline.asc().nullslast(), Notice.publication_date.desc()).all())
        total = len(clusters)
        notices = clusters[(page - 1) * 50:page * 50]
        tags = [row[0] for row in session.query(Notice.tags).distinct().all() for row in (row[0] or [])]
        types = [row[0] for row in session.query(Notice.notice_type).distinct().order_by(Notice.notice_type).all() if row[0]]
    return templates.TemplateResponse(request, "index.html", {"notices": notices, "total": total, "tags": sorted(set(tags)), "types": types, "filters": {"q": q, "tag": tag, "cpv": cpv, "region": region, "notice_type": notice_type, "scope": scope, "days": days}})


@app.get("/clusters/{cluster_id}", response_class=HTMLResponse)
def detail(request: Request, cluster_id: int):
    with SessionLocal() as session:
        rows = session.query(NoticeCluster, Notice).join(NoticeClusterMember, NoticeClusterMember.cluster_id == NoticeCluster.id).join(Notice, Notice.id == NoticeClusterMember.notice_id).filter(NoticeCluster.id == cluster_id).all()
        if not rows:
            raise HTTPException(404)
        cluster = build_cluster_views(rows)[0]
    return templates.TemplateResponse(request, "detail.html", {"notice": cluster})


@app.post("/imports/{day}")
def run_import(day: date):
    return {"imported": import_day(day), "day": day}


@app.post("/imports/ted/{day}")
def run_ted_import(day: date):
    return {"imported": import_ted_day(day), "day": day, "source": "ted"}


@app.post("/reports/daily", response_class=PlainTextResponse)
def run_report() -> str:
    return str(write_daily_report())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
