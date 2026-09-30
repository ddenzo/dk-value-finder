import csv
import json
import os
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .fetch_odds import ApiUsage, fetch_nfl_odds
from .probabilities import american_to_probability, expected_roi, remove_vig

TARGET_BOOK = "draftkings"
MIN_COMPARISON_BOOKS = 5
CANDIDATE_EV = 0.02
WATCH_EV = 0.0
HIGH_DISPERSION = 0.025


def _outcome_key(market_key: str, outcome: dict) -> tuple:
    return (market_key, outcome["name"], outcome.get("point"))


def _book_fair_probabilities(market: dict) -> dict[tuple, float]:
    outcomes = market.get("outcomes", [])
    if len(outcomes) < 2:
        return {}
    raw = [american_to_probability(o["price"]) for o in outcomes]
    fair = remove_vig(raw)
    return {_outcome_key(market["key"], o): p for o, p in zip(outcomes, fair)}


def _classification(ev: float, books: int, dispersion: float) -> str:
    if books >= MIN_COMPARISON_BOOKS and ev >= CANDIDATE_EV and dispersion < HIGH_DISPERSION:
        return "CANDIDATE"
    if books >= MIN_COMPARISON_BOOKS and ev > WATCH_EV:
        return "WATCH"
    return "PASS"


def analyze_event(event: dict) -> list[dict]:
    dk = None
    peers = []
    for book in event.get("bookmakers", []):
        if book.get("key") == TARGET_BOOK:
            dk = book
        else:
            peers.append(book)
    if not dk:
        return []
    peer_probs, peer_prices = defaultdict(list), defaultdict(list)
    for book in peers:
        for market in book.get("markets", []):
            fair_map = _book_fair_probabilities(market)
            for outcome in market.get("outcomes", []):
                key = _outcome_key(market["key"], outcome)
                if key in fair_map:
                    peer_probs[key].append(fair_map[key])
                    peer_prices[key].append(outcome["price"])
    rows = []
    for market in dk.get("markets", []):
        for outcome in market.get("outcomes", []):
            key = _outcome_key(market["key"], outcome)
            comps = peer_probs.get(key, [])
            if not comps:
                continue
            fair = statistics.median(comps)
            dispersion = statistics.pstdev(comps) if len(comps) > 1 else 0.0
            dk_break_even = american_to_probability(outcome["price"])
            ev = expected_roi(fair, outcome["price"])
            prices = peer_prices[key]
            best_price = max(prices + [outcome["price"]])
            price_rank = 1 + sum(1 for price in prices if price > outcome["price"])
            rows.append({
                "commence_time": event.get("commence_time"), "away_team": event.get("away_team"),
                "home_team": event.get("home_team"), "market": market["key"], "selection": outcome["name"],
                "point": outcome.get("point"), "dk_odds": outcome["price"], "best_market_odds": best_price,
                "dk_price_rank": price_rank, "dk_tied_best": outcome["price"] == best_price,
                "dk_break_even": dk_break_even, "fair_probability": fair, "edge": fair - dk_break_even,
                "expected_roi": ev, "comparison_books": len(comps), "consensus_dispersion": dispersion,
                "classification": _classification(ev, len(comps), dispersion),
            })
    return rows


def analyze(events: list[dict]) -> list[dict]:
    return sorted([r for e in events for r in analyze_event(e)], key=lambda r: r["expected_roi"], reverse=True)


def _selection_label(row: dict) -> str:
    point = "" if row["point"] is None else f" {row['point']:+g}"
    return f"{row['selection']}{point} {row['dk_odds']:+}"


def _agreement(dispersion: float) -> str:
    if dispersion < 0.01:
        return "Strong"
    if dispersion < HIGH_DISPERSION:
        return "Moderate"
    return "Mixed"


def _write_summary(rows: list[dict], usage: ApiUsage, games: int) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if not path:
        return
    candidates = [r for r in rows if r["classification"] == "CANDIDATE"]
    watches = [r for r in rows if r["classification"] == "WATCH"]
    remaining = "unknown" if usage.remaining is None else str(usage.remaining)
    last = "unknown" if usage.last is None else str(usage.last)
    lines = [
        "# 🏈 DK Value Finder", "",
        f"**{games} NFL games** · **{len(rows)} DraftKings prices analyzed** · "
        f"**{len(candidates)} candidate(s)** · **{len(watches)} watch(es)**", "",
        f"**Odds API:** {last} credits used this run · {remaining} remaining", "",
        "> **CANDIDATE** means the price passed the current market-value filters. It is not a prediction that the bet will win.", ""
    ]
    for heading, group in [("## 🎯 Candidates", candidates), ("## 👀 Watch list", watches)]:
        lines += [heading, ""]
        if not group:
            lines += ["None on this run.", ""]
            continue
        for row in group[:10]:
            tied = "Best/tied-best" if row["dk_tied_best"] else f"Rank #{row['dk_price_rank']}"
            lines += [
                f"### {_selection_label(row)}",
                f"**{row['away_team']} @ {row['home_team']}**", "",
                f"- Estimated fair probability: **{row['fair_probability']:.1%}**",
                f"- DraftKings break-even: **{row['dk_break_even']:.1%}**",
                f"- Estimated EV: **{row['expected_roi']:+.1%}**",
                f"- Comparison books: **{row['comparison_books']}**",
                f"- Market agreement: **{_agreement(row['consensus_dispersion'])}** "
                f"(dispersion {row['consensus_dispersion']:.1%})",
                f"- DraftKings price: **{tied}** among matching prices", "",
                f"**Why flagged:** The broader market's median no-vig probability is above DraftKings' break-even "
                f"probability, with enough matching books to qualify under the current {row['classification']} rules.", ""
            ]
    lines += ["---", "Full CSV and raw odds remain available under **Artifacts** for deeper review."]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_snapshot(rows: list[dict]) -> Path:
    Path("history").mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path("history") / f"nfl_value_{stamp}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    return path


def main() -> None:
    events, usage = fetch_nfl_odds()
    print(f"API usage: {usage.last} credits this request | {usage.used} used | {usage.remaining} remaining")
    if usage.remaining is not None and usage.remaining < 100:
        print("WARNING: Fewer than 100 Odds API credits remain.")
    Path("data").mkdir(exist_ok=True); Path("reports").mkdir(exist_ok=True)
    Path("data/latest.json").write_text(json.dumps(events, indent=2))
    rows = analyze(events)
    if not rows:
        print("No comparable DraftKings NFL markets found."); return
    with Path("reports/nfl_value.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    snapshot = _write_snapshot(rows)
    _write_summary(rows, usage, len(events))
    candidates = [r for r in rows if r["classification"] == "CANDIDATE"]
    watches = [r for r in rows if r["classification"] == "WATCH"]
    print(f"Analyzed {len(events)} games and {len(rows)} comparable DraftKings prices.")
    print(f"Flags: {len(candidates)} candidates | {len(watches)} watches")
    print(f"Historical snapshot: {snapshot}")


if __name__ == "__main__":
    main()
