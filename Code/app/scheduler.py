"""Small, dependency-free daily runner for the prototype."""
import logging
import time
from datetime import date, datetime, timedelta

from .importer import import_day
from .report import write_daily_report
from .ted_importer import import_ted_day

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_once() -> None:
    yesterday = date.today() - timedelta(days=1)
    # Each source remains operationally independent. A TED outage must not
    # suppress the German DÖE feed or its report.
    for source_name, import_day_for_source in (("DÖE", import_day), ("TED", import_ted_day)):
        try:
            for offset in range(3):
                target_day = yesterday - timedelta(days=offset)
                imported = import_day_for_source(target_day)
                logging.info("%s imported %s notices for %s", source_name, imported, target_day)
        except Exception:
            logging.exception("%s import failed; continuing with remaining sources", source_name)
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
