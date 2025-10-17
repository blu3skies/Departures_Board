# app.py
import os
from datetime import datetime
from flask import Flask, render_template, jsonify

from train_departures import get_train_departures
from bus_departures import get_bus_departures
from tube_status import get_tube_status
from weather_forecast import get_todays_weather

app = Flask(__name__)

@app.route("/")
def index():
    station = os.getenv("STATION_CODE", "PUT")
    rows = int(os.getenv("ROW_COUNT", "10"))
    bus_stop = os.getenv("BUS_STOP_ID", "")

    trains = get_train_departures(station, rows)
    print("DEBUG trains:", trains)  # ← add this line
    buses = get_bus_departures(bus_stop, limit=8) if bus_stop else []
    tubes = get_tube_status(["tube"])  # change list to include other modes if you want
    weather = get_todays_weather()

    return render_template(
        "index.html",
        updated=datetime.now().strftime("%H:%M:%S"),
        station=station,
        trains=trains,
        buses=buses,
        tubes=tubes,
        weather=weather,
    )

# tiny JSON endpoints (useful for debugging/JS refresh later)
@app.route("/api/trains")
def api_trains():
    station = os.getenv("STATION_CODE", "PUT")
    rows = int(os.getenv("ROW_COUNT", "10"))
    return jsonify(get_train_departures(station, rows))

@app.route("/api/tubes")
def api_tubes():
    return jsonify(get_tube_status(["tube"]))

@app.route("/api/buses")
def api_buses():
    bus_stop = os.getenv("BUS_STOP_ID", "")
    return jsonify(get_bus_departures(bus_stop, limit=8) if bus_stop else [])

@app.route("/api/weather")
def api_weather():
    return jsonify(get_todays_weather())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)