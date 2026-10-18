# City Weather Intelligence Dashboard

An end-to-end weather analytics data product built with Python, Streamlit, pandas, and the free Open-Meteo API. It compares daily forecasts for selected cities and presents temperature, precipitation, and data-quality information for a business-facing review.

## 1. Assignment Objective

The objective is to demonstrate how a useful data product can be defined and delivered end to end: select a public data source, extract and transform its data, validate and store it locally, and present understandable insights through an analytics application. This project applies that workflow to comparing daily weather forecasts across cities.

## 2. Core Requirements

| Assignment requirement | Project implementation |
| --- | --- |
| Python solution | ETL, validation, and dashboard code are written in Python. |
| Streamlit analytics layer | `app.py` provides the interactive dashboard. |
| Free public API; no paid access, private credentials, or reviewer secrets | Open-Meteo is called without an API key. |
| ETL or processing layer | `src/weather_etl.py` extracts, transforms, validates, and stores data. |
| Local raw and processed data | Raw API responses are stored as JSON; processed rows and the quality report are stored locally. |
| Business-facing application | The dashboard provides city selection, summary metrics, charts, a weather table, and quality status. |
| Data-quality checks and error handling | The pipeline checks required data rules and records or reports API/payload failures. |
| Git-based submission | Submit the complete project repository through Git, including the files and folders listed below. |
| AI conversation transcript | The assignment requires the full AI conversation transcript in the submitted repository under `ai_transcript/`. |

## 3. API Selection

**Selected API:** [Open-Meteo Forecast API](https://open-meteo.com/)

Open-Meteo is a public weather API that does not require a key for this project. The ETL requests daily maximum and minimum temperatures, precipitation totals, and weather codes for configured city coordinates. This avoids paid access, private company credentials, and reviewer-provided secrets. The reviewer does not need to prepare a data file or configure a credential before running the pipeline; an internet connection is required for a fresh API extraction.

## 4. Expected Solution Components

### 4.1 Extraction

`fetch_weather_for_city()` requests daily forecast data for each configured city. It applies a request timeout, checks the HTTP response, and verifies that the expected daily data is present. Failed requests and malformed payloads are handled by the ETL rather than silently treated as valid data.

### 4.2 Transformation

`transform_weather_data()` turns the API's parallel daily arrays into one row per city and date. It maps Open-Meteo weather codes to readable descriptions. The combined dataset is converted to appropriate date and numeric types before validation and output.

### 4.3 Data Model

The analytical dataset is a daily city-level forecast table. Each row represents one city on one forecast date.

| Field | Meaning |
| --- | --- |
| `city` | City name. |
| `date` | Forecast date. |
| `temp_max_c` | Maximum temperature in degrees Celsius. |
| `temp_min_c` | Minimum temperature in degrees Celsius. |
| `precipitation_mm` | Daily precipitation total in millimetres. |
| `weather_code` | Open-Meteo weather code. |
| `weather_description` | Readable label mapped from the weather code. |

The natural record key is (`city`, `date`).

### 4.4 Validation and Data Quality

`validate_dataset()` checks the required core schema and reports:

- missing values by field
- duplicate city/date records
- temperatures outside the configured range of -50°C to 60°C
- precipitation outside the configured range of 0 to 200 mm
- weather codes not present in the supported Open-Meteo mapping
- unexpected descriptions when the description field is present
- missing or unparseable dates
- records where minimum temperature exceeds maximum temperature

The report status is `passed` when these checks find no issues and `warning` when one or more checks flag a problem. The pipeline also captures API failures for individual cities; it stops with an error if no city data can be retrieved or if a response has an invalid shape.

### 4.5 Loading and Local Storage

The ETL writes the source response for each successfully retrieved city to `data/raw/`. It writes the combined analytical dataset to `data/processed/weather_processed.csv` and the validation summary, including any failed city requests, to `data/processed/quality_report.json`.

### 4.6 Analytics and Streamlit Dashboard

`app.py` loads the processed dataset and quality report. A reviewer can select a city, compare average maximum and minimum temperatures and total precipitation, inspect daily temperature and precipitation charts, review the forecast table, and see the quality report. Run the ETL once before launching the dashboard; the app explains when processed data is missing.

### 4.7 Tests

`tests/test_etl.py` exercises the validation logic with a sample containing duplicates, missing data, out-of-range measurements, an unsupported weather code, and an invalid minimum/maximum temperature relationship.

## 5. Repository Structure

```text
README.md
requirements.txt
etl.py
app.py
src/
  weather_etl.py
tests/
  test_etl.py
data/
  raw/
  processed/
ai_transcript/
  ai_transcript.txt
```

Generated raw JSON, processed CSV, and quality-report files are created by running the ETL. The `.gitkeep` files retain empty data directories in Git.

## 6. Setup and Run Instructions

From the repository root in Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python etl.py
streamlit run app.py
```

To run the data-quality tests:

```powershell
python -m pytest -q
```

Keep the terminal running the Streamlit command open while using the dashboard. A fresh ETL run requires internet access to Open-Meteo.

## 7. Git Submission and AI Transcript

Use Git to track the project and submit the repository, not just the dashboard script. Include the source, tests, requirements, README, and the required **full AI conversation transcript** in `ai_transcript/ai_transcript.txt`. The transcript file must contain the complete conversation used during the assignment; a short project summary is not a substitute. Do not include virtual environments or credentials in the submission.

## 8. Assumptions and Limitations

- The configured city list is intentionally small and can be changed in `src/weather_etl.py`.
- Open-Meteo forecast responses represent current forecast data, not a durable historical archive.
- A successful fresh run depends on internet access and API availability.
- The project is a lightweight assignment-scale pipeline; it does not include a scheduler or database service.

## 9. AI Usage

AI assistance was used during API/product evaluation, data-model and ETL planning, implementation support, and refinement of the dashboard and data-quality checks. The complete conversation transcript is a separate assignment deliverable and belongs in `ai_transcript/ai_transcript.txt`.

## 10. Possible Future Improvements

- Add more cities and configurable locations.
- Add retry and caching policies for API requests.
- Expand transformation and dashboard tests.
- Add further comparison filters and business metrics.
