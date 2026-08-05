"""
Shared helpers for looking up a rider's upcoming race program on
ProCyclingStats (procyclingstats.com), starting from the rider-name
format used in our own CQranking data ("LASTNAME(S) Firstname(s)",
surname fully upper-case).

Name matching between CQranking and ProCyclingStats is not
guaranteed: transliteration, middle names, and hyphenation can differ
between the two sites. Per the simple approach we agreed on: build one
best-guess slug per rider, and if ProCyclingStats doesn't have a page
for it, skip that rider entirely rather than trying to fuzzy-match.
"""

import re
import time
import unicodedata
from datetime import date

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.procyclingstats.com/rider/{slug}/calendar"
REQUEST_TIMEOUT = 20
RETRIES = 3
SLEEP_BETWEEN_REQUESTS = 0.4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 CiclismoRealeBot"
    )
}

# Letters that don't decompose into base+accent via NFKD and so need an
# explicit mapping to their closest ASCII equivalent (matches how
# ProCyclingStats builds its own slugs, e.g. "Søren" -> "soren").
_CHAR_MAP = {
    "ø": "o", "Ø": "o",
    "å": "a", "Å": "a",
    "æ": "ae", "Æ": "ae",
    "ð": "d", "Đ": "d", "đ": "d",
    "þ": "th", "Þ": "th",
    "ß": "ss",
    "ł": "l", "Ł": "l",
}


def _strip_accents(text):
    for src, dst in _CHAR_MAP.items():
        text = text.replace(src, dst)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _slug_part(text):
    text = _strip_accents(text).lower()
    text = text.replace("'", "-")
    text = re.sub(r"[^a-z0-9\-\s]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _split_name_words(rider_name):
    """
    Split a CQranking-format name ("VAN DER POEL Mathieu", "POGACAR
    Tadej" -- surname fully upper-case, given name(s) title case) into
    (surname_words, given_words), based on the leading run of
    all-uppercase words.
    """
    words = rider_name.split()
    surname_words = []
    given_words = []
    seen_given = False

    for w in words:
        letters = [c for c in w if c.isalpha()]
        is_upper_word = bool(letters) and all(c.isupper() for c in letters)
        if is_upper_word and not seen_given:
            surname_words.append(w)
        else:
            seen_given = True
            given_words.append(w)

    return surname_words, given_words


def surname(rider_name):
    """
    Best-guess surname only, in its original casing (e.g. "VAN DER
    POEL"). Falls back to the full name unchanged if it doesn't look
    like the expected "SURNAME(S) Given name(s)" shape.
    """
    surname_words, given_words = _split_name_words(rider_name)
    if not surname_words or not given_words:
        return rider_name
    return " ".join(surname_words)


def name_to_slug(rider_name):
    """
    rider_name: CQranking format, e.g. "VAN DER POEL Mathieu" or
    "POGACAR Tadej" (surname fully upper-case, given name(s) title
    case). Returns a best-guess ProCyclingStats slug
    ("firstname-lastname"), or None if the name can't be split.
    """
    surname_words, given_words = _split_name_words(rider_name)

    if not surname_words or not given_words:
        return None

    surname_slug = "-".join(p for p in (_slug_part(w) for w in surname_words) if p)
    given_slug = "-".join(p for p in (_slug_part(w) for w in given_words) if p)

    if not surname_slug or not given_slug:
        return None

    return f"{given_slug}-{surname_slug}"


def _normalize_date(date_text, today=None):
    """
    ProCyclingStats' "Upcoming program" table shows dates as "DD.MM"
    (no year, since the table only covers the near future). Convert
    to ISO "YYYY-MM-DD" so downstream sorting/formatting doesn't have
    to guess at the format. Falls back to the raw text unchanged if
    it doesn't match the expected shape (defensive -- this is scraped
    HTML, not a documented API).
    """
    if today is None:
        today = date.today()

    text = (date_text or "").strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?$", text)
    if not m:
        return date_text

    day, month = int(m.group(1)), int(m.group(2))
    year_group = m.group(3)

    if year_group:
        year = int(year_group)
        if year < 100:
            year += 2000
    else:
        year = today.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            return date_text
        # The table only lists *upcoming* races. A month/day that's
        # already well behind today's date is almost certainly next
        # year's edition rather than a stale one from earlier this
        # year (e.g. seeing "05.01" in November).
        if candidate < today.replace(day=1):
            year += 1

    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return date_text




def fetch_program(session, slug):
    """
    Fetch the "Upcoming program" table for a rider slug.

    Returns a list of dicts {date, race, class, url} (possibly empty,
    if the rider has no upcoming races on file), or None if
    ProCyclingStats has no rider page for this slug at all.
    """
    url = BASE_URL.format(slug=slug)
    last_exc = None
    resp = None
    for attempt in range(RETRIES):
        try:
            resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(1 + attempt)
    else:
        raise last_exc

    soup = BeautifulSoup(resp.text, "lxml")

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    if "page not found" in title_text.lower() or not title_text.lower().startswith("program for"):
        return None

    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if not header_row:
            continue
        header_cells = [c.get_text(strip=True) for c in header_row.find_all(["th", "td"])]
        if header_cells and header_cells[0].strip().lower() == "date":
            program = []
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                date_text = cells[0].get_text(strip=True)
                race_link = cells[1].find("a")
                if not date_text or not race_link:
                    continue
                race_name = race_link.get_text(strip=True)
                href = race_link.get("href", "")
                # PCS's race links always target a top-level "/race/..."
                # page (whatever sub-page that is -- overview, startlist,
                # statistics -- varies by race type/status, and we keep
                # that exactly as scraped rather than guessing at it).
                # The href itself is often written relative *without* a
                # leading slash (e.g. "race/gp-quebec/2026/statistics").
                # Resolving that against the current page's own URL
                # (urljoin(resp.url, href)) is wrong here -- it gets
                # nested under "/rider/<slug>/...", since the calendar
                # page itself isn't a real directory. Anchor directly to
                # the site root instead, which matches how these links
                # actually resolve on PCS regardless of a leading slash.
                if not href:
                    race_url = ""
                elif href.startswith("http://") or href.startswith("https://"):
                    race_url = href
                else:
                    race_url = "https://www.procyclingstats.com/" + href.lstrip("/")
                race_class = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                program.append(
                    {
                        "date": _normalize_date(date_text),
                        "race": race_name,
                        "class": race_class,
                        "url": race_url,
                    }
                )
            return program

    # Page existed (title checked out) but no "Date/Race/Class" table
    # was found -- treat as "no upcoming races" rather than an error.
    return []
