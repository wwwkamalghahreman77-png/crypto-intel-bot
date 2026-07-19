"""
analysis/scoring.py

سیستم امتیازدهی نهایی پروژه‌ها و سیگنال‌ها
"""

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

        value = scores.get(
            key,
            0
        )

        try:

            value = float(
                value
            )

        except Exception:

            value = 0

        total += (
            value
            * weight
        )

    return round(
        max(
            0,
            min(
                100,
                total
            )
        ),
        1
    )


def classify_status(
    total_score: float
) -> str:

    if total_score >= 85:

        return (
            "STRONG PROJECT"
        )

    elif total_score >= 70:

        return (
            "WATCHLIST"
        )

    elif total_score >= 55:

        return (
            "SPECULATIVE"
        )

    return "REJECT"
