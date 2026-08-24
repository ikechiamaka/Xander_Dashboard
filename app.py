"""Local Streamlit dashboard for the Monterey County public-data pipeline."""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "capstone.db"

st.set_page_config(page_title="Monterey Public Data", page_icon="📊", layout="wide")


@st.cache_data
def load_table(table: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(f"SELECT * FROM {table}", connection)


def numeric_values(frame: pd.DataFrame, column: str = "data_value") -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


st.title("Monterey County Public Data")
st.caption("CDC PLACES, HCAI, and CDPH data from the local SQLite pipeline")

measures = load_table("county_measures")
incidents = load_table("incidents")

if measures.empty:
    st.error(f"No county measures found at {DB_PATH}.")
    st.stop()

measures["numeric_value"] = numeric_values(measures)
measures["year_label"] = measures["year"].astype(str)
sources = sorted(measures["source"].dropna().unique())

with st.sidebar:
    st.header("Filters")
    selected_sources = st.multiselect("Source", sources, default=sources)
    filtered = measures[measures["source"].isin(selected_sources)]
    measure_names = sorted(filtered["measure"].dropna().unique())
    selected_measures = st.multiselect("Measure", measure_names, default=measure_names[:8])

filtered = filtered[filtered["measure"].isin(selected_measures)]

tab_overview, tab_trends, tab_cdc, tab_data = st.tabs(
    ["Overview", "Trends", "CDC PLACES", "Data"]
)

with tab_overview:
    first, second, third, fourth = st.columns(4)
    first.metric("Measures", f"{len(filtered):,}")
    second.metric("Data sources", filtered["source"].nunique())
    third.metric("Years / periods", filtered["year_label"].nunique())
    fourth.metric("Incident records", f"{len(incidents):,}")

    st.subheader("Latest available values")
    latest = filtered.dropna(subset=["numeric_value"]).sort_values("year_label").groupby(
        "measure", as_index=False
    ).tail(1)
    st.dataframe(
        latest[["source", "measure", "year", "numeric_value", "unit", "pulled_at"]]
        .sort_values("measure")
        .rename(columns={"numeric_value": "value"}),
        use_container_width=True,
        hide_index=True,
    )

with tab_trends:
    st.subheader("Measure trends")
    trend = filtered.dropna(subset=["numeric_value"]).copy()
    if trend.empty:
        st.info("Choose at least one measure with numeric values.")
    else:
        trend["period"] = trend["year_label"]
        chart_data = trend.pivot_table(
            index="period", columns="measure", values="numeric_value", aggfunc="mean"
        ).sort_index()
        st.line_chart(chart_data)
        st.caption("Values are shown as published; rates and counts are not combined.")

with tab_cdc:
    st.subheader("CDC PLACES measures")
    cdc = measures[measures["source"].str.contains("places|cdc", case=False, na=False)].copy()
    if cdc.empty:
        st.info("No CDC PLACES records were found in the database.")
    else:
        cdc["numeric_value"] = numeric_values(cdc)
        category = st.selectbox("CDC category", ["All"] + sorted(cdc["category"].dropna().unique()))
        if category != "All":
            cdc = cdc[cdc["category"] == category]
        st.dataframe(
            cdc[["year", "category", "measure", "numeric_value", "unit"]]
            .rename(columns={"numeric_value": "value"}),
            use_container_width=True,
            hide_index=True,
        )

with tab_data:
    st.subheader("Database records")
    st.write(f"Database: `{DB_PATH}`")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

