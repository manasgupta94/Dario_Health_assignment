import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"


@st.cache_data
def load_data() -> pd.DataFrame:
    file_path = PROCESSED_DIR / "weather_processed.csv"
    if not file_path.exists():
        raise FileNotFoundError("Processed data not found. Run 'python etl.py' first.")
    return pd.read_csv(file_path, parse_dates=["date"])


@st.cache_data
def load_quality_report() -> dict:
    report_path = PROCESSED_DIR / "quality_report.json"
    if not report_path.exists():
        return {"status": "unknown", "summary": {}}
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


st.set_page_config(page_title="City Weather Dashboard", layout="wide")
st.title("City Weather Intelligence Dashboard")

try:
    df = load_data()
    quality = load_quality_report()
except FileNotFoundError:
    st.warning("Processed dataset is missing. Please run the ETL first: python etl.py")
    st.stop()

cities = df["city"].sort_values().unique().tolist()
selected_city = st.selectbox("Select city", cities)
filtered_df = df[df["city"] == selected_city].copy()

if filtered_df.empty:
    st.info("No weather data available for the selected city.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Max Temp", f"{filtered_df['temp_max_c'].mean():.1f}°C")
col2.metric("Avg Min Temp", f"{filtered_df['temp_min_c'].mean():.1f}°C")
col3.metric("Total Rainfall", f"{filtered_df['precipitation_mm'].sum():.1f} mm")
col4.metric("Weather Quality", quality["status"].title())

st.subheader(f"Temperature trend for {selected_city}")
st.line_chart(filtered_df.set_index("date")[["temp_max_c", "temp_min_c"]])

st.subheader("Precipitation overview")
st.bar_chart(filtered_df.set_index("date")["precipitation_mm"])

st.subheader("Weather summary table")
st.dataframe(filtered_df[["date", "temp_max_c", "temp_min_c", "precipitation_mm", "weather_description"]].sort_values("date"), use_container_width=True)

st.subheader("Data quality checks")
st.json(quality)
