"""
Master pipeline runner - scrapes and loads all working data sources.
Safe to run repeatedly (daily) since every loader has duplicate protection.

Sheriff log is intentionally excluded until Monterey County confirms
it's okay to use their internal API directly.
"""

import sys
import traceback

# --- fetch scripts ---
from scrape_cdph_all import scrape_cdph_chart, DATA_SOURCES
import requests
import os

# --- load scripts ---
from load_cdph import load_cdph_csv
from load_county_measures import ensure_table, load_places, load_hcai


def fetch_places():
    """CDC PLACES - direct API call, no scraping needed."""
    print("\n--- Fetching CDC PLACES ---")
    url = "https://chronicdata.cdc.gov/resource/swc5-untb.json"
    params = {"locationname": "Monterey", "$limit": 1000}
    response = requests.get(url, params=params)
    response.raise_for_status()

    import csv
    records = response.json()
    fieldnames = [
        "year", "locationname", "locationid", "category", "measure",
        "data_value", "data_value_unit", "data_value_type",
        "low_confidence_limit", "high_confidence_limit", "totalpopulation"
    ]
    with open("data/places_monterey.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"PLACES: fetched {len(records)} records")


def fetch_hcai():
    """HCAI ED data - direct CSV download, no scraping needed."""
    print("\n--- Fetching HCAI ---")
    url = "https://data.chhs.ca.gov/dataset/b91d0f25-d2b1-4c9f-b22d-13be3a6c5c90/resource/be06665a-7695-4a0b-af07-f0556d7e6707/download/disposition_ed_2024masked.csv"
    response = requests.get(url)
    response.raise_for_status()
    with open("data/hcai_ed_by_county.csv", "wb") as f:
        f.write(response.content)
    print(f"HCAI: downloaded {len(response.content)} bytes")


def fetch_and_load_cdph():
    """All four CDPH indicators - Playwright scrape, then load each into DB."""
    print("\n--- Fetching + Loading CDPH ---")
    files = {
        "deaths": ("cdph_deaths_timetrend.csv", "Any Opioid Overdose Deaths"),
        "ed_visits": ("cdph_ed_visits_timetrend.csv", "ED Visits"),
        "hospitalizations": ("cdph_hospitalizations_timetrend.csv", "Hospitalizations"),
        "prescriptions": ("cdph_prescriptions_timetrend.csv", "Prescriptions"),
    }
    for source_key, (filename, label) in files.items():
        scrape_cdph_chart(source_key, filename)
        load_cdph_csv(os.path.join("data", filename), label)


def run_step(name, func):
    """Run a step, log failures without stopping the whole pipeline."""
    try:
        func()
        print(f"[OK] {name}")
    except Exception:
        print(f"[FAILED] {name}")
        traceback.print_exc()


def main():
    ensure_table()

    run_step("Fetch PLACES", fetch_places)
    run_step("Load PLACES", load_places)

    run_step("Fetch HCAI", fetch_hcai)
    run_step("Load HCAI", load_hcai)

    run_step("Fetch + Load CDPH (all 4 charts)", fetch_and_load_cdph)

    print("\nPipeline run complete.")


if __name__ == "__main__":
    main()