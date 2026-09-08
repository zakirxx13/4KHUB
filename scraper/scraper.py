import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SOURCE_URL = os.environ.get("SOURCE_URL", "").strip()
OUTPUT_FILE = Path("streams.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AuthorizedScraper/1.0)"
}


def fetch(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()
    return response.text


def scrape():
    if not SOURCE_URL:
        raise RuntimeError(
            "SOURCE_URL is not configured. "
            "Add SOURCE_URL in GitHub Actions Secrets."
        )

    html = fetch(SOURCE_URL)
    soup = BeautifulSoup(html, "html.parser")

    items = []

    for card in soup.select(".movie-card"):
        title_element = card.select_one(".title")

        if not title_element:
            continue

        title = title_element.get_text(
            " ",
            strip=True
        )

        link_element = card.select_one("a")

        url = ""

        if link_element:
            href = link_element.get("href")

            if href:
                url = urljoin(
                    SOURCE_URL,
                    href
                )

        items.append({
            "name": title,
            "url": url
        })

    return {
        "streams": items
    }


def save(data):
    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def main():
    try:
        data = scrape()

        save(data)

        print(
            f"Successfully scraped "
            f"{len(data['streams'])} items."
        )

        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as error:
        print(
            f"ERROR: {error}",
            file=sys.stderr
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
