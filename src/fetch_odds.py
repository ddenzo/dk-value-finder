import os
from dataclasses import dataclass

import requests

BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "americanfootball_nfl"


@dataclass(frozen=True)
class ApiUsage:
    last: int | None
    used: int | None
    remaining: int | None


def _header_int(headers, name: str) -> int | None:
    value = headers.get(name)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def fetch_nfl_odds() -> tuple[list[dict], ApiUsage]:
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
    usage = ApiUsage(
        last=_header_int(response.headers, "x-requests-last"),
        used=_header_int(response.headers, "x-requests-used"),
        remaining=_header_int(response.headers, "x-requests-remaining"),
    )
    return response.json(), usage
