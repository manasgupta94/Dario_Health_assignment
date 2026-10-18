import json
from pathlib import Path
from typing import Dict, List, Tuple

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


def fetch_weather_for_city(city: Dict[str, float]) -> Dict:
    """Fetch weather forecast data for a single city using Open-Meteo."""
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={city['latitude']}&longitude={city['longitude']}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&"
        "timezone=auto"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


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

    rows = []
    for idx, day in enumerate(dates):
        rows.append(
            {
                "city": city_name,
                "date": day,
                "temp_max_c": temps_max[idx] if idx < len(temps_max) else None,
                "temp_min_c": temps_min[idx] if idx < len(temps_min) else None,
                "precipitation_mm": precipitation[idx] if idx < len(precipitation) else None,
                "weather_code": weather_codes[idx] if idx < len(weather_codes) else None,
                "weather_description": WEATHER_CODES.get(weather_codes[idx], "Unknown") if idx < len(weather_codes) else "Unknown",
            }
        )
    return pd.DataFrame(rows)


def validate_dataset(df: pd.DataFrame) -> Dict:
    """Run standard quality checks and return summary and invalid row list."""
    total_rows = len(df)
    missing_values = int(df.isnull().sum().sum())
    invalid_temperature_rows = int(
        df[(df["temp_max_c"].abs() > 100) | (df["temp_min_c"].abs() > 100)].shape[0]
    )
    invalid_precip_rows = int(df[(df["precipitation_mm"] < 0)].shape[0])
    duplicate_rows = int(df.duplicated(subset=["city", "date"]).sum())
    invalid_weather_codes = int(df[(df["weather_code"].notna()) & (~df["weather_code"].isin(WEATHER_CODES.keys()))].shape[0])

    summary = {
        "total_rows": total_rows,
        "missing_values": missing_values,
        "invalid_temperature_rows": invalid_temperature_rows,
        "invalid_precip_rows": invalid_precip_rows,
        "duplicate_rows": duplicate_rows,
        "invalid_weather_codes": invalid_weather_codes,
    }

    status = "passed"
    if missing_values > 0 or invalid_temperature_rows > 0 or invalid_precip_rows > 0 or duplicate_rows > 0 or invalid_weather_codes > 0:
        status = "warning"

    return {"summary": summary, "status": status}


def build_processed_dataset() -> pd.DataFrame:
    frames = []
    for city in CITIES:
        raw = fetch_weather_for_city(city)
        save_raw_data(raw, city["city"])
        df = transform_weather_data(raw, city["city"])
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"])
    combined["temp_max_c"] = pd.to_numeric(combined["temp_max_c"], errors="coerce")
    combined["temp_min_c"] = pd.to_numeric(combined["temp_min_c"], errors="coerce")
    combined["precipitation_mm"] = pd.to_numeric(combined["precipitation_mm"], errors="coerce")
    combined["weather_code"] = pd.to_numeric(combined["weather_code"], errors="coerce")

    validation = validate_dataset(combined)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(PROCESSED_DIR / "weather_processed.csv", index=False)
    with open(PROCESSED_DIR / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)
    return combined


if __name__ == "__main__":
    build_processed_dataset()
    print("Weather ETL completed successfully.")
