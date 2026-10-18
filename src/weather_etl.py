import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

CITIES = [
    {"city": "London", "latitude": 51.5072, "longitude": -0.1276},
    {"city": "New York", "latitude": 40.7128, "longitude": -74.0060},
    {"city": "Tokyo", "latitude": 35.6762, "longitude": 139.6503},
    {"city": "Sydney", "latitude": -33.8688, "longitude": 151.2093},
    {"city": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
]

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm",
}

REQUIRED_COLUMNS = [
    "city",
    "date",
    "temp_max_c",
    "temp_min_c",
    "precipitation_mm",
    "weather_code",
    "weather_description",
]


def fetch_weather_for_city(city: Dict[str, float]) -> Dict:
    """Fetch weather forecast data for a single city using Open-Meteo."""
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&"
        "timezone=auto"
    )
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"API call failed for {city['city']}: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(f"Unexpected API payload for {city['city']}: response is not valid JSON.") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Unexpected API payload for {city['city']}: expected a JSON object.")

    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise ValueError(f"Unexpected API payload for {city['city']}: missing daily forecast data.")

    dates = daily.get("time")
    if not isinstance(dates, list) or not dates:
        raise ValueError(f"Unexpected API payload for {city['city']}: forecast dates are missing or empty.")

    daily_fields = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "weather_code"]
    for field in daily_fields:
        values = daily.get(field)
        if not isinstance(values, list) or len(values) != len(dates):
            raise ValueError(
                f"Unexpected API payload for {city['city']}: daily field '{field}' is missing or has an invalid length."
            )
    return data


def save_raw_data(raw_payload: Dict, city_name: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DIR / f"{city_name.lower().replace(' ', '_')}_raw.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, ensure_ascii=False, indent=2)
    return file_path


def transform_weather_data(raw_payload: Dict, city_name: str) -> pd.DataFrame:
    daily = raw_payload.get("daily", {})
    dates = daily.get("time", [])
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_sum", [])
    weather_codes = daily.get("weather_code", [])

    expected_length = len(dates)
    arrays = [temps_max, temps_min, precipitation, weather_codes]
    if not isinstance(dates, list) or not dates or any(
        not isinstance(values, list) or len(values) != expected_length for values in arrays
    ):
        raise ValueError(f"Unexpected API payload for {city_name}: daily forecast arrays are incomplete or inconsistent.")

    rows: List[Dict[str, object]] = []
    for idx, day in enumerate(dates):
        code = weather_codes[idx]
        rows.append(
            {
                "city": city_name,
                "date": day,
                "temp_max_c": temps_max[idx],
                "temp_min_c": temps_min[idx],
                "precipitation_mm": precipitation[idx],
                "weather_code": code,
                "weather_description": WEATHER_CODES.get(code, "Unknown") if code is not None else "Unknown",
            }
        )
    return pd.DataFrame(rows)


def validate_dataset(df: pd.DataFrame) -> Dict:
    """Run standard quality checks and return a summary of record-level issues."""
    core_columns = ["city", "date", "temp_max_c", "temp_min_c", "precipitation_mm", "weather_code"]
    missing_core = [col for col in core_columns if col not in df.columns]
    if missing_core:
        raise ValueError(f"Missing required core columns: {missing_core}")

    validation_columns = [col for col in REQUIRED_COLUMNS if col in df.columns]
    total_rows = len(df)
    missing_values = int(df[validation_columns].isnull().sum().sum())
    missing_by_column = {col: int(df[col].isnull().sum()) for col in validation_columns}

    invalid_temperature_rows = int(
        df[
            (
                (df["temp_max_c"].notna())
                & ((df["temp_max_c"] < -50) | (df["temp_max_c"] > 60))
            )
            | (
                (df["temp_min_c"].notna())
                & ((df["temp_min_c"] < -50) | (df["temp_min_c"] > 60))
            )
        ].shape[0]
    )

    invalid_precip_rows = int(
        df[(df["precipitation_mm"].notna()) & ((df["precipitation_mm"] < 0) | (df["precipitation_mm"] > 200))].shape[0]
    )

    duplicate_rows = int(df.duplicated(subset=["city", "date"], keep=False).sum())

    invalid_weather_codes = int(
        df[(df["weather_code"].notna()) & (~df["weather_code"].isin(WEATHER_CODES.keys()))].shape[0]
    )

    unexpected_weather_categories = 0
    if "weather_description" in df.columns:
        unexpected_weather_categories = int(
            df[(df["weather_description"].notna()) & (~df["weather_description"].isin(WEATHER_CODES.values()))].shape[0]
        )

    invalid_date_rows = int(
        df[(df["date"].isna()) | (pd.to_datetime(df["date"], errors="coerce").isna())].shape[0]
    )

    broken_temperature_relationships = int(
        df[
            (df["temp_min_c"].notna())
            & (df["temp_max_c"].notna())
            & (df["temp_min_c"] > df["temp_max_c"])
        ].shape[0]
    )

    summary = {
        "total_rows": total_rows,
        "missing_values": missing_values,
        "missing_by_column": missing_by_column,
        "invalid_temperature_rows": invalid_temperature_rows,
        "invalid_precip_rows": invalid_precip_rows,
        "duplicate_rows": duplicate_rows,
        "invalid_weather_codes": invalid_weather_codes,
        "unexpected_weather_categories": unexpected_weather_categories,
        "invalid_date_rows": invalid_date_rows,
        "broken_temperature_relationships": broken_temperature_relationships,
    }

    issue_counts = [
        summary["missing_values"],
        summary["invalid_temperature_rows"],
        summary["invalid_precip_rows"],
        summary["duplicate_rows"],
        summary["invalid_weather_codes"],
        summary["unexpected_weather_categories"],
        summary["invalid_date_rows"],
        summary["broken_temperature_relationships"],
    ]

    status = "passed" if all(count == 0 for count in issue_counts) else "warning"

    return {"summary": summary, "status": status}


def build_processed_dataset() -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    failed_api_calls: List[Dict[str, str]] = []

    for city in CITIES:
        try:
            raw = fetch_weather_for_city(city)
            df = transform_weather_data(raw, city["city"])
        except (RuntimeError, ValueError) as exc:
            failed_api_calls.append({"city": city["city"], "error": str(exc)})
            continue

        save_raw_data(raw, city["city"])
        frames.append(df)

    if not frames:
        raise RuntimeError("No weather data was successfully retrieved from the source API.")

    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined["temp_max_c"] = pd.to_numeric(combined["temp_max_c"], errors="coerce")
    combined["temp_min_c"] = pd.to_numeric(combined["temp_min_c"], errors="coerce")
    combined["precipitation_mm"] = pd.to_numeric(combined["precipitation_mm"], errors="coerce")
    combined["weather_code"] = pd.to_numeric(combined["weather_code"], errors="coerce")

    validation = validate_dataset(combined)
    validation["failed_api_calls"] = failed_api_calls
    validation["summary"]["failed_api_calls"] = len(failed_api_calls)
    if failed_api_calls:
        validation["status"] = "warning"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(PROCESSED_DIR / "weather_processed.csv", index=False)
    with open(PROCESSED_DIR / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)
    return combined


if __name__ == "__main__":
    build_processed_dataset()
    print("Weather ETL completed successfully.")
