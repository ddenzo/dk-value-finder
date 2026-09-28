import unittest

from src.analyze import analyze_event


class AnalyzerTests(unittest.TestCase):
    def test_identical_spread_lines_are_compared(self):
        event = {
            "commence_time": "2026-10-01T00:00:00Z",
            "away_team": "Away",
            "home_team": "Home",
            "bookmakers": [
                {"key": "draftkings", "markets": [{"key": "spreads", "outcomes": [
                    {"name": "Away", "point": 7.5, "price": -110},
                    {"name": "Home", "point": -7.5, "price": -110},
                ]}]},
                {"key": "book_a", "markets": [{"key": "spreads", "outcomes": [
                    {"name": "Away", "point": 7.5, "price": -125},
                    {"name": "Home", "point": -7.5, "price": 105},
                ]}]},
                {"key": "book_b", "markets": [{"key": "spreads", "outcomes": [
                    {"name": "Away", "point": 7.0, "price": -110},
                    {"name": "Home", "point": -7.0, "price": -110},
                ]}]},
            ],
        }
        rows = analyze_event(event)
        away = next(row for row in rows if row["selection"] == "Away")
        self.assertEqual(away["comparison_books"], 1)
        self.assertEqual(away["point"], 7.5)
        self.assertGreater(away["fair_probability"], away["dk_break_even"])


if __name__ == "__main__":
    unittest.main()
