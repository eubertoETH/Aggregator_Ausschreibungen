#!/usr/bin/env python3
"""Read-only TED Search API probe for validating the connector contract.

This is deliberately not a production importer: it fetches a small,
inspectable result page and prints the source identifiers and available
formats. It never writes to PostgreSQL or to the raw archive.
"""
import argparse
import json
from datetime import date
from urllib.request import Request, urlopen


TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"
FIELDS = [
    "publication-number",
    "procedure-identifier",
    "publication-date",
    "notice-type",
    "form-type",
    "notice-title",
    "buyer-name",
    "links",
]


def request_body(publication_day: date, country: str, limit: int) -> dict:
    return {
        "query": f"publication-date = {publication_day:%Y%m%d} AND place-of-performance-country-lot = {country.upper()}",
        "fields": FIELDS,
        "page": 1,
        "limit": limit,
        "scope": "ACTIVE",
    }


def fetch_probe(publication_day: date, country: str, limit: int) -> dict:
    body = json.dumps(request_body(publication_day, country, limit)).encode("utf-8")
    request = Request(TED_SEARCH_URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("day", type=date.fromisoformat, help="publication day, YYYY-MM-DD")
    parser.add_argument("--country", default="DEU", help="ISO-3166 alpha-3 performance country (default: DEU)")
    parser.add_argument("--limit", type=int, default=5, choices=range(1, 251), metavar="1..250")
    args = parser.parse_args()

    result = fetch_probe(args.day, args.country, args.limit)
    summary = {
        "query": request_body(args.day, args.country, args.limit)["query"],
        "total_notice_count": result.get("totalNoticeCount"),
        "notices": [
            {
                "publication_number": item.get("publication-number"),
                "procedure_identifier": item.get("procedure-identifier"),
                "notice_type": item.get("notice-type"),
                "title_languages": sorted((item.get("notice-title") or {}).keys()),
                "link_formats": sorted((item.get("links") or {}).keys()),
            }
            for item in result.get("notices", [])
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
