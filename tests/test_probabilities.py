import unittest

from src.probabilities import american_to_probability, expected_roi, remove_vig


class ProbabilityTests(unittest.TestCase):
    def test_negative_american_odds(self):
        self.assertAlmostEqual(american_to_probability(-110), 110 / 210)

    def test_positive_american_odds(self):
        self.assertAlmostEqual(american_to_probability(150), 100 / 250)

    def test_remove_vig(self):
        fair = remove_vig([american_to_probability(-110), american_to_probability(-110)])
        self.assertAlmostEqual(fair[0], 0.5)
        self.assertAlmostEqual(fair[1], 0.5)

    def test_positive_expected_roi(self):
        self.assertGreater(expected_roi(0.55, -110), 0)


if __name__ == "__main__":
    unittest.main()
