import os
import requests
import xmltodict
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

def get_train_departures(station_code: str, rows: int = 10):
    """Return a structured list of train departures."""
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
    body = _build_request_body(station_code, rows)

    response = requests.post(NATIONAL_RAIL_URL, data=body.encode("utf-8"), headers=headers, timeout=20)
    response.raise_for_status()

    data = xmltodict.parse(response.text)
    board = data["soap:Envelope"]["soap:Body"]["GetDepartureBoardResponse"]["GetStationBoardResult"]
    train_services = board.get("lt5:trainServices", {}).get("lt5:service", [])

    if isinstance(train_services, dict):
        train_services = [train_services]

    departures = []
    for svc in train_services:
        departures.append({
            "std": svc.get("lt4:std"),
            "etd": svc.get("lt4:etd"),
            "destination": svc["lt5:destination"]["lt4:location"]["lt4:locationName"],
            "platform": svc.get("lt4:platform", "-"),
            "operator": svc.get("lt4:operator", "Unknown"),
            "operator_code": svc.get("lt4:operatorCode", "")
        })

    return departures