#!/usr/bin/env python3
import os
import time
from typing import List, Tuple

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.table import Table

from national_rail_api import get_departures

load_dotenv()

STATION_CODE = os.getenv("STATION_CODE", "PUT")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "60"))
ROWS = int(os.getenv("ROW_COUNT", "6"))

console = Console()


def fetch_board() -> List[Tuple[str, str, str, str]]:
    try:
        return get_departures(STATION_CODE, ROWS)
    except Exception as exc:
        console.print(f"[red]Failed to fetch departures: {exc}[/red]")
        return []


def render_board() -> Table:
    departures = fetch_board()

    table = Table(title=f"Departures - {STATION_CODE}", title_style="bold cyan")
    table.add_column("Time", justify="center")
    table.add_column("Destination", justify="left")
    table.add_column("Platform", justify="center")
    table.add_column("Status", justify="center")

    if not departures:
        table.add_row("-", "No data", "-", "—")
        return table

    for time_, dest, plat, status in departures:
        colour = "green" if status and "time" in status.lower() else "yellow"
        if status and ("delay" in status.lower() or "cancel" in status.lower()):
            colour = "red"
        table.add_row(time_ or "-", dest, plat, f"[{colour}]{status or '-'}[/{colour}]")

    return table


def main() -> None:
    with Live(render_board(), refresh_per_second=2, screen=True) as live:
        while True:
            time.sleep(REFRESH_INTERVAL)
            live.update(render_board())


if __name__ == "__main__":
    main()
