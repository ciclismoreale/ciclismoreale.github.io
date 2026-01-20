import feedparser
from datetime import datetime
import re

RSS_URL = "https://cqranking.com/men/xml/RSS_RecentRacesFull.xml"
OUTPUT_MD = "recent-races.md"
MAX_ITEMS = 12

feed = feedparser.parse(RSS_URL)

def clean_html(text):
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

lines = []

# Section title
lines.append("## Risultati recenti\n")
lines.append('<div class="rss-scroll">\n')

for entry in feed.entries[:MAX_ITEMS]:
    title = entry.title.strip()
    link = entry.link.strip()
    pub_date = datetime(*entry.published_parsed[:6]).strftime("%d %b %Y")
    description = clean_html(entry.description)

    lines.append('<div class="rss-card">')
    lines.append(f'<div class="rss-title"><a href="{link}" target="_blank">{title}</a></div>')
    lines.append(f'<div class="rss-date">{pub_date}</div>')
    lines.append(f'<div class="rss-desc">{description}</div>')  # Removed <pre> for cleaner styling
    lines.append('</div>\n')


lines.append("</div>")

with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
