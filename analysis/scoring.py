WEIGHTS = {
    "security": 0.25,
    "fundamental": 0.20,
    "news": 0.15,
    "narrative": 0.15,
    "technical": 0.10,
    "community": 0.10,
    "liquidity": 0.05,
}


def calculate_total_score(scores: dict) -> float:
    total = 0.0
    for key, weight in WEIGHTS.items():
        total += scores.get(key, 0) * weight
    return round(total, 1)


def classify_status(total_score: float) -> str:
    if total_score >= 85:
        return "STRONG PROJECT"
    elif total_score >= 70:
        return "WATCHLIST"
    else:
        return "REJECT"
