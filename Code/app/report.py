from datetime import date, timedelta
from pathlib import Path

from .cluster_views import build_cluster_views
from .database import SessionLocal
from .models import Notice, NoticeCluster, NoticeClusterMember
from .settings import DEFAULT_REPORT_DAYS, REPORT_DIR


def write_daily_report(days: int = DEFAULT_REPORT_DAYS) -> Path:
    today = date.today()
    with SessionLocal() as session:
        rows = session.query(NoticeCluster, Notice).join(NoticeClusterMember, NoticeClusterMember.cluster_id == NoticeCluster.id).join(Notice, Notice.id == NoticeClusterMember.notice_id).filter(Notice.publication_date >= today - timedelta(days=days)).all()
        notices = build_cluster_views(rows)
    relevant = [item for item in notices if item.tags or any(code.startswith(("712", "7132", "714", "7153", "7154")) for code in item.cpv_codes)]
    lines = [f"# Ausschreibungsreport – {today.isoformat()}", "", f"Neue Bekanntmachungen der letzten {days} Tage: **{len(notices)}**", f"Planungs-/Bestands-/Sanierungs-/Fassaden-Treffer: **{len(relevant)}**", ""]
    for item in relevant:
        tags = f" · {', '.join(item.tags)}" if item.tags else ""
        closing = item.participation_deadline or item.submission_deadline
        closing_text = f" · Frist: {closing.strftime('%d.%m.%Y %H:%M') if closing else 'nicht angegeben'}"
        lines.extend([f"## {item.title or 'Ohne Titel'}", f"{item.buyer_name or 'Auftraggeber unbekannt'} · {item.city or item.nuts_region or 'Ort unbekannt'} · {item.publication_date}{tags}{closing_text}"])
        for source_code, notice_url in item.source_links:
            lines.append(f"[Bekanntmachung ({source_code.upper()})]({notice_url})")
        lines.append("")
    target = Path(REPORT_DIR)
    target.mkdir(parents=True, exist_ok=True)
    report = target / f"report-{today.isoformat()}.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report
