import os
import requests
from dotenv import load_dotenv
from typing import List, Dict
import time

load_dotenv()

TFL_BASE_URL = "https://api.tfl.gov.uk/StopPoint"
SUBSCRIPTION_KEY = os.getenv("TFL_SUBSCRIPTION_KEY")


def get_bus_departures(stop_code: str | None = None, limit: int = 10) -> List[Dict]:
    """
    Return upcoming bus departures for a given TfL stop code.
    Authenticates using TfL subscription key if provided.
    """
    if not stop_code:
        stop_code = os.getenv("BUS_STOP_ID")

    if not stop_code:
        raise ValueError("BUS_STOP_ID not set in environment or provided directly")

    headers = {}
    if SUBSCRIPTION_KEY:
        headers["Ocp-Apim-Subscription-Key"] = SUBSCRIPTION_KEY

    url = f"{TFL_BASE_URL}/{stop_code}/Arrivals"
    
    # Retry logic with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Increase timeout to 30 seconds
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.ReadTimeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"TfL API timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print("TfL API failed after all retries, returning empty list")
                return []
        except requests.exceptions.RequestException as e:
            print(f"TfL API request failed: {e}")
            return []

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

if __name__ == "__main__":
    import json
    stop_code = os.getenv("BUS_STOP_ID")
    print(f"Fetching bus departures for stop {stop_code}...")
    data = get_bus_departures(stop_code, limit=8)
    with open("bus_departures_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(json.dumps(data, indent=2))
    print("\nSaved output to bus_departures_output.json")