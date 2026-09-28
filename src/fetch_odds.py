import os
import requests

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "americanfootball_nfl"


def fetch_nfl_odds() -> list[dict]:
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise RuntimeError("Set ODDS_API_KEY in your environment before running.")

    response = requests.get(
        f"{BASE_URL}/sports/{SPORT}/odds",
        params={
            "apiKey": api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()
