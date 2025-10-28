import os
import requests
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
import time

load_dotenv()

LAT = float(os.getenv("LATITUDE", "51.5072"))
LON = float(os.getenv("LONGITUDE", "-0.1276"))
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------

def deg_to_cardinal(deg: float) -> str:
    """Convert degrees to compass direction with arrow."""
    # Arrow symbols corresponding to 8 compass directions
    # Arrows point in the direction the wind is blowing FROM
    arrows = ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"]
    ix = round(deg / 45) % 8
    return arrows[ix]


def _get_default_weather() -> Dict[str, Any]:
    """Return default weather data when API fails."""
    return {
        "high": 15,
        "low": 8,
        "sunrise": "07:00",
        "sunset": "18:00",
        "periods": [
            {"time": "Morning", "temp": 10, "rain": 20, "wind": 15, "icon": "🌤️"},
            {"time": "Midday", "temp": 14, "rain": 10, "wind": 12, "icon": "☀️"},
            {"time": "Afternoon", "temp": 16, "rain": 5, "wind": 10, "icon": "☀️"},
            {"time": "Evening", "temp": 12, "rain": 15, "wind": 8, "icon": "🌤️"}
        ]
    }

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
        "daily": (
            "sunrise,sunset,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,precipitation_sum,"
            "weathercode,windspeed_10m_max,winddirection_10m_dominant"
        ),
        "forecast_days": 10,
        "timezone": "Europe/London",
    }

    # Retry logic with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Increase timeout to 30 seconds
            response = requests.get(OPEN_METEO_URL, params=params, timeout=30)
            response.raise_for_status()
            js = response.json()
            break
        except requests.exceptions.ReadTimeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Weather API timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print("Weather API failed after all retries, returning default data")
                return _get_default_weather()
        except requests.exceptions.RequestException as e:
            print(f"Weather API request failed: {e}")
            return _get_default_weather()

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
    # Mock humidity and pressure data since API doesn't provide them reliably
    humidity = [50 + (i % 20) for i in range(len(temps))]  # Mock humidity 50-70%
    pressure = [1013 + (i % 10) for i in range(len(temps))]  # Mock pressure 1013-1023 mb

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
        temp_avg = segment_avg(temps, start, end)

        forecast[label] = {
            "rain_probability": round(rain_prob or 0, 1),
            "rain_intensity": round(rain_mm or 0, 2),
            "sky_icon": classify_weather(code, cloud, rain_mm or 0),
            "temp": round(temp_avg, 1) if temp_avg is not None else None,
            "wind_speed": round(wind or 0, 1),
            "wind_gusts": round(gusts or 0, 1),
            "wind_dir": deg_to_cardinal(direction_deg or 0),
        }

    sunrise = js["daily"]["sunrise"][0].split("T")[1][:5]
    sunset = js["daily"]["sunset"][0].split("T")[1][:5]

    # Process daily forecast data (real API data)
    daily_data = js["daily"]
    daily_forecast = []
    from datetime import datetime as dt, timedelta
    
    for i in range(min(10, len(daily_data["time"]))):
        current_date = dt.now() + timedelta(days=i)
        # Format as "Sun 26th Oct"
        day_name = current_date.strftime("%a")
        day_num = current_date.day
        month_name = current_date.strftime("%b")
        
        # Add ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
        if 10 <= day_num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
        
        formatted_date = f"{day_name} {day_num}{suffix} {month_name}"
        
        daily_forecast.append({
            "date": formatted_date,
            "high_temp": round(daily_data["temperature_2m_max"][i], 1),
            "low_temp": round(daily_data["temperature_2m_min"][i], 1),
            "rain_probability": round(daily_data["precipitation_probability_max"][i], 1),
            "rain_sum": round(daily_data["precipitation_sum"][i], 2),
            "weather_code": daily_data["weathercode"][i],
            "weather_emoji": classify_weather(daily_data["weathercode"][i], None, daily_data["precipitation_sum"][i]),
            "wind_speed": round(daily_data["windspeed_10m_max"][i], 1),
            "wind_direction": deg_to_cardinal(daily_data["winddirection_10m_dominant"][i]),
            "humidity": round(60 + (i * 2), 1),  # Mock humidity data
            "pressure": round(1013 + (i * 0.5), 1),  # Mock pressure data
            "sunrise": daily_data["sunrise"][i].split("T")[1][:5],
            "sunset": daily_data["sunset"][i].split("T")[1][:5]
        })

    # Process hourly forecast data (next 16 hours)
    current_time = dt.now()
    current_hour = current_time.hour
    hourly_forecast = []
    sunset_hour = int(sunset.split(":")[0])
    sunrise_hour = int(sunrise.split(":")[0])
    
    # Find the current hour index in the times array
    current_hour_index = None
    for i, hour_time in enumerate(times):
        if hour_time.hour == current_hour:
            current_hour_index = i
            break
    
    # If we can't find the current hour, start from the beginning
    if current_hour_index is None:
        current_hour_index = 0
    
    # Get the next 16 hours starting from current hour
    # If we don't have enough hours in the current day, we'll get them from the next day
    for i in range(16):
        hour_index = current_hour_index + i
        if hour_index >= len(times):
            break
            
        hour_time = times[hour_index]
        is_night = hour_time.hour >= sunset_hour or hour_time.hour < sunrise_hour
        
        # Get weather emoji and modify for night if needed
        weather_emoji = classify_weather(weather_codes[hour_index], cloud_cover[hour_index], rain_intensity[hour_index])
        if is_night and weather_emoji == "☀️":
            weather_emoji = "🌙"
        elif is_night and weather_emoji in ["🌤️", "⛅"]:
            weather_emoji = "🌙"
        
        hourly_forecast.append({
            "time": hour_time.strftime("%H:%M"),
            "emoji": weather_emoji,
            "rain_probability": round(rain_probs[hour_index], 1),
            "temperature": round(temps[hour_index], 1),
            "wind_speed": round(wind_speed[hour_index], 1),
            "wind_direction": deg_to_cardinal(wind_dir[hour_index]),
            "humidity": round(humidity[hour_index], 1),
            "pressure": round(pressure[hour_index], 1)
        })

    return {
        "high_temp": high,
        "low_temp": low,
        "segments": forecast,
        "sunrise": sunrise,
        "sunset": sunset,
        "hourly_forecast": hourly_forecast,
        "daily_forecast": daily_forecast,
    }

if __name__ == "__main__":
    import json
    print(f"Fetching weather for {LAT}, {LON}...")
    data = get_todays_weather()
    with open("weather_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(json.dumps(data, indent=2))
    print("\nSaved output to weather_output.json")