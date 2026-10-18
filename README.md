# City Weather Intelligence Dashboard

This project builds a simple end-to-end weather analytics data product using Python, Streamlit, and the free Open-Meteo public weather API. The dashboard compares daily weather conditions across multiple cities and surfaces key operational insights such as temperature trends, rainfall, and forecast quality.

## Project overview

The solution follows an ETL workflow:

1. Extract: fetch public weather forecast data from Open-Meteo.
2. Transform: normalize the API response into a single analytical table.
3. Validate: run data-quality checks for missing values, duplicates, invalid temperatures, and unexpected categories.
4. Load: save raw and processed outputs locally.
5. Present: deploy a Streamlit dashboard for business-friendly exploration.

## API choice

Open-Meteo is a free public API that requires no paid subscription or secret credentials. It is a strong fit for the assignment because it is accessible, stable, and suitable for reproducible data extraction.

## Repository structure

- README.md
- requirements.txt
- app.py
- etl.py
- /data/raw/
- /data/processed/
- /ai_transcript/
- /src/
- /tests/

## Local run instructions

```bash
git clone <repository-url>
cd <repository-folder>
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python etl.py
streamlit run app.py
```

## Data model and ETL explanation

The project uses a simple weather model with a city-level daily fact table:

- city: city name
- date: daily forecast date
- temp_max_c: maximum temperature in °C
- temp_min_c: minimum temperature in °C
- precipitation_mm: total precipitation in mm
- weather_code: raw weather code from the API
- weather_description: mapped readable label

The ETL process fetches weather data for several cities, saves the raw JSON payload, normalizes the data into a pandas DataFrame, validates data quality rules, and saves processed outputs to the local data folder.

## Dashboard application overview

The Streamlit application allows the reviewer to:

- choose a city
- inspect daily temperature patterns
- review precipitation trends
- compare minimum and maximum temperatures
- view data-quality status
- review raw validation results

## Data quality checks and validation logic

The project includes validation for:

- missing values
- duplicate date-city rows
- invalid temperature values beyond realistic ranges
- negative precipitation values
- invalid weather codes
- empty API responses or failed fetches

These checks are summarized in a quality report saved in the processed data folder.

## Assumptions and known limitations

- The dashboard is based on a limited set of cities selected in the ETL configuration.
- Weather data updates are based on the latest API response and are not a historical archive.
- The assignment is designed for a simple, functional product rather than a full enterprise-scale data platform.
- The app demonstrates ETL and analytics patterns in a lightweight format.

## AI usage during the assignment

AI was used to:

- evaluate API options and compare product ideas
- design the data model and ETL structure
- help define relevant business-facing metrics
- improve dashboard design and validation logic
- review assumptions and reduce weak or unrealistic architecture choices

## What would improve with more time

- add more cities and broader coverage
- include richer forecast comparison filters
- add caching and more robust retry logic
- add unit tests around transformation logic
- improve visual design and KPI storytelling

## Notes

This project uses a free public API and does not require paid access or private credentials.
