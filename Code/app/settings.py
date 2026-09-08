import os
from pathlib import Path
from urllib.parse import quote


def database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url
    password_file = os.getenv("POSTGRES_PASSWORD_FILE")
    if password_file:
        password = Path(password_file).read_text(encoding="utf-8").strip()
        if not password:
            raise RuntimeError("POSTGRES_PASSWORD_FILE is empty")
        host = os.getenv("POSTGRES_HOST", "db")
        name = os.getenv("POSTGRES_DB", "aggregator")
        user = os.getenv("POSTGRES_USER", "aggregator")
        return f"postgresql+psycopg://{quote(user)}:{quote(password)}@{host}:5432/{quote(name)}"
    return "postgresql+psycopg://aggregator:aggregator@db:5432/aggregator"


DATABASE_URL = database_url()
REPORT_DIR = os.getenv("REPORT_DIR", "/data/reports")
RAW_ARCHIVE_DIR = os.getenv("RAW_ARCHIVE_DIR", "/data/raw")
DEFAULT_REPORT_DAYS = int(os.getenv("DEFAULT_REPORT_DAYS", "14"))
TED_COUNTRY_CODE = os.getenv("TED_COUNTRY_CODE", "DEU").upper()
