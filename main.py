import os
from dotenv import load_dotenv
from train_departures import get_train_departures
from bus_departures import get_bus_departures

load_dotenv()

def main():
    station_code = os.getenv("STATION_CODE")
    rows = int(os.getenv("ROW_COUNT", "10"))
    bus_stop_id = os.getenv("BUS_STOP_ID")

    # === Train Departures ===
    print(f"\n🚆 Upcoming train departures for {station_code}:\n")
    trains = get_train_departures(station_code, rows)
    for train in trains:
        print(f"{train['std'] or '-':<6}  {train['destination']:<25}  "
              f"Plat {train['platform']:<3}  {train['etd']:<10}  "
              f"{train['operator']} ({train['operator_code']})")

    # === Bus Departures ===
    print(f"\n🚌 Upcoming bus departures for stop {bus_stop_id}:\n")
    buses = get_bus_departures(bus_stop_id, limit=10)
    for bus in buses:
        mins = bus['expected_in_min']
        print(f"{bus['line']:<4}  {bus['destination']:<25}  in {mins:>2} min")

if __name__ == "__main__":
    main()