import html
import re
from datetime import datetime

import feedparser

RSS_URL = "https://cqranking.com/men/xml/RSS_RecentRacesFull.xml"
OUTPUT_MD = "recent-races.md"
MAX_ITEMS = 12
FLAG_URL = "https://cqranking.com/common/flags/{code}.gif"

MEDALS = {"1": "🥇", "2": "🥈", "3": "🥉"}

# Matches "Date: 4 Aug 2026 - Category: 2.PSs"
DATE_CATEGORY_RE = re.compile(r"Date:\s*(?P<date>[^-]+?)\s*-\s*Category:\s*(?P<category>.+)")

# Matches "1. BRENNAN Matthew (GBR/TVL)" or "1. Veloce Club Rouen 76" (team result,
# no nationality/team-code suffix).
RESULT_LINE_RE = re.compile(
    r"^(?P<rank>\d+)\.\s*(?P<name>.+?)(?:\s*\((?P<nat>[A-Z]{2,4})/(?P<team>[A-Za-z0-9?]{2,4})\))?$"
)

# Matches "Leader: BRENNAN Matthew (GBR/TVL)"
LEADER_RE = re.compile(
    r"^Leader:\s*(?P<name>.+?)(?:\s*\((?P<nat>[A-Z]{2,4})/(?P<team>[A-Za-z0-9?]{2,4})\))?$"
)


def parse_description(raw_description):
    """
    Turn the RSS description blob (date/category + top results + optional
    leader, all mashed together with <br> tags) into structured fields:
    (date_str, category, results, leader) where results is a list of
    (rank, name, nation) tuples and leader is (name, nation) or None.
    Returns None fields / an empty list when a piece isn't found, so
    callers can fall back gracefully.
    """
    text = re.sub(r"<br\s*/?>", "\n", raw_description)
    text = re.sub(r"<[^>]+>", "", text)  # drop remaining tags, e.g. the <a> link
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    date_str, category = "", ""
    results = []
    leader = None

    for line in lines:
        m = DATE_CATEGORY_RE.match(line)
        if m:
            date_str = m.group("date").strip()
            category = m.group("category").strip()
            continue

        m = RESULT_LINE_RE.match(line)
        if m:
            results.append((m.group("rank"), m.group("name").strip(), m.group("nat")))
            continue

        m = LEADER_RE.match(line)
        if m:
            leader = (m.group("name").strip(), m.group("nat"))
            continue
        # Anything else (e.g. "Now on CQranking.com: Top 20") is ignored.

    return date_str, category, results, leader


def flag_img(nation):
    if not nation:
        return ""
    return f'<img class="flag" src="{FLAG_URL.format(code=nation)}" width="16">'


def render_card(entry):
    title = html.escape(entry.title.strip())
    link = entry.link.strip()
    pub_date = datetime(*entry.published_parsed[:6]).strftime("%d %b %Y")
    date_str, category, results, leader = parse_description(entry.description)

    parts = ['<div class="rss-card">']
    parts.append(f'<div class="rss-title"><a href="{link}" target="_blank">{title}</a></div>')

    meta_bits = [b for b in (date_str or pub_date, category) if b]
    if meta_bits:
        parts.append(f'<div class="rss-meta">{" · ".join(html.escape(b) for b in meta_bits)}</div>')

    if results:
        parts.append('<ol class="rss-results">')
        for rank, name, nation in results:
            medal = MEDALS.get(rank, f"{rank}.")
            parts.append(
                '<li>'
                f'<span class="rss-medal">{medal}</span>'
                f'{flag_img(nation)}'
                f'<span class="rss-rider">{html.escape(name)}</span>'
                '</li>'
            )
        parts.append("</ol>")
    else:
        # Fall back to the plain cleaned description if we couldn't
        # parse a structured result list out of it.
        fallback = re.sub(r"<br\s*/?>", "\n", entry.description)
        fallback = re.sub(r"<[^>]+>", "", fallback).strip()
        parts.append(f'<div class="rss-desc">{html.escape(fallback)}</div>')

    if leader:
        leader_name, leader_nat = leader
        parts.append(
            '<div class="rss-leader">'
            f'{flag_img(leader_nat)}'
            f'<strong>Leader:</strong> {html.escape(leader_name)}'
            "</div>"
        )

    parts.append("</div>")
    return "\n".join(parts)


feed = feedparser.parse(RSS_URL)

lines = ["## Risultati recenti\n", '<div class="rss-scroll">\n']

for entry in feed.entries[:MAX_ITEMS]:
    lines.append(render_card(entry))
    lines.append("")

lines.append("</div>")

with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
