from src.weather_etl import build_processed_dataset


if __name__ == "__main__":
    build_processed_dataset()
    print("ETL finished. Processed weather data saved in /data/processed.")
