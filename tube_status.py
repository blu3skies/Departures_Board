import os
import requests
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

TFL_BASE_URL = "https://api.tfl.gov.uk/Line/Mode"
SUBSCRIPTION_KEY = os.getenv("TFL_SUBSCRIPTION_KEY")

# You can modify this list to include other modes if you like
DEFAULT_MODES = ["tube", "overground", "dlr", "elizabeth-line", "tram"]

def get_tube_status(modes: List[str] | None = None) -> List[Dict]:
    """
    Return the current status for specified TfL modes (default: Tube + Overground + DLR + Elizabeth Line + Tram).
    """
    if modes is None:
        modes = DEFAULT_MODES

    mode_str = ",".join(modes)
    url = f"{TFL_BASE_URL}/{mode_str}/Status"

    headers = {}
    if SUBSCRIPTION_KEY:
        headers["Ocp-Apim-Subscription-Key"] = SUBSCRIPTION_KEY

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    statuses = []
    for line in data:
        line_name = line["name"]
        statuses_list = line.get("lineStatuses", [])
        if not statuses_list:
            continue

        status = statuses_list[0].get("statusSeverityDescription", "Unknown")
        reason = statuses_list[0].get("reason", "")
        mode = line.get("modeName", "unknown")
        statuses.append({
            "mode": mode,
            "line": line_name,
            "status": status,
            "reason": reason
        })

    return statuses

if __name__ == "__main__":
    import json
    modes = ["tube"]
    print(f"Fetching tube status for {', '.join(modes)}...")
    data = get_tube_status(modes)
    with open("tube_status_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(json.dumps(data, indent=2))
    print("\nSaved output to tube_status_output.json")