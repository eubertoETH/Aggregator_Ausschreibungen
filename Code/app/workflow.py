"""User-facing tender workflow state derived from durable source facts."""
from datetime import datetime

STATUS_LABELS = {
    "more_than_7": "Mehr als 7 Tage",
    "one_to_7": "Noch 1–7 Tage",
    "expired": "Frist abgelaufen",
    "decided": "Entschieden",
    "unknown": "Frist unbekannt",
}


def deadline_status(deadline: datetime | None, source_types: list[str]) -> str:
    signals = " ".join(source_types).lower()
    tokens = {token.strip(".,;:/()[]") for token in signals.replace("-", " ").split()}
    # eForms CAN = contract award notice. Only explicit award/result forms are
    # considered decided; a past deadline alone remains 'expired'.
    if "can" in tokens or "contract award" in signals or "result" in tokens:
        return "decided"
    if deadline is None:
        return "unknown"
    now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
    remaining_days = (deadline - now).total_seconds() / 86400
    if remaining_days < 0:
        return "expired"
    if remaining_days <= 7:
        return "one_to_7"
    return "more_than_7"


def is_below_threshold(source_types: list[str]) -> bool:
    """Only return true for an explicit national/below-threshold source cue."""
    signals = " ".join(source_types).lower()
    return any(item in signals for item in ("unterschwelle", "below-threshold", "national"))
