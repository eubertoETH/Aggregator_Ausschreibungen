"""Small, dependency-free daily runner for the prototype."""
import logging
import time
from datetime import date, datetime, timedelta

from .importer import import_day
from .report import write_daily_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_once() -> None:
    # Re-read three completed export days: late corrections are safe due to versioned upserts.
    yesterday = date.today() - timedelta(days=1)
    for offset in range(3):
        imported = import_day(yesterday - timedelta(days=offset))
        logging.info("Imported %s notices for %s", imported, yesterday - timedelta(days=offset))
    logging.info("Wrote report: %s", write_daily_report())


def seconds_until_next_run() -> float:
    now = datetime.now()
    target = now.replace(hour=2, minute=15, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


if __name__ == "__main__":
    while True:
        time.sleep(seconds_until_next_run())
        try:
            run_once()
        except Exception:
            logging.exception("Daily import/report failed")
