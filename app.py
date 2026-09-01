"""Local Streamlit dashboard for the Monterey County public-data pipeline."""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
import altair as alt


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "capstone.db"
DISPLAY_DB_PATH = "data/capstone.db"

st.set_page_config(page_title="Monterey Public Data", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { min-width: 235px; max-width: 270px; }
    [data-testid="stSidebar"] section { padding: 1.5rem 1rem; }
    [data-testid="stSidebar"] h2 { font-size: 1.25rem; margin-bottom: 1.25rem; }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size: .85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    st.error(f"No county measures found in {DISPLAY_DB_PATH}.")
    st.stop()

measures["numeric_value"] = numeric_values(measures)
measures["year_label"] = measures["year"].astype(str)
sources = sorted(measures["source"].dropna().unique())

with st.sidebar:
    st.header("Filters")
    if st.button("Refresh database", use_container_width=True):
        load_table.clear()
        st.rerun()
    source_choice = st.selectbox("Source", ["All sources"] + sources)
    if source_choice == "All sources":
        filtered = measures.copy()
    else:
        filtered = measures[measures["source"] == source_choice]
    measure_names = sorted(filtered["measure"].dropna().unique())
    measure_choice = st.selectbox("Measure", ["All measures"] + measure_names)

if measure_choice != "All measures":
    filtered = filtered[filtered["measure"] == measure_choice]

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
        units = sorted(trend["unit"].fillna("Unspecified").unique())
        selected_unit = st.selectbox("Display comparable values", units)
        trend = trend[trend["unit"].fillna("Unspecified") == selected_unit].copy()
        trend["period"] = trend["year_label"]
        charts = []
        for measure_name in sorted(trend["measure"].unique()):
            measure_data = trend[trend["measure"] == measure_name]
            upper_bound = float(measure_data["numeric_value"].max()) * 1.1
            chart = (
                alt.Chart(measure_data)
                .mark_bar(color="#e85d62")
                .encode(
                    x=alt.X("period:N", sort=None, title="Period", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y(
                        "numeric_value:Q",
                        title=f"Value ({selected_unit})",
                        scale=alt.Scale(domain=[0, upper_bound]),
                    ),
                    tooltip=["period:N", "measure:N", "numeric_value:Q", "unit:N"],
                )
                .properties(title=measure_name, height=230)
            )
            charts.append(chart)
        st.altair_chart(alt.vconcat(*charts).resolve_scale(y="independent"), use_container_width=True)
        st.caption(
            "Measures are separated by unit, and each panel scales to 110% of its own largest value."
        )

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
    st.write(f"Database: `{DISPLAY_DB_PATH}`")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
