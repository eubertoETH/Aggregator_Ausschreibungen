import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://aggregator:aggregator@db:5432/aggregator")
REPORT_DIR = os.getenv("REPORT_DIR", "/data/reports")
RAW_ARCHIVE_DIR = os.getenv("RAW_ARCHIVE_DIR", "/data/raw")
DEFAULT_REPORT_DAYS = int(os.getenv("DEFAULT_REPORT_DAYS", "14"))
