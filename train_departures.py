import os
import requests
import xmltodict
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

NATIONAL_RAIL_URL = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/ldb9.asmx"
TOKEN = os.getenv("NATIONAL_RAIL_TOKEN")


def _build_request_body(station_code: str, rows: int) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:typ="http://thalesgroup.com/RTTI/2013-11-28/Token/types"
               xmlns:ldb="http://thalesgroup.com/RTTI/2016-02-16/ldb/">
  <soap:Header>
    <typ:AccessToken>
      <typ:TokenValue>{TOKEN}</typ:TokenValue>
    </typ:AccessToken>
  </soap:Header>
  <soap:Body>
    <ldb:GetDepartureBoardRequest>
      <ldb:numRows>{rows}</ldb:numRows>
      <ldb:crs>{station_code}</ldb:crs>
      <ldb:filterType>to</ldb:filterType>
      <ldb:timeOffset>0</ldb:timeOffset>
      <ldb:timeWindow>120</ldb:timeWindow>
    </ldb:GetDepartureBoardRequest>
  </soap:Body>
</soap:Envelope>"""


def _extract(obj, *keys):
    """Safely walk nested dict/list structure returned by xmltodict."""
    cur = obj
    for key in keys:
        if cur is None:
            return None
        if isinstance(cur, list):
            cur = cur[0] if cur else None
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    if isinstance(cur, list):
        return cur[0] if cur else None
    return cur


def get_departures(station_code: str, rows: int = 12):
    """Fetch raw departures data from the National Rail API and return a list of dicts."""
    if not TOKEN:
        raise RuntimeError("NATIONAL_RAIL_TOKEN is not set")

    soap_body = _build_request_body(station_code, rows)
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}

    response = requests.post(NATIONAL_RAIL_URL, data=soap_body.encode("utf-8"), headers=headers, timeout=20)
    response.raise_for_status()

    # Save raw response for inspection (useful during debugging)
    with open("response.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("DEBUG: Response saved to response.xml")

    try:
        data = xmltodict.parse(response.text)
    except Exception as e:
        print("DEBUG: xmltodict.parse failed:", e)
        return []

    board = (
        data.get("soap:Envelope", {})
        .get("soap:Body", {})
        .get("GetDepartureBoardResponse", {})
        .get("GetStationBoardResult", {})
    )

    services = board.get("lt5:trainServices", {}).get("lt5:service", [])
    if services is None:
        services = []
    if isinstance(services, dict):
        services = [services]

    results = []
    for svc in services:
        try:
            std = _extract(svc, "lt4:std") or _extract(svc, "lt5:std") or ""
            etd = _extract(svc, "lt4:etd") or _extract(svc, "lt5:etd") or ""
            platform = _extract(svc, "lt4:platform") or _extract(svc, "lt5:platform") or "-"
            operator = _extract(svc, "lt4:operator") or _extract(svc, "lt5:operator") or ""
            operator_code = _extract(svc, "lt4:operatorCode") or _extract(svc, "lt5:operatorCode") or ""

            dest = _extract(svc, "lt5:destination", "lt4:location", "lt4:locationName")
            if dest is None:
                dest = _extract(svc, "lt5:destination", "lt5:location", "lt4:locationName") or _extract(
                    svc, "lt5:destination", "lt4:locationName"
                )
            if dest is None:
                dest = "Unknown"

            results.append(
                {
                    "std": std,
                    "destination": dest,
                    "platform": platform,
                    "etd": etd,
                    "operator": operator,
                    "operatorCode": operator_code,
                }
            )
        except Exception as e:
            print("DEBUG: Failed to extract service details:", repr(e))
            continue

    return results


def get_train_departures(station_code: str, rows: int = 12):
    """
    Returns departures grouped by platform for display,
    including 'due in X mins' calculated using ETD if delayed,
    otherwise STD. Also handles 'Due' and 'Cancelled' cases.
    """
    raw = get_departures(station_code, rows)

    def _calculate_due_in(std: str, etd: str) -> str:
        """Return minutes until departure, using ETD when available and valid."""
        try:
            now = datetime.now()

            etd_clean = (etd or "").strip().lower()
            use_time = std

            # Skip if cancelled or no report
            if etd_clean in ("cancelled", "no report"):
                return ""

            # Prefer ETD if it's a valid time (like 15:25)
            if etd_clean not in ("on time", "ontime", "due", "", "delayed"):
                if ":" in etd_clean:
                    use_time = etd

            if not use_time:
                return ""

            dep_time = datetime.strptime(use_time, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )

            # Handle midnight rollover
            if (dep_time - now).total_seconds() < -300:
                dep_time += timedelta(days=1)

            diff = int((dep_time - now).total_seconds() // 60)

            # Show "Due" if less than 1 min
            if diff <= 1:
                return "Due"

            return str(diff)
        except Exception as e:
            print(f"DEBUG: Failed to calculate due_in for std={std}, etd={etd}: {e}")
            return ""

    likely_platform = {
        "Sutton": "4",
        "Sutton (London)": "4",
        "Orpington": "3",
        "London Victoria": "2",
        "St Albans": "1",
        "St Albans City": "1",
    }

    grouped = defaultdict(list)
    now = datetime.now()

    for t in raw:
        std = t.get("std", "")
        etd = t.get("etd", "")
        due_in = _calculate_due_in(std, etd)

        # Store as both integer and text for flexibility in HTML
        if due_in in ("", "Due"):
            t["due_in_mins"] = None
        else:
            try:
                t["due_in_mins"] = int(due_in)
            except ValueError:
                t["due_in_mins"] = None

        t["due_in_text"] = due_in

        platform = t.get("platform", "-") or "-"
        destination = t.get("destination", "Unknown")

        if platform == "-":
            platform = (
                likely_platform.get(destination)
                or next((p for k, p in likely_platform.items() if destination.startswith(k)), "-")
            )

        print(f"{t.get('std')} ({t.get('etd')}) -> due in {due_in} mins (now={now.strftime('%H:%M')})")
        grouped[platform].append(t)

    def _sort_key(item):
        k = item[0]
        try:
            return (0, int(k))
        except Exception:
            return (1, k or "")

    sorted_grouped = dict(sorted(grouped.items(), key=_sort_key))
    return sorted_grouped


if __name__ == "__main__":
    import json

    station = os.getenv("STATION_CODE", "HNH")
    rows = int(os.getenv("ROW_COUNT", "10"))

    print(f"Fetching train departures for {station}...")
    data = get_train_departures(station, rows)

    with open("train_departures_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(json.dumps(data, indent=2))
    print("\nSaved output to train_departures_output.json")