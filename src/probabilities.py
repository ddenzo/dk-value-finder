def american_to_probability(odds: int | float) -> float:
    """Convert American odds to implied probability."""
    if odds == 0:
        raise ValueError("American odds cannot be zero")
    return (-odds) / ((-odds) + 100) if odds < 0 else 100 / (odds + 100)


def american_profit_per_unit(odds: int | float) -> float:
    """Profit on a 1-unit winning stake at American odds."""
    if odds == 0:
        raise ValueError("American odds cannot be zero")
    return 100 / (-odds) if odds < 0 else odds / 100


def expected_roi(fair_probability: float, american_odds: int | float) -> float:
    """Expected profit per unit staked, expressed as a decimal ROI."""
    profit = american_profit_per_unit(american_odds)
    return fair_probability * profit - (1 - fair_probability)


def remove_vig(probabilities: list[float]) -> list[float]:
    """Normalize implied probabilities so they sum to 1."""
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("Probability total must be positive")
    return [p / total for p in probabilities]
