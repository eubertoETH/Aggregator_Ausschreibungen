"""Read models for one user-visible procurement procedure per cluster."""
from collections import defaultdict
from dataclasses import dataclass

from .models import Notice, NoticeCluster
from .workflow import deadline_status, is_below_threshold

SOURCE_PRIORITY = {"doe": 0, "ted": 1}


@dataclass
class ClusterView:
    cluster: NoticeCluster
    notices: list[Notice]

    def _ordered(self) -> list[Notice]:
        return sorted(
            self.notices,
            key=lambda notice: (SOURCE_PRIORITY.get(notice.source_code, 99), notice.imported_at),
            reverse=False,
        )

    def _value(self, field: str):
        return next((value for notice in self._ordered() if (value := getattr(notice, field)) not in (None, "", [])), None)

    @property
    def id(self) -> int:
        return self.cluster.id

    @property
    def title(self): return self._value("title")
    @property
    def description(self): return self._value("description")
    @property
    def buyer_name(self): return self._value("buyer_name")
    @property
    def city(self): return self._value("city")
    @property
    def nuts_region(self): return self._value("nuts_region")
    @property
    def publication_date(self): return self._value("publication_date")
    @property
    def notice_type(self): return self._value("notice_type")
    @property
    def procedure_type(self): return self._value("procedure_type")
    @property
    def estimated_value(self): return self._value("estimated_value")
    @property
    def currency(self): return self._value("currency")
    @property
    def submission_deadline(self): return self._value("submission_deadline")
    @property
    def participation_deadline(self): return self._value("participation_deadline")
    @property
    def cpv_codes(self): return sorted({code for notice in self.notices for code in (notice.cpv_codes or [])})
    @property
    def tags(self): return sorted({tag for notice in self.notices for tag in (notice.tags or [])})
    @property
    def service_categories(self): return sorted({code for notice in self.notices for code in (notice.service_categories or [])})
    @property
    def object_types(self): return sorted({code for notice in self.notices for code in (notice.object_types or [])})
    @property
    def classification_reasons(self):
        result = {}
        for notice in self._ordered():
            result.update(notice.classification_reasons or {})
        return result
    @property
    def procedure_identifier(self): return self._value("procedure_identifier") or self.cluster.procedure_identifier
    @property
    def deadline(self): return self.participation_deadline or self.submission_deadline
    @property
    def status(self): return deadline_status(self.deadline, [(notice.notice_type or "") + " " + (notice.form_type or "") for notice in self.notices])
    @property
    def is_below_threshold(self): return is_below_threshold([(notice.notice_type or "") + " " + (notice.form_type or "") for notice in self.notices])
    @property
    def bookmarked(self): return self.cluster.bookmarked_at is not None
    @property
    def bookmark_note(self): return self.cluster.bookmark_note
    @property
    def source_codes(self): return sorted({notice.source_code for notice in self.notices})
    @property
    def source_links(self):
        return [(notice.source_code, notice.notice_url) for notice in self._ordered() if notice.notice_url]
    @property
    def notice_url(self): return next((link for _, link in self.source_links), None)
    @property
    def has_conflicts(self) -> bool:
        fields = ("title", "buyer_name", "city", "submission_deadline", "participation_deadline", "estimated_value")
        return any(len({getattr(notice, field) for notice in self.notices if getattr(notice, field) not in (None, "")}) > 1 for field in fields)


def build_cluster_views(rows: list[tuple[NoticeCluster, Notice]]) -> list[ClusterView]:
    grouped: dict[int, tuple[NoticeCluster, list[Notice]]] = {}
    for cluster, notice in rows:
        item = grouped.setdefault(cluster.id, (cluster, []))
        item[1].append(notice)
    views = [ClusterView(cluster=cluster, notices=notices) for cluster, notices in grouped.values()]
    return sorted(
        views,
        key=lambda item: (
            item.participation_deadline is None and item.submission_deadline is None,
            (item.participation_deadline or item.submission_deadline or item.publication_date).isoformat()
            if item.participation_deadline or item.submission_deadline or item.publication_date else "",
        ),
    )
