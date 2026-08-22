import sqlite3
import csv
import re

DB_PATH = "data/capstone.db"


def load_cdph_csv(filepath, measure_name):
    """
    Loads a CDPH dashboard per-graph CSV export into county_measures.
    These exports have 2 title rows, then a header row, then quarterly data.
    measure_name: what to label this measure as in the database
                  (e.g. 'Any Opioid Overdose Deaths')
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = 0

    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    # first two rows are titles, third row (index 2) is the real header
    header = reader[2]
    data_rows = reader[3:]

    for row in data_rows:
        if not row or not row[0].strip():
            continue

        quarter_label = row[0].strip()  # e.g. "2006 Q1"
        match = re.match(r"(\d{4})\s*Q(\d)", quarter_label)
        if not match:
            continue
        year, quarter = match.group(1), match.group(2)

        # column layout: Quarter, Annualized Rate, Lower CL, Upper CL,
        # Quarterly Count, 12mo Rolling Rate, Lower CL, Upper CL, 12mo Rolling Count
        annualized_rate = row[1].strip() if len(row) > 1 else None
        quarterly_count = row[4].strip() if len(row) > 4 else None

        cur.execute("""
            INSERT OR IGNORE INTO county_measures
            (source, county, fips, year, category, measure, data_value_type, data_value, unit, pulled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            "cdph_overdose",
            "Monterey",
            "06053",
            f"{year} Q{quarter}",
            "Overdose Surveillance",
            f"{measure_name} - Rate",
            None,
            annualized_rate,
            "per 100k residents",
        ))
        if cur.rowcount:
            inserted += 1

        cur.execute("""
            INSERT OR IGNORE INTO county_measures
            (source, county, fips, year, category, measure, data_value_type, data_value, unit, pulled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            "cdph_overdose",
            "Monterey",
            "06053",
            f"{year} Q{quarter}",
            "Overdose Surveillance",
            f"{measure_name} - Count",
            None,
            quarterly_count,
            "count",
        ))
        if cur.rowcount:
            inserted += 1

    conn.commit()
    conn.close()
    print(f"CDPH ({measure_name}): inserted {inserted} new rows")


if __name__ == "__main__":
    load_cdph_csv(
        "data/Monterey_Any OpioidDeath_TimeTrend_08.07.2026.csv",
        "Any Opioid Overdose Deaths"
    )