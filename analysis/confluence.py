"""
analysis/confluence.py

موتور امتیازدهی کانفلوئنس ۰ تا ۱۰۰.

سیگنال فقط زمانی صادر می‌شود که:
- امتیاز کانفلوئنس به حداقل برسد
- چند تایم‌فریم تأیید باشند
- ساختار بازار تأیید شود
- حرکت اصلی هنوز شروع نشده باشد
- رشد اولیه بیشتر از ۵٪ نباشد

هشدارهای مستقل:
- فقط شکست واقعی و تأییدشده
- فقط الگوی کاتالیزوری معتبر
- فقط Pre-Breakout واقعی
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

MAX_INITIAL_MOVE_PCT = 5.0

TIMEFRAMES_MTF = [
    "15m",
    "1h",
    "4h",
    "1d",
    "1w",
]


def _is_rising(
    closes,
    min_ratio=0.55
):

    if len(closes) < 5:
        return False

    rising = sum(
        1
        for i in range(
            1,
            len(closes)
        )
        if closes[i] >= closes[i - 1]
    )

    return (
        rising
        /
        (len(closes) - 1)
    ) >= min_ratio


def _mtf_alignment_score(
    get_klines_fn,
    symbol,
    direction
):

    is_long = (
        direction == "LONG"
    )

    tf_results = {}

    for tf in TIMEFRAMES_MTF:

        candles = get_klines_fn(
            symbol,
            interval=tf,
            limit=25
        )

        if (
            not candles
            or len(candles) < 8
        ):

            tf_results[tf] = None

            continue

        closes = [
            float(c[4])
            for c in candles
        ]

        rising = _is_rising(
            closes
        )

        tf_results[tf] = (
            rising
            if is_long
            else not rising
        )

        time.sleep(
            0.1
        )

    available = [
        value
        for value
        in tf_results.values()
        if value is not None
    ]

    if len(available) < 3:

        return {
            "score": 0,
            "reasons": [],
            "risks": [
                "داده تایم‌فریم کافی نبود"
            ],
            "aligned_count": 0,
            "available_count": 0,
        }

    aligned = sum(
        1
        for value in available
        if value
    )

    ratio = (
        aligned
        /
        len(available)
    )

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
            f"روند در اکثر تایم‌فریم‌ها هم‌راستاست "
            f"({aligned}/{len(available)})"
        )

    else:

        score = 0

        risks.append(
            f"تایم‌فریم‌ها هم‌راستا نیستند "
            f"({aligned}/{len(available)})"
        )

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
        "aligned_count": aligned,
        "available_count": len(available),
    }


def _default_volume_bonus(
    signal_meta: dict,
    direction: str
):

    reasons = []
    risks = []

    score = 0.0

    volume = signal_meta.get(
        "volume",
        0
    )

    change = signal_meta.get(
        "change",
        0
    )

    if volume >= 10_000_000:

        score += 8

        reasons.append(
            "حجم معاملات ۲۴ ساعته بسیار بالا"
        )

    elif volume >= 3_000_000:

        score += 5

        reasons.append(
            "حجم معاملات ۲۴ ساعته بالا"
        )

    elif volume >= 500_000:

        score += 2

    if abs(change) >= 15:

        score += 7

        reasons.append(
            f"جهش قیمت شدید ({change}%)"
        )

    elif abs(change) >= 7:

        score += 4

        reasons.append(
            f"جهش قیمت قابل توجه ({change}%)"
        )

    return {
        "score": round(
            min(score, 15),
            1
        ),
        "reasons": reasons,
        "risks": risks,
        "whale_alert": (
            volume >= 10_000_000
        ),
    }


def calculate_trade_levels(
    current_price,
    swing_low,
    swing_high,
    direction
):

    if direction == "LONG":

        stop_loss = round(
            swing_low * 0.98,
            8
        )

        risk = (
            current_price
            - stop_loss
        )

        if risk <= 0:
            return None

        return {
            "entry": round(
                current_price,
                8
            ),

            "stop_loss": stop_loss,

            "tp1": round(
                current_price
                + risk * 1,
                8
            ),

            "tp2": round(
                current_price
                + risk * 2,
                8
            ),

            "tp3": round(
                current_price
                + risk * 3,
                8
            ),

            "tp4": round(
                current_price
                + risk * 4,
                8
            ),
        }

    stop_loss = round(
        swing_high * 1.02,
        8
    )

    risk = (
        stop_loss
        - current_price
    )

    if risk <= 0:
        return None

    return {
        "entry": round(
            current_price,
            8
        ),

        "stop_loss": stop_loss,

        "tp1": round(
            current_price
            - risk * 1,
            8
        ),

        "tp2": round(
            current_price
            - risk * 2,
            8
        ),

        "tp3": round(
            current_price
            - risk * 3,
            8
        ),

        "tp4": round(
            current_price
            - risk * 4,
            8
        ),
    }


def _safe_float(
    value,
    default=0.0
):

    try:

        value = float(
            value
        )

        if (
            np.isnan(value)
            or np.isinf(value)
        ):

            return default

        return value

    except Exception:

        return default


def analyze_coiling_setup(
    df: pd.DataFrame
):

    empty_result = {

        "match": False,

        "score": 0,

        "type":
            "PRE_BREAKOUT_COILING",

        "volatility_compression":
            False,

        "bollinger_squeeze":
            False,

        "volume_accumulation":
            False,

        "obv_rising":
            False,

        "price_not_overextended":
            False,

        "near_resistance":
            False,

        "reasons": [],
    }

    if (
        df is None
        or len(df) < 60
    ):

        return empty_result

    data = df.copy()

    required = [
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in required:

        if column not in data.columns:

            return empty_result

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data = data.dropna(
        subset=required
    )

    if len(data) < 60:

        return empty_result

    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data["volume"]

    previous_close = close.shift(
        1
    )

    tr1 = high - low

    tr2 = (
        high
        - previous_close
    ).abs()

    tr3 = (
        low
        - previous_close
    ).abs()

    true_range = pd.concat(
        [
            tr1,
            tr2,
            tr3
        ],
        axis=1
    ).max(
        axis=1
    )

    atr = true_range.rolling(
        14
    ).mean()

    current_atr = _safe_float(
        atr.iloc[-1]
    )

    old_atr = _safe_float(
        atr.iloc[-30:-15].mean()
    )

    atr_compression = (
        old_atr > 0
        and current_atr
        < old_atr * 0.80
    )

    bb_mid = close.rolling(
        20
    ).mean()

    bb_std = close.rolling(
        20
    ).std()

    bb_upper = (
        bb_mid
        + bb_std * 2
    )

    bb_lower = (
        bb_mid
        - bb_std * 2
    )

    bb_width = (
        (
            bb_upper
            - bb_lower
        )
        /
        bb_mid.replace(
            0,
            np.nan
        )
    )

    current_bb_width = _safe_float(
        bb_width.iloc[-1]
    )

    historical_bb_width = _safe_float(
        bb_width.iloc[-60:-20].mean()
    )

    bb_squeeze = (
        historical_bb_width > 0
        and current_bb_width
        < historical_bb_width * 0.75
    )

    volume_ma20 = volume.rolling(
        20
    ).mean()

    current_volume_ma = _safe_float(
        volume_ma20.iloc[-1]
    )

    old_volume_ma = _safe_float(
        volume_ma20.iloc[-20]
    )

    volume_ratio = (
        current_volume_ma
        /
        old_volume_ma
        if old_volume_ma > 0
        else 0
    )

    volume_accumulation = (
        volume_ratio >= 1.15
        and volume_ratio <= 2.50
    )

    price_change = close.diff()

    direction_values = np.where(
        price_change > 0,
        1,
        np.where(
            price_change < 0,
            -1,
            0
        )
    )

    obv = (
        pd.Series(
            direction_values,
            index=data.index
        )
        * volume
    ).cumsum()

    obv_recent = _safe_float(
        obv.iloc[-1]
    )

    obv_old = _safe_float(
        obv.iloc[-20]
    )

    obv_rising = (
        obv_recent
        > obv_old
    )

    price_3d_change = (

        (
            close.iloc[-1]
            /
            close.iloc[-4]
        )
        - 1

    ) * 100

    price_7d_change = (

        (
            close.iloc[-1]
            /
            close.iloc[-8]
        )
        - 1

    ) * 100

    price_not_overextended = (

        price_3d_change
        <= MAX_INITIAL_MOVE_PCT

        and

        price_7d_change
        <= 10
    )

    resistance = _safe_float(
        high.iloc[-31:-1].max()
    )

    current_price = _safe_float(
        close.iloc[-1]
    )

    resistance_distance = (

        (
            resistance
            - current_price
        )
        /
        current_price
        * 100

        if current_price > 0
        else 999
    )

    near_resistance = (
        0
        <= resistance_distance
        <= 8
    )

    score = 0

    reasons = []

    if atr_compression:

        score += 20

        reasons.append(
            "کاهش محسوس نوسان و ATR"
        )

    if bb_squeeze:

        score += 20

        reasons.append(
            "فشردگی Bollinger Bands"
        )

    if volume_accumulation:

        score += 15

        reasons.append(
            "افزایش تدریجی حجم"
        )

    if obv_rising:

        score += 15

        reasons.append(
            "روند صعودی OBV و احتمال ورود نقدینگی"
        )

    if price_not_overextended:

        score += 15

        reasons.append(
            "حرکت اصلی هنوز شروع نشده"
        )

    if near_resistance:

        score += 15

        reasons.append(
            "قیمت در آستانه مقاومت مهم قرار دارد"
        )

    active_conditions = sum(
        [
            atr_compression,
            bb_squeeze,
            volume_accumulation,
            obv_rising,
            price_not_overextended,
            near_resistance,
        ]
    )

    match = (

        active_conditions >= 4

        and score >= 60

        and price_3d_change
        <= MAX_INITIAL_MOVE_PCT
    )

    return {

        "match": match,

        "score": score,

        "type":
            "PRE_BREAKOUT_COILING",

        "volatility_compression":
            atr_compression,

        "bollinger_squeeze":
            bb_squeeze,

        "volume_accumulation":
            volume_accumulation,

        "obv_rising":
            obv_rising,

        "price_not_overextended":
            price_not_overextended,

        "near_resistance":
            near_resistance,

        "atr_ratio": round(
            current_atr / old_atr,
            3
        )
        if old_atr > 0
        else None,

        "bollinger_width": round(
            current_bb_width,
            5
        ),

        "volume_ratio": round(
            volume_ratio,
            2
        ),

        "change_3d": round(
            price_3d_change,
            2
        ),

        "change_7d": round(
            price_7d_change,
            2
        ),

        "resistance_distance": round(
            resistance_distance,
            2
        ),

        "hits": active_conditions,

        "reasons": reasons,
    }


def run_confluence_analysis(
    symbol,
    get_klines_fn,
    signal_meta: dict,
    direction="LONG",
    extra_analyzer=None,
    min_signal_score=None
):

    primary_candles = get_klines_fn(
        symbol,
        interval="4h",
        limit=100
    )

    structure_candles = get_klines_fn(
        symbol,
        interval="1d",
        limit=90
    )

    primary_df = klines_to_df(
        primary_candles
    )

    structure_df = klines_to_df(
        structure_candles
    )

    if (
        primary_df is None
        or structure_df is None
        or len(structure_df) < 30
    ):

        return None

    reasons = []

    risks = []

    total_score = 0.0

    ind = compute_indicators(
        primary_df
    )

    ind_result = score_indicator_bundle(
        ind,
        direction=direction
    )

    total_score += ind_result[
        "score"
    ]

    reasons.extend(
        ind_result[
            "reasons"
        ]
    )

    risks.extend(
        ind_result[
            "risks"
        ]
    )

    smc_result = analyze_smc(
        structure_df,
        direction=direction
    )

    total_score += smc_result[
        "score"
    ]

    reasons.extend(
        smc_result[
            "reasons"
        ]
    )

    risks.extend(
        smc_result[
            "risks"
        ]
    )

    mtf_result = _mtf_alignment_score(
        get_klines_fn,
        symbol,
        direction
    )

    total_score += mtf_result[
        "score"
    ]

    reasons.extend(
        mtf_result[
            "reasons"
        ]
    )

    risks.extend(
        mtf_result[
            "risks"
        ]
    )

    if extra_analyzer:

        extra_result = extra_analyzer(
            symbol,
            direction
        )

    else:

        extra_result = _default_volume_bonus(
            signal_meta,
            direction
        )

    total_score += extra_result.get(
        "score",
        0
    )

    reasons.extend(
        extra_result.get(
            "reasons",
            []
        )
    )

    risks.extend(
        extra_result.get(
            "risks",
            []
        )
    )

    total_score = round(
        min(
            total_score,
            100
        ),
        1
    )

    closes = structure_df[
        "close"
    ].tolist()

    highs = structure_df[
        "high"
    ].tolist()

    lows = structure_df[
        "low"
    ].tolist()

    current_price = closes[-1]

    swing_low_20d = min(
        lows[-21:-1]
    )
    if len(lows) >= 21
    else min(
        lows[:-1]
    )

    swing_high_20d = max(
        highs[-21:-1]
    )
    if len(highs) >= 21
    else max(
        highs[:-1]
    )

    trade_levels = calculate_trade_levels(
        current_price,
        swing_low_20d,
        swing_high_20d,
        direction
    )

    signal_bar = (

        min_signal_score

        if min_signal_score
        is not None

        else MIN_SIGNAL_SCORE
    )

    decision = (

        "SIGNAL"

        if total_score >= signal_bar

        else "REJECT"
    )

    catalyst_result = analyze_catalyst_breakout(
        structure_df
    )

    long_term_candles = get_klines_fn(
        symbol,
        interval="1d",
        limit=200
    )

    long_term_df = klines_to_df(
        long_term_candles
    )

    trendline_result = detect_trendline_break(
        long_term_df
    )

    coiling_result = analyze_coiling_setup(
        structure_df
    )

    return {

        "symbol":
            symbol,

        "direction":
            direction,

        "score":
            total_score,

        "decision":
            decision,

        "reasons":
            reasons[:8],

        "risks":
            risks[:5],

        "trade_levels":
            trade_levels,

        "current_price":
            round(
                current_price,
                8
            ),

        "structure_signal":
            smc_result.get(
                "structure_signal"
            ),

        "smart_money_alert":
            extra_result.get(
                "whale_alert",
                False
            ),

        "funding_rate":
            extra_result.get(
                "funding_rate"
            ),

        "open_interest":
            extra_result.get(
                "open_interest"
            ),

        "long_short_ratio":
            extra_result.get(
                "long_short_ratio"
            ),

        "catalyst_breakout":
            catalyst_result,

        "trendline_break":
            trendline_result,

        "coiling_setup":
            coiling_result,

        "breakdown": {

            "indicators":
                ind_result[
                    "score"
                ],

            "smc":
                smc_result[
                    "score"
                ],

            "mtf":
                mtf_result[
                    "score"
                ],

            "extra":
                extra_result.get(
                    "score",
                    0
                ),
        },
    }
