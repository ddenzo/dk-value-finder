# DK Value Finder

An NFL odds-analysis project that compares DraftKings prices with a no-vig consensus derived from other sportsbooks.

## What V1 does

- Pulls NFL moneyline, spread, and total markets from The Odds API.
- Treats DraftKings as the target sportsbook.
- Removes vig separately from each comparison sportsbook's market.
- Compares only identical selections and lines (for example, +7.5 is not mixed with +7 or +8).
- Averages available no-vig probabilities into a market consensus.
- Calculates DraftKings break-even probability, estimated probability edge, and expected ROI.
- Writes all comparable prices to `reports/nfl_value.csv`, ranked by estimated ROI.

This is a price-analysis tool, not a guarantee of profitable bets. Market consensus is an estimate of probability and can be wrong.

## Setup

1. Create an account at The Odds API and obtain an API key.
2. Clone this repository and enter its directory.
3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\\Scripts\\activate`.

4. Set the API key locally. Do not commit it:

```bash
export ODDS_API_KEY="your-key-here"
```

5. Run:

```bash
python -m src.analyze
```

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs these tests on every push and pull request.

## How the math works

American odds are converted to implied probabilities. For each comparison book, the probabilities for all outcomes in a market are normalized to sum to 100%, removing the book's overround using a proportional no-vig method. Those fair probabilities are averaged across books offering the exact same outcome/line. The resulting consensus probability is compared with the DraftKings break-even probability and price to estimate edge and expected ROI.

## Next steps

After V1 is validated, useful additions include minimum-book filters, stale-line checks, closing-line-value tracking, historical backtesting, a small web dashboard, and a separate NFL teaser analyzer.
