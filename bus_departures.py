import os
import requests
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

TFL_BASE_URL = "https://api.tfl.gov.uk/StopPoint"

# Optional: use your key if set (improves reliability)
APP_ID = os.getenv("TFL_APP_ID")
APP_KEY = os.getenv("TFL_APP_KEY")


def get_bus_departures(stop_code: str | None = None, limit: int = 10) -> List[Dict]:
    """
    Return upcoming bus departures for a given TfL stop code.
    Reads stop_code from .env if not provided.
    """
    if not stop_code:
        stop_code = os.getenv("BUS_STOP_ID")

    if not stop_code:
        raise ValueError("BUS_STOP_ID not set in environment or provided directly")

    # Build URL with optional key parameters
    url = f"{TFL_BASE_URL}/{stop_code}/Arrivals"
    params = {}
    if APP_ID and APP_KEY:
        params = {"app_id": APP_ID, "app_key": APP_KEY}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Sort by soonest arrival
    sorted_data = sorted(data, key=lambda x: x["timeToStation"])

    departures = []
    for item in sorted_data[:limit]:
        departures.append({
            "line": item.get("lineName"),
            "destination": item.get("destinationName"),
            "expected_in_min": int(item["timeToStation"] / 60),
            "vehicle_id": item.get("vehicleId"),
            "towards": item.get("towards"),
            "station_name": item.get("stationName")
        })

    return departures