"""SQLite schema and loaders for CDC PLACES and California HCAI exports."""

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "capstone.db"


def ensure_table():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS county_measures (
            id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL,
            county TEXT NOT NULL, fips TEXT, year TEXT, category TEXT,
            measure TEXT, data_value_type TEXT, data_value TEXT, unit TEXT,
            pulled_at TEXT, UNIQUE(source, county, year, category, measure, data_value_type)
        )""")
        # The original loader allowed duplicates when data_value_type was NULL.
        # Keep the oldest copy, then normalize the CDPH type labels so future
        # INSERT OR IGNORE operations are effective.
        connection.execute("""DELETE FROM county_measures
            WHERE id NOT IN (
                SELECT MIN(id) FROM county_measures
                GROUP BY source, county, year, category, measure,
                         COALESCE(data_value_type, '')
            )""")
        connection.execute("""UPDATE county_measures SET data_value_type = 'rate'
            WHERE data_value_type IS NULL AND measure LIKE '% - Rate'""")
        connection.execute("""UPDATE county_measures SET data_value_type = 'count'
            WHERE data_value_type IS NULL AND measure LIKE '% - Count'""")


def _insert(connection, values):
    cursor = connection.execute("""INSERT INTO county_measures
        (source, county, fips, year, category, measure, data_value_type,
         data_value, unit, pulled_at)
        SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')
        WHERE NOT EXISTS (
            SELECT 1 FROM county_measures
            WHERE source = ? AND county = ? AND year = ? AND category = ?
              AND measure = ? AND COALESCE(data_value_type, '') = COALESCE(?, '')
        )""", (*values, values[0], values[1], values[3], values[4], values[5], values[6]))
    return cursor.rowcount


def load_places(filepath=None):
    filepath = Path(filepath or ROOT / "data" / "places_monterey.csv")
    if not filepath.exists():
        raise FileNotFoundError(filepath)
    inserted = 0
    with sqlite3.connect(DB_PATH) as connection, filepath.open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            inserted += _insert(connection, (
                "cdc_places", item.get("locationname") or "Monterey",
                item.get("locationid") or "06053", item.get("year", ""),
                item.get("category", ""), item.get("measure", ""),
                item.get("data_value_type", ""), item.get("data_value", ""),
                item.get("data_value_unit", "%"),
            ))
    print(f"CDC PLACES: inserted {inserted} rows")


def load_hcai(filepath=None):
    filepath = Path(filepath or ROOT / "data" / "hcai_ed_by_county.csv")
    if not filepath.exists():
        raise FileNotFoundError(filepath)
    inserted = 0
    with sqlite3.connect(DB_PATH) as connection, filepath.open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            if item.get("Patient County", "").strip().lower() != "monterey":
                continue
            inserted += _insert(connection, (
                "hcai", "Monterey", "06053", item.get("Service year", ""),
                "Emergency Department", item.get("Disposition", ""),
                None, item.get("Encounters", ""), "count",
            ))
    print(f"HCAI: inserted {inserted} rows")
