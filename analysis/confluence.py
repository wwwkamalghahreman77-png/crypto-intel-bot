"""
analysis/confluence.py

موتور امتیازدهی کانفلوئنس ۰ تا ۱۰۰.

تصمیم:
    >= 55 → SIGNAL
    < 55  → REJECT

هشدارهای مستقل:
    - CATALYST_BREAKOUT
    - TRENDLINE_BREAK
    - PRE_BREAKOUT_COILING

WATCHLIST معاملاتی حذف شده است.
"""

import time
import numpy as np
import pandas as pd

from analysis.indicators import (
    klines_to_df,
    compute_indicators,
    score_indicator_bundle,
)
from analysis.smc import analyze_smc
from analysis.catalyst_breakout import analyze_catalyst_breakout
from analysis.trendline import detect_trendline_break


MIN_SIGNAL_SCORE = 55

TIMEFRAMES_MTF = ["15m", "1h", "4h", "1d", "1w"]


def _is_rising(closes, min_ratio=0.55):
    if len(closes) < 5:
        return False

    rising = sum(
        1
        for i in range(1, len(closes))
        if closes[i] >= closes[i - 1]
    )

    return (rising / (len(closes) - 1)) >= min_ratio


def _mtf_alignment_score(get_klines_fn, symbol, direction) -> dict:

    is_long = direction == "LONG"
    tf_results = {}

    for tf in TIMEFRAMES_MTF:

        candles = get_klines_fn(
            symbol,
            interval=tf,
            limit=25
        )

        if not candles or len(candles) < 8:
            tf_results[tf] = None
            continue

        closes = [
            float(c[4])
            for c in candles
        ]

        rising = _is_rising(closes)

        tf_results[tf] = (
            rising
            if is_long
            else not rising
        )

        time.sleep(0.1)

    available = [
        v
        for v in tf_results.values()
        if v is not None
    ]

    if len(available) < 3:

        return {
            "score": 0,
            "reasons": [],
            "risks": ["داده تایم‌فریم کافی نبود"],
            "aligned_count": 0,
            "available_count": 0,
        }

    aligned = sum(
        1
        for v in available
        if v
    )

    ratio = aligned / len(available)

    reasons = []
    risks = []

    if ratio == 1:

        score = 20

        reasons.append(
            "روند در تمام تایم‌فریم‌ها هم‌راستاست"
        )

    elif ratio >= 0.6:

        score = 12

        reasons.append(
            f"روند در اکثر تایم‌فریم‌ها هم‌راستاست ({aligned}/{len(available)})"
        )

    else:

        score = 0

        risks.append(
            f"تایم‌فریم‌ها هم‌راستا نیستند ({aligned}/{len(available)})"
        )

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
        "aligned_count": aligned,
        "available_count": len(available),
    }


def _default_volume_bonus(signal_meta: dict, direction: str) -> dict:

    reasons = []
    risks = []

    score = 0.0

    volume = signal_meta.get(
       
