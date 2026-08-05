"""
Shared scraping logic for cqranking.com rider ranking tables.

Replaces the old Selenium/ChromeDriver-based scraping (which loaded a full
headless browser to read a plain, server-rendered HTML table) with plain
HTTP requests + BeautifulSoup. Same output CSV schema as before:

    Rank, Prev., Country Flag, Rider, Team, Date of birth, CQ
"""

import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "https://cqranking.com/men/asp/gen/cqRankingRider.asp"
PAGE_SIZE = 100
MAX_RIDERS = 5000
REQUEST_TIMEOUT = 20
RETRIES = 3
SLEEP_BETWEEN_REQUESTS = 0.3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 CiclismoRealeBot"
    )
}


def _fetch_page(session, year, current, start):
    params = {"year": year, "current": current, "start": start}
    last_exc = None
    for attempt in range(RETRIES):
        try:
            resp = session.get(
                BASE_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            # Return the final URL too (after redirects) so relative links
            # (e.g. root-relative flag image src="/common/flags/XXX.gif")
            # can be resolved to absolute URLs, the way a browser/Selenium
            # would when reading element.src.
            return resp.text, resp.url
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(1 + attempt)
    raise last_exc


def _find_ranking_table(soup):
    """Find the table whose header row contains a 'Rank' column."""
    for table in soup.find_all("table"):
        first_row = table.find("tr")
        if not first_row:
            continue
        th_texts = [th.get_text(strip=True) for th in first_row.find_all("th")]
        if "Rank" in th_texts:
            return table
    return None


def scrape_cq_ranking(year, current, max_riders=MAX_RIDERS, page_size=PAGE_SIZE):
    """
    Scrape the CQ ranking rider table.

    year:    ranking year, e.g. 2026
    current: 0 = ranking at start of year, 1 = current in-progress ranking
    """
    session = requests.Session()
    all_data = []
    headers = []

    start_rank = 1
    total_rank = 1

    while total_rank <= max_riders:
        print(f"Scraping page starting at rank {total_rank} (start={start_rank})...")
        html, page_url = _fetch_page(session, year, current, start_rank)
        soup = BeautifulSoup(html, "lxml")
        table = _find_ranking_table(soup)

        if table is None:
            print("No table found. Stopping.")
            break

        rows = table.find_all("tr")[1:]  # skip header row
        if not rows:
            print("No rows found on page. Stopping.")
            break

        if not headers:
            header_ths = table.find("tr").find_all("th")
            headers = [th.get_text(strip=True) for th in header_ths if th.get_text(strip=True)]
            headers.insert(2, "Country Flag")

        page_data = []
        for row in rows:
            cells = row.find_all(["th", "td"])
            if not cells:
                continue

            row_data = []
            flag_url = ""

            for c in cells:
                img = c.find("img")
                if img:
                    src = img.get("src", "")
                    flag_url = urljoin(page_url, src) if src else ""
                    continue
                text = c.get_text(strip=True)
                if text:
                    row_data.append(text)

            if not row_data:
                continue

            # Replace scraped rank with a continuous rank across pages
            row_data[0] = str(total_rank)
            # Insert flag URL where the old Selenium scraper put it
            row_data.insert(2, flag_url)

            # Normalize row length to header length
            if len(row_data) < len(headers):
                row_data += [""] * (len(headers) - len(row_data))
            elif len(row_data) > len(headers):
                row_data = row_data[: len(headers)]

            page_data.append(row_data)
            total_rank += 1

            if total_rank > max_riders:
                break

        if not page_data:
            print("No parsable rows on page. Stopping.")
            break

        all_data.extend(page_data)
        start_rank += page_size
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    return pd.DataFrame(all_data, columns=headers)
