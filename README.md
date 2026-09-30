# DK Value Finder

An NFL market-price analyzer that compares DraftKings with a no-vig consensus derived from other sportsbooks.

## V2

V2 is deliberately more selective than V1:

- Pulls NFL moneyline, spread, and total markets from The Odds API.
- Treats DraftKings as the target sportsbook and excludes it from consensus.
- Compares only identical selections and lines.
- Removes vig separately for each comparison book.
- Uses the **median** no-vig probability across books to reduce outlier influence.
- Measures consensus dispersion (population standard deviation of fair probabilities).
- Records DraftKings' price rank and whether it is tied for the best available price.
- Requires at least **5 matching comparison books** for a positive flag.
- Labels a price **CANDIDATE** when estimated EV is at least 2% and consensus dispersion is below 2.5 percentage points.
- Labels other positive-EV prices with sufficient market depth **WATCH**; all others are **PASS**.
- Displays Odds API credits used by the request and credits remaining.
- Saves a timestamped CSV snapshot on every run for future CLV/backtesting work.

These thresholds are starting hypotheses, not proven betting rules. The purpose of collecting snapshots is to test and refine them rather than assume they are predictive.

## Run live analysis

Use **Actions → Live NFL value report → Run workflow**. The workflow uses the repository secret `ODDS_API_KEY` and uploads the current report, raw odds, and timestamped snapshot as an artifact retained for 30 days.

A typical log begins with API usage, for example:

```
API usage: 3 credits this request | 21 used | 479 remaining
```

It warns when fewer than 100 credits remain.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ODDS_API_KEY="your-key-here"
python -m src.analyze
```

On Windows, activate with `.venv\\Scripts\\activate` and set the environment variable using your shell's syntax. Never commit the API key.

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs tests on every push and pull request.

## Next validation step

Accumulate snapshots and compare flagged prices with later/closing prices. That will let the project measure closing-line value and determine whether the V2 thresholds identify durable market value. A later predictive layer can separately incorporate football information such as injuries, weather, rest and team efficiency.
