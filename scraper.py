import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = os.getenv(
    "SOURCE_URL",
    "https://4khdhub.one/"
)

OUTPUT_FILE = Path("streams.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AuthorizedScraper/1.0)"
}


def fetch_page(url: str) -> str:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()
    return response.text


def scrape():
    html = fetch_page(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    results = []

    # নিজের সাইটের HTML অনুযায়ী selector পরিবর্তন করো
    for card in soup.select(".movie-card"):
        title_element = card.select_one(".title")

        if not title_element:
            continue

        title = title_element.get_text(" ", strip=True)

        link_element = card.select_one("a")

        url = ""
        if link_element:
            url = link_element.get("href", "")

        results.append({
            "name": title,
            "url": url
        })

    return {
        "streams": results
    }


def main():
    try:
        data = scrape()

        OUTPUT_FILE.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print(
            f"Scraped {len(data['streams'])} items"
        )

        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as exc:
        print(f"Scraper failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
