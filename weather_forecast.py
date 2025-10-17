import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

LAT = float(os.getenv("LATITUDE", "51.5072"))
LON = float(os.getenv("LONGITUDE", "-0.1276"))
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def deg_to_cardinal(deg: float) -> str:
    """Convert degrees to compass direction (e.g. SW)."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = round(deg / 45) % 8
    return dirs[ix]


def classify_rain_intensity(mm: float) -> str:
    """Return a qualitative description of rain intensity."""
    if mm == 0:
        return "☀️ Dry"
    elif mm < 0.5:
        return "🌦️ Drizzle"
    elif mm < 2:
        return "🌧️ Light rain"
    elif mm < 5:
        return "🌧️ Moderate rain"
    else:
        return "⛈️ Heavy rain"


def get_todays_weather(lat: float = LAT, lon: float = LON) -> Dict[str, Any]:
    """Return today's high/low temp, rain, wind, and sunrise/sunset."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "temperature_2m,precipitation_probability,precipitation,"
            "windspeed_10m,winddirection_10m,windgusts_10m"
        ),
        "daily": "sunrise,sunset",
        "forecast_days": 1,
        "timezone": "Europe/London",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    js = response.json()

    hourly = js["hourly"]
    times = [datetime.fromisoformat(t) for t in hourly["time"]]
    temps = hourly["temperature_2m"]
    rain_probs = hourly["precipitation_probability"]
    rain_intensity = hourly["precipitation"]
    wind_speed = hourly["windspeed_10m"]
    wind_dir = hourly["winddirection_10m"]
    wind_gusts = hourly["windgusts_10m"]

    high = round(max(temps), 1)
    low = round(min(temps), 1)

    segments = {
        "morning": (6, 12),
        "midday": (12, 18),
        "evening": (18, 24),
    }

    def segment_avg(values, start, end):
        relevant = [v for t, v in zip(times, values) if start <= t.hour < end]
        return sum(relevant) / len(relevant) if relevant else None

    forecast = {}
    for label, (start, end) in segments.items():
        rain_prob = segment_avg(rain_probs, start, end)
        rain_mm = segment_avg(rain_intensity, start, end)
        wind = segment_avg(wind_speed, start, end)
        gusts = segment_avg(wind_gusts, start, end)
        direction_deg = segment_avg(wind_dir, start, end)
        forecast[label] = {
            "rain_probability": round(rain_prob or 0, 1),
            "rain_intensity": classify_rain_intensity(rain_mm or 0),
            "wind_speed": round(wind or 0, 1),
            "wind_gusts": round(gusts or 0, 1),
            "wind_dir": deg_to_cardinal(direction_deg or 0),
        }

    sunrise = js["daily"]["sunrise"][0].split("T")[1][:5]
    sunset = js["daily"]["sunset"][0].split("T")[1][:5]

    return {
        "high_temp": high,
        "low_temp": low,
        "segments": forecast,
        "sunrise": sunrise,
        "sunset": sunset,
    }