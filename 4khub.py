import asyncio
import json
import os
import sys

import requests
from playwright.async_api import async_playwright


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SOURCE_URL = os.environ.get("SOURCE_URL", "").strip()
TMDB_TOKEN = os.environ.get("TMDB_TOKEN", "").strip()

TMDB_BASE = "https://api.themoviedb.org/3"


# --------------------------------------------------
# TMDB
# --------------------------------------------------

def tmdb_search(query):
    if not TMDB_TOKEN:
        raise RuntimeError("TMDB_TOKEN is missing")

    response = requests.get(
        f"{TMDB_BASE}/search/multi",
        params={
            "query": query,
            "language": "en-US",
            "include_adult": "false",
        },
        headers={
            "Authorization": f"Bearer {TMDB_TOKEN}",
            "accept": "application/json",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("results", []):
        media_type = item.get("media_type")

        if media_type not in ("movie", "tv"):
            continue

        results.append({
            "tmdb_id": item.get("id"),
            "type": media_type,
            "title": (
                item.get("title")
                or item.get("name")
                or ""
            ),
            "year": (
                item.get("release_date", "")[:4]
                or item.get("first_air_date", "")[:4]
            ),
        })

    return results


# --------------------------------------------------
# PLAYWRIGHT
# --------------------------------------------------

async def scrape_page():

    if not SOURCE_URL:
        raise RuntimeError(
            "SOURCE_URL is missing"
        )

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131 Safari/537.36"
            )
        )

        await page.goto(
            SOURCE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(2000)

        results = await page.locator(
            ".movie-card"
        ).evaluate_all(
            """
            cards => cards.map(card => {
                const title =
                    card.querySelector(".title");

                const link =
                    card.querySelector("a");

                return {
                    name: title
                        ? title.textContent.trim()
                        : "",
                    url: link
                        ? link.href
                        : ""
                };
            })
            """
        )

        await browser.close()

        return results


# --------------------------------------------------
# MAIN
# --------------------------------------------------

async def main():

    print("Starting scraper...")

    items = await scrape_page()

    print(
        f"Found {len(items)} items"
    )

    output = {
        "items": items
    }

    with open(
        "output.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("output.json created")


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except Exception as error:

        print(
            f"ERROR: {error}",
            file=sys.stderr
        )

        sys.exit(1)
