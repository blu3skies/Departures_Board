import os
import requests
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

LAT = float(os.getenv("LATITUDE", "51.5072"))
LON = float(os.getenv("LONGITUDE", "-0.1276"))
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------

def deg_to_cardinal(deg: float) -> str:
    """Convert degrees to compass direction."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = round(deg / 45) % 8
    return dirs[ix]


def classify_weather(code: int | None, cloud: float | None, rain_mm: float) -> str:
    """Return emoji based on weather code and cloud cover."""
    if code is None:
        # Fallback if code missing
        if rain_mm > 5:
            return "⛈️"
        elif rain_mm > 0.5:
            return "🌧️"
        elif cloud and cloud > 85:
            return "☁️"
        elif cloud and cloud > 50:
            return "⛅"
        else:
            return "🌤️"

    # Primary mapping from Open-Meteo weather codes
    if code == 0:
        return "☀️"
    elif code in (1, 2, 3):
        if cloud and cloud > 80:
            return "☁️"
        elif cloud and cloud > 50:
            return "⛅"
        else:
            return "🌤️"
    elif code in (45, 48):
        return "🌫️"
    elif 51 <= code <= 67:
        return "🌦️"
    elif 71 <= code <= 77:
        return "🌨️"
    elif 80 <= code <= 82:
        return "🌧️"
    elif 95 <= code <= 99:
        return "⛈️"
    else:
        return "🌤️"


# ---------------------------------------------------------
# Main forecast function
# ---------------------------------------------------------

def get_todays_weather(lat: float = LAT, lon: float = LON) -> Dict[str, Any]:
    """Return today's high/low temps, rain/wind forecast, and sunrise/sunset."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "temperature_2m,precipitation_probability,precipitation,"
            "weathercode,cloudcover,"
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
    weather_codes = hourly["weathercode"]
    cloud_cover = hourly["cloudcover"]
    wind_speed = hourly["windspeed_10m"]
    wind_dir = hourly["winddirection_10m"]
    wind_gusts = hourly["windgusts_10m"]

    high = round(max(temps), 1)
    low = round(min(temps), 1)

    segments = {
        "morning": (6, 11),
        "midday": (11, 14),
        "afternoon": (14, 18),
        "evening": (18, 21),
    }

    def segment_avg(values, start, end):
        relevant = [v for t, v in zip(times, values) if start <= t.hour < end]
        return sum(relevant) / len(relevant) if relevant else None

    def segment_mode(values, start, end):
        relevant = [int(v) for t, v in zip(times, values) if start <= t.hour < end]
        if not relevant:
            return None
        return max(set(relevant), key=relevant.count)

    forecast = {}
    for label, (start, end) in segments.items():
        rain_prob = segment_avg(rain_probs, start, end)
        rain_mm = segment_avg(rain_intensity, start, end)
        cloud = segment_avg(cloud_cover, start, end)
        code = segment_mode(weather_codes, start, end)
        wind = segment_avg(wind_speed, start, end)
        gusts = segment_avg(wind_gusts, start, end)
        direction_deg = segment_avg(wind_dir, start, end)

        forecast[label] = {
            "rain_probability": round(rain_prob or 0, 1),
            "rain_intensity": round(rain_mm or 0, 2),
            "sky_icon": classify_weather(code, cloud, rain_mm or 0),
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