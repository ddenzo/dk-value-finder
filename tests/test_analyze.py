import unittest

from src.analyze import _classification, _crossed_key_numbers, analyze_event, wong_eligible_legs


def spread_book(key, away_price=-125, home_price=105, point=7.5):
    return {"key": key, "markets": [{"key": "spreads", "outcomes": [
        {"name": "Away", "point": point, "price": away_price},
        {"name": "Home", "point": -point, "price": home_price},
    ]}]}


class AnalyzerTests(unittest.TestCase):
    def test_identical_spread_lines_are_compared(self):
        event = {
            "away_team": "Away", "home_team": "Home",
            "bookmakers": [
                spread_book("draftkings", -110, -110),
                spread_book("book_a"),
                spread_book("book_b", point=7.0),
            ],
        }
        away = next(row for row in analyze_event(event) if row["selection"] == "Away")
        self.assertEqual(away["comparison_books"], 1)
        self.assertEqual(away["point"], 7.5)

    def test_median_resists_one_outlier(self):
        event = {"away_team": "Away", "home_team": "Home", "bookmakers": [
            spread_book("draftkings", -110, -110),
            spread_book("a", -125, 105), spread_book("b", -125, 105),
            spread_book("c", -125, 105), spread_book("d", -125, 105),
            spread_book("outlier", 200, -300),
        ]}
        away = next(row for row in analyze_event(event) if row["selection"] == "Away")
        self.assertEqual(away["comparison_books"], 5)
        self.assertGreater(away["fair_probability"], 0.53)
        self.assertGreater(away["consensus_dispersion"], 0)

    def test_candidate_requires_depth_ev_and_agreement(self):
        self.assertEqual(_classification(0.03, 5, 0.01), "CANDIDATE")
        self.assertEqual(_classification(0.03, 4, 0.01), "PASS")
        self.assertEqual(_classification(0.03, 5, 0.04), "WATCH")
        self.assertEqual(_classification(-0.01, 8, 0.01), "PASS")

    def test_price_rank_detects_better_peer_price(self):
        event = {"away_team": "Away", "home_team": "Home", "bookmakers": [
            spread_book("draftkings", -110, -110),
            spread_book("a", -105, -115),
            spread_book("b", -115, -105),
        ]}
        away = next(row for row in analyze_event(event) if row["selection"] == "Away")
        self.assertEqual(away["best_market_odds"], -105)
        self.assertEqual(away["dk_price_rank"], 2)
        self.assertFalse(away["dk_tied_best"])

    def test_three_point_leg_crosses_one_key_number(self):
        rows = [{"market": "spreads", "point": 1.5, "selection": "Dog", "comparison_books": 7,
                 "consensus_dispersion": 0.01, "away_team": "A", "home_team": "B"}]
        legs = wong_eligible_legs(rows)
        three = next(x for x in legs if x["teaser_points"] == 3)
        self.assertEqual(three["teased_point"], 4.5)
        self.assertEqual(three["key_numbers_crossed"], "3")

    def test_six_point_classic_wong_crosses_three_and_seven(self):
        rows = [{"market": "spreads", "point": 1.5, "selection": "Dog", "comparison_books": 7,
                 "consensus_dispersion": 0.01, "away_team": "A", "home_team": "B"}]
        legs = wong_eligible_legs(rows)
        six = next(x for x in legs if x["teaser_points"] == 6)
        self.assertEqual(six["teased_point"], 7.5)
        self.assertEqual(six["key_numbers_crossed"], "3 and 7")

    def test_three_point_cannot_cross_both_keys(self):
        self.assertNotEqual(_crossed_key_numbers(1.5, 4.5), [3, 7])


if __name__ == "__main__":
    unittest.main()
