import requests
import csv
import os

API_URL = "https://chronicdata.cdc.gov/resource/swc5-untb.json"
DATA_DIR = "data"
OUT_FILE = os.path.join(DATA_DIR, "places_monterey.csv")

FIELDNAMES = [
    "year", "locationname", "locationid", "category", "measure",
    "data_value", "data_value_unit", "data_value_type",
    "low_confidence_limit", "high_confidence_limit", "totalpopulation"
]


def fetch_places_data(location="Monterey", limit=1000):
    params = {
        "locationname": location,
        "$limit": limit
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()


def save_to_csv(records):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in records:
            writer.writerow({k: r.get(k, "") for k in FIELDNAMES})


def main():
    records = fetch_places_data()
    print(f"Fetched {len(records)} measures for Monterey")
    save_to_csv(records)
    print(f"Saved to {OUT_FILE}")


if __name__ == "__main__":
    main()