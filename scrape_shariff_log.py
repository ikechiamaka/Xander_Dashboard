from playwright.sync_api import sync_playwright
import json
import csv
import os
from datetime import datetime, timezone

URL = "https://mcso.countyofmonterey.gov/daily-patrol-log"
DATA_DIR = "data"
LOG_FILE = os.path.join(DATA_DIR, "sheriff_log_history.csv")
FIELDNAMES = ["rptNumb", "date", "time", "charges", "location", "officer", "notes", "suspects", "victims", "pulled_at"]


def scrape_sheriff_log():
    captured_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # non-headless confirmed to get past Akamai earlier
        page = browser.new_page()

        def handle_response(response):
            if "GetDailyLog" in response.url:
                print(f"Captured response from: {response.url}")
                try:
                    captured_data["entries"] = response.json().get("entries", [])
                except Exception as e:
                    print(f"Could not parse response as JSON: {e}")

        page.on("response", handle_response)

        print("Loading page...")
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(5000)

        browser.close()

    return captured_data.get("entries", [])


def load_existing_report_numbers():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["rptNumb"] for row in reader}


def append_new_entries(entries, existing_ids):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_exists = os.path.exists(LOG_FILE)
    new_count = 0

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        for entry in entries:
            rpt = entry.get("rptNumb")
            if rpt in existing_ids:
                continue

            writer.writerow({
                "rptNumb": rpt,
                "date": entry.get("date"),
                "time": entry.get("time"),
                "charges": entry.get("charges"),
                "location": entry.get("location"),
                "officer": entry.get("officer"),
                "notes": entry.get("notes"),
                "suspects": json.dumps(entry.get("suspects", [])),
                "victims": json.dumps(entry.get("victims", [])),
                "pulled_at": datetime.now(timezone.utc).isoformat()
            })
            existing_ids.add(rpt)
            new_count += 1

    return new_count


def main():
    entries = scrape_sheriff_log()
    existing_ids = load_existing_report_numbers()
    new_count = append_new_entries(entries, existing_ids)
    print(f"Fetched {len(entries)} entries, added {new_count} new ones.")


if __name__ == "__main__":
    main()