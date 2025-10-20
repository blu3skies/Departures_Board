# Departures Board

A Python-based Flask web application that serves as a real-time, at-a-glance dashboard for London travel and weather information.  
It’s designed for wall-mounted or kiosk displays — for example, an old Android tablet running **Fully Kiosk Browser** or a small Raspberry Pi screen.

---

## ✨ Overview

Departures Board combines multiple live data sources into a single page:

- **National Rail** – Train departures for a chosen UK station  
- **TfL Bus API** – Live bus arrivals for a nearby stop  
- **TfL Line Status** – Tube and Overground service updates  
- **Open-Meteo** – Local weather forecast (rain, wind, temperature, sunrise/sunset)

Everything refreshes automatically and displays in a clean, **teletext-inspired** layout for readability at a distance.

---

## 🧩 Features

### 🚆 Train Departures
- Live data from National Rail OpenLDBWS (SOAP API)
- Displays time, destination, platform, status (On time / Delayed / Cancelled), and operator
- Groups trains by platform
- Automatically fetches the **station’s full name** (e.g. “Herne Hill”) from the API

### 🚍 Bus Arrivals
- Uses TfL StopPoint API  
- Shows upcoming buses with line number, destination, and minutes to arrival

### 🚇 Tube & Overground Status
- Uses TfL Line Status API  
- Lists disruptions, with reasons hidden behind a “Show details” button  
- Displays colour-coded line bars, and combines all *Good Service* lines into a neat summary block

### 🌤️ Weather Forecast
- Powered by **Open-Meteo**
- Shows four periods (Morning / Midday / Afternoon / Evening)  
- Displays rain %, wind speed/direction, and emoji-based sky condition  
- Highlights daily High and Low temperatures, Sunrise and Sunset

### 🖥️ Web Interface
- Built with Flask + Jinja2 templates (`base.html`, `index.html`)
- Static assets: `styles.css` and `app.js`
- Auto-refreshes every 60 seconds
- Responsive layout suitable for 7–15″ displays
- Optional CRT scanline overlay for retro effect

---

## ⚙️ Configuration

Create a `.env` file in the project root with your API keys and coordinates:

```env
# National Rail
NATIONAL_RAIL_TOKEN=your_national_rail_ldbws_token
STATION_CODE=HNH         # e.g. Herne Hill, PUT = Putney, WAT = Waterloo
ROW_COUNT=12

# TfL
BUS_STOP_ID=490004401N   # TfL StopPoint ID for your nearest stop
TFL_SUBSCRIPTION_KEY=your_tfl_api_key

# Weather
LATITUDE=51.450848
LONGITUDE=-0.115857