# app.py
import os
from datetime import datetime
from flask import Flask, render_template, jsonify

from train_departures import get_train_departures
from bus_departures import get_bus_departures
from tube_status import get_tube_status
from weather_forecast import get_todays_weather

app = Flask(__name__)

LINE_COLOURS = {
    "bakerloo": "#ae6118",
    "central": "#dc241f",
    "circle": "#f3ce0f",
    "district": "#00782a",
    "dlr": "#00afad",
    "elizabethline": "#6950a1",
    "hammersmithandcity": "#f4a9be",
    "jubilee": "#868f98",
    "metropolitan": "#751056",
    "northern": "#000000",
    "overground": "#e86a10",
    "piccadilly": "#0019a8",
    "tram": "#66c61a",
    "victoria": "#00a0e2",
    "waterlooandcity": "#76d0a3",
    "waterloocity": "#76d0a3",  
}


def _line_key(name: str | None) -> str:
    """Normalize TfL line names for colour lookups."""
    if not name:
        return ""
    return "".join(ch for ch in name.lower() if ch.isalnum())

def _normalize_tubes(raw):
    """
    Normalize tube entries into dicts: {'name': ..., 'status': ..., 'severity': ...}
    and sort so that worst severities appear first.
    """
    def detect_severity(status_text):
        s = (status_text or "").lower()
        if any(k in s for k in ("major", "severe", "significant")):
            return "major"
        if any(k in s for k in ("minor", "part", "planned", "closure", "reduced")):
            return "warn"
        return "good"

    out = []
    for t in (raw or []):
        name = None
        status = None
        reason = ""

        if isinstance(t, dict):
            # common fields
            name = t.get("name") or t.get("lineName") or t.get("line") or t.get("id")
            # nested status shapes may vary
            status = t.get("status") or t.get("lineStatus") or t.get("description")
            reason = (
                t.get("reason")
                or t.get("details")
                or t.get("additionalInfo")
                or ""
            )
        else:
            # could be a plain string like "Bakerloo: Good Service" or "Bakerloo - Good Service"
            try:
                s = str(t)
                if ":" in s:
                    name, status = [p.strip() for p in s.split(":", 1)]
                elif " - " in s:
                    name, status = [p.strip() for p in s.split(" - ", 1)]
                elif "—" in s:
                    name, status = [p.strip() for p in s.split("—", 1)]
                else:
                    # fallback: whole string as name
                    name = s
                    status = ""
            except Exception:
                name = str(t)
                status = ""

        severity = detect_severity(status or reason)
        key = _line_key(name)
        out.append(
            {
                "name": name or "Unknown",
                "status": status or "Unknown",
                "severity": severity,
                "color": LINE_COLOURS.get(key, "#3f3f46"),
                "reason": reason,
            }
        )

    # sort by severity: major -> warn -> good, preserve original order within groups
    order = {"major": 0, "warn": 1, "good": 2}
    out.sort(key=lambda x: order.get(x.get("severity", "good"), 2))
    return out


@app.route("/")
def index():
    station = os.getenv("STATION_CODE", "PUT")
    rows = int(os.getenv("ROW_COUNT", "10"))
    bus_stop = os.getenv("BUS_STOP_ID", "")

    trains = get_train_departures(station, rows)
    buses = get_bus_departures(bus_stop, limit=8) if bus_stop else []
    raw_tubes = get_tube_status(["tube"])  # change list to include other modes if you want
    tubes = _normalize_tubes(raw_tubes)
    tube_issues = [t for t in tubes if t.get("severity") != "good"]
    tube_good = [t for t in tubes if t.get("severity") == "good"]
    if tube_issues:
        if tube_good:
            summary = f"Good service on all other line{'s' if len(tube_good) != 1 else ''}."
        else:
            summary = ""
    else:
        summary = "Good service on all lines." if tube_good else ""
    tube_good_colours = [t.get("color") for t in tube_good if t.get("color")][:12]
    weather = get_todays_weather()
    now = datetime.now()
    current_datetime = now.strftime("%d %b %Y - %H:%M")

    return render_template(
        "index.html",
        updated=now.strftime("%H:%M:%S"),
        current_datetime=current_datetime,
        station=station,
        trains=trains,
        buses=buses,
        tubes=tube_issues,
        weather=weather,
        tube_has_data=bool(tubes),
        tube_good_summary=summary,
        tube_good_colours=tube_good_colours,
    )

# tiny JSON endpoints (useful for debugging/JS refresh later)
@app.route("/api/trains")
def api_trains():
    station = os.getenv("STATION_CODE", "PUT")
    rows = int(os.getenv("ROW_COUNT", "10"))
    return jsonify(get_train_departures(station, rows))

@app.route("/api/tubes")
def api_tubes():
    raw = get_tube_status(["tube"])
    return jsonify(_normalize_tubes(raw))

@app.route("/api/buses")
def api_buses():
    bus_stop = os.getenv("BUS_STOP_ID", "")
    return jsonify(get_bus_departures(bus_stop, limit=8) if bus_stop else [])

@app.route("/api/weather")
def api_weather():
    return jsonify(get_todays_weather())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
