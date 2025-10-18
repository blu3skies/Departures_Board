import os
import requests
import xmltodict
from collections import defaultdict
from dotenv import load_dotenv

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
        # If list, take first element
        if isinstance(cur, list):
            cur = cur[0] if cur else None
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    # If final is list, prefer first element
    if isinstance(cur, list):
        return cur[0] if cur else None
    return cur


def get_departures(station_code: str, rows: int = 10):
    """Fetch raw departures data from the National Rail API and return a list of simple dicts."""
    if not TOKEN:
        raise RuntimeError("NATIONAL_RAIL_TOKEN is not set")

    soap_body = _build_request_body(station_code, rows)
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}

    response = requests.post(NATIONAL_RAIL_URL, data=soap_body.encode("utf-8"), headers=headers, timeout=20)
    response.raise_for_status()

    # Save raw response for inspection
    with open("response.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("DEBUG: Response saved to response.xml")

    # Parse XML
    try:
        data = xmltodict.parse(response.text)
    except Exception as e:
        print("DEBUG: xmltodict.parse failed:", e)
        return []

    # Navigate to board result (be defensive about keys)
    board = (
        data.get("soap:Envelope", {})
        .get("soap:Body", {})
        .get("GetDepartureBoardResponse", {})
        .get("GetStationBoardResult", {})
    )
    # trainServices appear under lt5:trainServices / lt5:service in this feed
    services = board.get("lt5:trainServices", {}).get("lt5:service", [])
    if services is None:
        services = []

    # normalize single-service dict into list
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

            # destination: lt5:destination -> lt4:location -> lt4:locationName
            dest = _extract(svc, "lt5:destination", "lt4:location", "lt4:locationName")
            if dest is None:
                # fallback: sometimes destination may be under lt5:destination -> lt5:locationName etc.
                dest = _extract(svc, "lt5:destination", "lt5:location", "lt4:locationName") or _extract(svc, "lt5:destination", "lt4:locationName")

            if dest is None:
                dest = "Unknown"

            results.append({
                "std": std,
                "destination": dest,
                "platform": platform,
                "etd": etd,
                "operator": operator,
                "operatorCode": operator_code,
            })
        except Exception as e:
            # KeyError with key 0 becomes '0' when str(e); keep full exception repr for debugging
            print("DEBUG: Failed to extract service details:", repr(e))
            continue

    return results


def get_train_departures(station_code: str, rows: int = 10):
    """
    Returns departures grouped by platform for display.
    """
    raw = get_departures(station_code, rows)

    likely_platform = {
        "Sutton": "4",
        "Sutton (London)": "4",
        "Orpington": "3",
        "London Victoria": "2",
        "St Albans": "1",
        "St Albans City": "1",
    }

    grouped = defaultdict(list)
    for t in raw:
        platform = t.get("platform", "-") or "-"
        destination = t.get("destination", "Unknown")
        if platform == "-":
            # try approximate match on destination
            # use startswith or exact keys in likely_platform
            platform = likely_platform.get(destination) or next((p for k, p in likely_platform.items() if destination.startswith(k)), "-")
        grouped[platform].append(t)

    # sort platforms: numeric first then alphanumeric
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

    # Save full JSON for inspection
    with open("train_departures_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Print summary to console
    print(json.dumps(data, indent=2))
    print("\nSaved output to train_departures_output.json")