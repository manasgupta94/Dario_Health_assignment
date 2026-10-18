import json
from unittest.mock import Mock

import pandas as pd
import pytest

import src.weather_etl as weather_etl
from src.weather_etl import fetch_weather_for_city, transform_weather_data, validate_dataset


def test_validate_dataset_reports_each_quality_issue():
    df = pd.DataFrame(
        [
            {
                "city": "London",
                "date": "2026-10-19",
                "temp_max_c": 22.0,
                "temp_min_c": 10.0,
                "precipitation_mm": 1.5,
                "weather_code": 1,
                "weather_description": "Mainly clear",
            },
            {
                "city": "London",
                "date": "2026-10-19",
                "temp_max_c": 22.0,
                "temp_min_c": 10.0,
                "precipitation_mm": 1.5,
                "weather_code": 1,
                "weather_description": "Mainly clear",
            },
            {
                "city": "New York",
                "date": "2026-10-20",
                "temp_max_c": 120,
                "temp_min_c": 90,
                "precipitation_mm": -5,
                "weather_code": 999,
                "weather_description": "Unexpected",
            },
            {
                "city": "Tokyo",
                "date": "2026-10-21",
                "temp_max_c": 12.0,
                "temp_min_c": 18.0,
                "precipitation_mm": None,
                "weather_code": 2,
                "weather_description": "Partly cloudy",
            },
        ]
    )

    result = validate_dataset(df)
    summary = result["summary"]

    assert summary["total_rows"] == 4
    assert summary["missing_values"] == 1
    assert summary["duplicate_rows"] == 2
    assert summary["invalid_temperature_rows"] == 1
    assert summary["invalid_precip_rows"] == 1
    assert summary["invalid_weather_codes"] == 1
    assert summary["unexpected_weather_categories"] == 1
    assert summary["invalid_date_rows"] == 0
    assert summary["broken_temperature_relationships"] == 1
    assert result["status"] == "warning"


def test_validate_dataset_accepts_core_schema_without_optional_description():
    df = pd.DataFrame(
        [{
            "city": "London",
            "date": "2026-10-19",
            "temp_max_c": 22.0,
            "temp_min_c": 10.0,
            "precipitation_mm": 1.5,
            "weather_code": 1,
        }]
    )

    result = validate_dataset(df)

    assert result["status"] == "passed"
    assert result["summary"]["missing_values"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"daily": None},
        {"daily": {"time": []}},
        {
            "daily": {
                "time": ["2026-10-19"],
                "temperature_2m_max": [],
                "temperature_2m_min": [10.0],
                "precipitation_sum": [0.0],
                "weather_code": [1],
            }
        },
    ],
)
def test_fetch_rejects_malformed_or_empty_daily_payloads(monkeypatch, payload):
    response = Mock()
    response.json.return_value = payload
    monkeypatch.setattr(weather_etl.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(ValueError, match="Unexpected API payload"):
        fetch_weather_for_city({"city": "London", "latitude": 51.5, "longitude": -0.1})


def test_transform_rejects_inconsistent_daily_arrays():
    payload = {
        "daily": {
            "time": ["2026-10-19"],
            "temperature_2m_max": [22.0],
            "temperature_2m_min": [],
            "precipitation_sum": [0.0],
            "weather_code": [1],
        }
    }

    with pytest.raises(ValueError, match="arrays are incomplete or inconsistent"):
        transform_weather_data(payload, "London")


def test_partial_city_api_failure_sets_warning_and_is_reported(monkeypatch, tmp_path):
    cities = [
        {"city": "London", "latitude": 51.5, "longitude": -0.1},
        {"city": "Tokyo", "latitude": 35.7, "longitude": 139.7},
    ]
    payload = {
        "daily": {
            "time": ["2026-10-19"],
            "temperature_2m_max": [22.0],
            "temperature_2m_min": [10.0],
            "precipitation_sum": [0.0],
            "weather_code": [1],
        }
    }

    def fetch_city(city):
        if city["city"] == "Tokyo":
            raise RuntimeError("API unavailable")
        return payload

    monkeypatch.setattr(weather_etl, "CITIES", cities)
    monkeypatch.setattr(weather_etl, "fetch_weather_for_city", fetch_city)
    monkeypatch.setattr(weather_etl, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(weather_etl, "PROCESSED_DIR", tmp_path / "processed")

    result = weather_etl.build_processed_dataset()
    report_path = tmp_path / "processed" / "quality_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(result) == 1
    assert report["status"] == "warning"
    assert report["summary"]["failed_api_calls"] == 1
    assert report["failed_api_calls"] == [{"city": "Tokyo", "error": "API unavailable"}]
