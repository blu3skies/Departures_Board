import os
from typing import List, Tuple
import requests
import xmltodict
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# Current public endpoint
NATIONAL_RAIL_URL = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/ldb9.asmx"
TOKEN = os.getenv("NATIONAL_RAIL_TOKEN")


def _build_request_body(station_code: str, rows: int) -> str:
    """SOAP 1.2 envelope using the current (2016-02-16) schema."""
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


def get_departures(station_code: str, rows: int = 10) -> List[Tuple[str, str, str, str, str, str]]:
    """Return simplified departure data including operator info."""
    if not TOKEN:
        raise RuntimeError("NATIONAL_RAIL_TOKEN is not set")

    soap_body = _build_request_body(station_code, rows)
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}

    response = requests.post(
        NATIONAL_RAIL_URL,
        data=soap_body.encode("utf-8"),
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()

    if "xml" not in response.headers.get("Content-Type", "").lower():
        snippet = response.text[:400]
        raise RuntimeError(f"Unexpected non-XML response:\n{snippet}")

    data = xmltodict.parse(response.text)

    board = data["soap:Envelope"]["soap:Body"]["GetDepartureBoardResponse"]["GetStationBoardResult"]
    departures = []
    train_services = board.get("lt5:trainServices", {}).get("lt5:service", [])
    if isinstance(train_services, dict):
        train_services = [train_services]

    for svc in train_services:
        std = svc.get("lt4:std")  # scheduled time
        etd = svc.get("lt4:etd")  # estimated departure
        dest = svc["lt5:destination"]["lt4:location"]["lt4:locationName"]
        platform = svc.get("lt4:platform", "-")
        operator = svc.get("lt4:operator", "Unknown")
        operator_code = svc.get("lt4:operatorCode", "")
        departures.append((std, dest, platform, etd, operator, operator_code))

    return departures


def write_departures_to_file(departures: List[Tuple[str, str, str, str, str, str]], station_code: str):
    """Group departures by platform and write them to a text file."""
    output_file = "departures.txt"

    # Group by platform using defaultdict
    grouped = defaultdict(list)
    for d in departures:
        grouped[d[2]].append(d)  # d[2] = platform

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Upcoming departures for {station_code}:\n\n")

        # Sort platforms numerically where possible
        for platform in sorted(grouped.keys(), key=lambda p: (p.isdigit(), int(p) if p.isdigit() else p)):
            f.write(f"Platform {platform}\n")
            for std, dest, plat, etd, operator, op_code in grouped[platform]:
                f.write(f"{std or '-':<6}  {dest:<25}  Plat {plat:<3}  {etd:<10}  {operator} ({op_code})\n")
            f.write("\n")

    print(f"✅ Departures grouped by platform written to {output_file}")


def main():
    station_code = os.getenv("STATION_CODE", "PUT")
    rows = int(os.getenv("ROW_COUNT", "10"))

    try:
        departures = get_departures(station_code, rows)
    except Exception as e:
        with open("departures.txt", "w", encoding="utf-8") as f:
            f.write(f"Error fetching departures: {e}\n")
        print("⚠️  Error written to departures.txt")
        return

    write_departures_to_file(departures, station_code)


if __name__ == "__main__":
    main()