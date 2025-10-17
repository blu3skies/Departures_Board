import requests
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Coordinates for your area (London example)

LAT = os.getenv("LATITUDE")
LON = os.getenv("LONGITUDE")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_todays_weather(lat: float = LAT, lon: float = LON) -> Dict[str, Any]:
    """Return today's high/low temp and rain probability (morning, midday, evening)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability",
        "forecast_days": 1,
        "timezone": "Europe/London",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()["hourly"]

    times = [datetime.fromisoformat(t) for t in data["time"]]
    temps = data["temperature_2m"]
    rain_probs = data["precipitation_probability"]

    # High/low temps
    high = max(temps)
    low = min(temps)

    # Morning (06–12), midday (12–18), evening (18–24)
    segments = {
        "morning": (6, 12),
        "midday": (12, 18),
        "evening": (18, 24),
    }

    rain_summary = {}
    for label, (start, end) in segments.items():
        relevant = [p for t, p in zip(times, rain_probs) if start <= t.hour < end]
        if relevant:
            rain_summary[label] = round(sum(relevant) / len(relevant), 1)
        else:
            rain_summary[label] = None

    return {
        "high_temp": round(high, 1),
        "low_temp": round(low, 1),
        "rain_probability": rain_summary,
    }