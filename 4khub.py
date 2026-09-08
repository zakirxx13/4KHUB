import json
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# ============================================================
# CONFIG
# ============================================================

# নিজের / অনুমোদিত source URL
SOURCE_URL = "https://YOUR-OWN-SITE.example"

# TMDB API key এখানে বসাতে পারো
TMDB_API_KEY = "YOUR_TMDB_API_KEY"

TMDB_URL = "https://api.themoviedb.org/3"

OUTPUT_FILE = "output.json"


# ============================================================
# TMDB
# ============================================================

def tmdb_search(title):
    if not TMDB_API_KEY or TMDB_API_KEY == "YOUR_TMDB_API_KEY":
        print("TMDB API key not configured")
        return []

    response = requests.get(
        f"{TMDB_URL}/search/multi",
        params={
            "api_key": TMDB_API_KEY,
            "query": title,
            "include_adult": "false",
            "language": "en-US"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("results", []):
        media_type = item.get("media_type")

        if media_type not in ["movie", "tv"]:
            continue

        name = (
            item.get("title")
            or item.get("name")
            or ""
        )

        date = (
            item.get("release_date")
            or item.get("first_air_date")
            or ""
        )

        results.append({
            "tmdb_id": item.get("id"),
            "type": media_type,
            "title": name,
            "year": date[:4] if date else "",
            "overview": item.get("overview", ""),
            "rating": item.get("vote_average", 0)
        })

    return results


# ============================================================
# PLAYWRIGHT
# ============================================================

def playwright_scrape():
    print("[Playwright] Starting...")

    results = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        page.goto(
            SOURCE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(2000)

        cards = page.locator(".movie-card")

        count = cards.count()

        print(
            f"[Playwright] Found {count} cards"
        )

        for i in range(count):

            card = cards.nth(i)

            try:
                title = card.locator(
                    ".title"
                ).inner_text().strip()
            except Exception:
                continue

            try:
                href = card.locator(
                    "a"
                ).get_attribute("href")
            except Exception:
                href = ""

            results.append({
                "title": title,
                "url": href or ""
            })

        browser.close()

    return results


# ============================================================
# SELENIUM
# ============================================================

def selenium_scrape():
    print("[Selenium] Starting...")

    options = Options()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "--window-size=1920,1080"
    )

    driver = webdriver.Chrome(
        options=options
    )

    results = []

    try:

        driver.get(SOURCE_URL)

        time.sleep(3)

        elements = driver.find_elements(
            "css selector",
            ".movie-card"
        )

        print(
            f"[Selenium] Found {len(elements)} cards"
        )

        for element in elements:

            try:
                title = element.find_element(
                    "css selector",
                    ".title"
                ).text.strip()
            except Exception:
                continue

            try:
                link = element.find_element(
                    "css selector",
                    "a"
                ).get_attribute("href")
            except Exception:
                link = ""

            results.append({
                "title": title,
                "url": link or ""
            })

    finally:

        driver.quit()

    return results


# ============================================================
# TMDB MATCH
# ============================================================

def attach_tmdb(items):

    final_items = []

    for item in items:

        title = item.get(
            "title",
            ""
        ).strip()

        if not title:
            continue

        print(
            f"[TMDB] Searching: {title}"
        )

        try:

            matches = tmdb_search(title)

        except Exception as error:

            print(
                f"[TMDB] Error: {error}"
            )

            matches = []

        best = (
            matches[0]
            if matches
            else {}
        )

        final_items.append({
            "title": title,
            "url": item.get("url", ""),
            "tmdb": best
        })

    return final_items


# ============================================================
# MAIN
# ============================================================

def main():

    if (
        not SOURCE_URL
        or "YOUR-OWN-SITE" in SOURCE_URL
    ):
        print(
            "ERROR: Set SOURCE_URL first."
        )
        sys.exit(1)

    print("=" * 60)
    print("4KHUB PYTHON SCRAPER")
    print("=" * 60)

    # Playwright
    try:
        playwright_items = playwright_scrape()
    except Exception as error:
        print(
            f"[Playwright] ERROR: {error}"
        )
        playwright_items = []

    # Selenium
    try:
        selenium_items = selenium_scrape()
    except Exception as error:
        print(
            f"[Selenium] ERROR: {error}"
        )
        selenium_items = []

    # Combine
    combined = (
        playwright_items
        + selenium_items
    )

    # Remove duplicates
    unique = {}

    for item in combined:

        key = (
            item.get("title", "")
            .strip()
            .lower()
        )

        if key and key not in unique:
            unique[key] = item

    items = list(
        unique.values()
    )

    print(
        f"Unique items: {len(items)}"
    )

    # TMDB
    items = attach_tmdb(items)

    output = {
        "success": True,
        "count": len(items),
        "items": items
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Created {OUTPUT_FILE}"
    )

    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        print("Stopped.")
        sys.exit(1)

    except Exception as error:

        print(
            f"FATAL ERROR: {error}",
            file=sys.stderr
        )

        sys.exit(1)
