import csv
import json
from collections import defaultdict
from pathlib import Path

from .fetch_odds import fetch_nfl_odds
from .probabilities import american_to_probability, expected_roi, remove_vig

TARGET_BOOK = "draftkings"


def _outcome_key(market_key: str, outcome: dict) -> tuple:
    # A price is only comparable when the outcome and line are identical.
    return (market_key, outcome["name"], outcome.get("point"))


def _book_fair_probabilities(market: dict) -> dict[tuple, float]:
    outcomes = market.get("outcomes", [])
    if len(outcomes) < 2:
        return {}
    raw = [american_to_probability(o["price"]) for o in outcomes]
    fair = remove_vig(raw)
    return {_outcome_key(market["key"], o): p for o, p in zip(outcomes, fair)}


def analyze_event(event: dict) -> list[dict]:
    dk = None
    peers = []
    for book in event.get("bookmakers", []):
        (dk := book) if book.get("key") == TARGET_BOOK else peers.append(book)
    if not dk:
        return []

    peer_probs = defaultdict(list)
    for book in peers:
        for market in book.get("markets", []):
            for key, prob in _book_fair_probabilities(market).items():
                peer_probs[key].append(prob)

    rows = []
    for market in dk.get("markets", []):
        for outcome in market.get("outcomes", []):
            key = _outcome_key(market["key"], outcome)
            comps = peer_probs.get(key, [])
            if not comps:
                continue
            fair = sum(comps) / len(comps)
            dk_break_even = american_to_probability(outcome["price"])
            rows.append({
                "commence_time": event.get("commence_time"),
                "away_team": event.get("away_team"),
                "home_team": event.get("home_team"),
                "market": market["key"],
                "selection": outcome["name"],
                "point": outcome.get("point"),
                "dk_odds": outcome["price"],
                "dk_break_even": dk_break_even,
                "fair_probability": fair,
                "edge": fair - dk_break_even,
                "expected_roi": expected_roi(fair, outcome["price"]),
                "comparison_books": len(comps),
            })
    return rows


def analyze(events: list[dict]) -> list[dict]:
    rows = [row for event in events for row in analyze_event(event)]
    return sorted(rows, key=lambda row: row["expected_roi"], reverse=True)


def main() -> None:
    events = fetch_nfl_odds()
    Path("data").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    Path("data/latest.json").write_text(json.dumps(events, indent=2))
    rows = analyze(events)
    if not rows:
        print("No comparable DraftKings NFL markets found.")
        return
    with Path("reports/nfl_value.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Analyzed {len(events)} games and wrote {len(rows)} prices to reports/nfl_value.csv")
    print("\nTop 10 by estimated ROI:")
    for row in rows[:10]:
        point = "" if row["point"] is None else f" {row['point']:+g}"
        print(f"{row['away_team']} @ {row['home_team']} | {row['selection']}{point} "
              f"{row['dk_odds']:+} | fair {row['fair_probability']:.1%} | "
              f"edge {row['edge']:+.1%} | EV {row['expected_roi']:+.1%} | "
              f"n={row['comparison_books']}")


if __name__ == "__main__":
    main()
