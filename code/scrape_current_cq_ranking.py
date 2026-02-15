from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# ---------------- CONFIG ----------------
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
PAGE_SIZE = 100
MAX_RIDERS = 5000
BASE_URL = "https://cqranking.com/men/asp/gen/cqRankingRider.asp?year=2026&current=1&start={}"
# ----------------------------------------

# Chrome setup
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

all_data = []
headers = []

start_rank = 1      # Pagination offset for URL
total_rank = 1      # Continuous rank across pages

while total_rank <= MAX_RIDERS:
    url = BASE_URL.format(start_rank)
    print(f"Scraping page starting at rank {total_rank} (URL start={start_rank})...")
    driver.get(url)

    try:
        table = wait.until(
            EC.presence_of_element_located((By.XPATH, "//table[.//th[text()='Rank']]"))
        )
    except:
        print("No table found. Stopping.")
        break

    if not headers:
        ths = table.find_elements(By.XPATH, ".//tr[1]/th")
        headers = [th.text.strip() for th in ths if th.text.strip()]
        headers.insert(2, "Country Flag")  # Insert after "Prev." column

    rows = table.find_elements(By.XPATH, ".//tr")[1:]  # Skip header row
    if not rows:
        print("No rows found on page. Stopping.")
        break

    page_data = []

    for row in rows:
        cells = row.find_elements(By.XPATH, ".//th|.//td")
        if not cells:
            continue

        row_data = []
        flag_url = ""

        for c in cells:
            img = c.find_elements(By.TAG_NAME, "img")
            if img:
                flag_url = img[0].get_attribute("src")
                continue
            text = c.text.strip()
            if text:
                row_data.append(text)

        if not row_data:
            continue

        row_data[0] = str(total_rank)
        # Insert flag
        row_data.insert(2, flag_url)

        # Normalize row length
        if len(row_data) < len(headers):
            row_data += [""] * (len(headers) - len(row_data))
        elif len(row_data) > len(headers):
            row_data = row_data[:len(headers)]

        page_data.append(row_data)
        total_rank += 1

        # Stop if MAX_RIDERS reached
        if total_rank > MAX_RIDERS:
            break

    all_data.extend(page_data)
    start_rank += PAGE_SIZE  # next page
    time.sleep(0.01)

driver.quit()

df = pd.DataFrame(all_data, columns=headers)
df.to_csv("data/current_cqranking_riders.csv", index=False, encoding="utf-8")
print(f"Scraping complete. Saved {len(df)} riders.")
