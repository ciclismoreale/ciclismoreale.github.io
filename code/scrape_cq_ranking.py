import time

from cq_scrape_common import scrape_cq_ranking

# ---------------- CONFIG ----------------
YEAR = 2026
CURRENT = 0  # ranking at the beginning of the year
OUTPUT_CSV = "data/cqranking_riders.csv"
# ----------------------------------------

if __name__ == "__main__":
    t0 = time.time()
    df = scrape_cq_ranking(year=YEAR, current=CURRENT)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"Scraping complete. Saved {len(df)} riders in {time.time() - t0:.1f}s.")
