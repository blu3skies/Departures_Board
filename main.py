import os
from dotenv import load_dotenv
from train_departures import get_train_departures
from bus_departures import get_bus_departures
from tube_status import get_tube_status
from weather_forecast import get_todays_weather

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

    # === Tube Status ===
    print(f"\n🚇 Tube line status:\n")
    tubes = get_tube_status()
    for tube in tubes:
        line_display = f"{tube['line']:<15}"
        status_display = f"{tube['status']:<15}"
        if tube["reason"]:
            print(f"{line_display}  {status_display}  {tube['reason']}")
        else:
            print(f"{line_display}  {status_display}")
    
    # === Weather Forecast ===
    print("\n🌤 Today's weather forecast:\n")
    weather = get_todays_weather()
    print(f"High: {weather['high_temp']}°C   Low: {weather['low_temp']}°C")

    rain = weather["rain_probability"]
    print(f"Chance of rain - Morning: {rain['morning']}%, Midday: {rain['midday']}%, Evening: {rain['evening']}%")

if __name__ == "__main__":
    main()