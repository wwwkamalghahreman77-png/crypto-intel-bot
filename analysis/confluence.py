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

from analysis.catalyst_breakout import (
    analyze_catalyst_breakout
)

from analysis.trendline import (
    detect_trendline_break
)


MIN_SIGNAL_SCORE = 55

TIMEFRAMES_MTF = [
    "15m",
    "1h",
    "4h",
    "1d",
    "1w"
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
        (
            len(closes) - 1
        )
    ) >= min_ratio


def _mtf_alignment_score(
    get_klines_fn,
    symbol,
    direction
):

    is_long = direction == "LONG"

    tf_results = {}

    for tf in TIMEFRAMES_MTF:

        candles = get_klines_fn(
            symbol,
            interval=tf,
            limit=25
        )

        if (
            not candles
            or
            len(candles) < 8
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
        v
        for v in tf_results.values()
        if v is not None
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
        for v in available
        if v
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
        "whale_alert": volume >= 10_000_000,
    }


MAX_STOP_DISTANCE_PCT = 0.15  # حداکثر فاصله مجاز حد ضرر از قیمت فعلی (۱۵٪)
NEAR_LEVEL_PCT = 5.0          # اگر فاصله تا مقاومت/حمایت کمتر از این درصد باشد، "نزدیک سطح" است
BREAKOUT_CONFIRM_PCT = 0.5    # حداقل فاصله بسته‌شدن کندل از سطح برای تایید شکست قطعی


def calculate_trade_levels(
    current_price,
    swing_low,
    swing_high,
    direction
):

    max_distance = current_price * MAX_STOP_DISTANCE_PCT

    if direction == "LONG":

        raw_stop = swing_low * 0.98

        # اگر کف نوسان خیلی دور بود، حد ضرر به حداکثر فاصله مجاز محدود می‌شود
        stop_loss = round(
            max(raw_stop, current_price - max_distance),
            8
        )

        risk = current_price - stop_loss

        if risk <= 0:
            return None

        return {
            "entry": round(current_price, 8),
            "stop_loss": stop_loss,
            "tp1": round(current_price + risk * 1, 8),
            "tp2": round(current_price + risk * 2, 8),
            "tp3": round(current_price + risk * 3, 8),
            "tp4": round(current_price + risk * 4, 8),
        }

    raw_stop = swing_high * 1.02

    # اگر سقف نوسان خیلی دور بود (مثل TLM)، حد ضرر به حداکثر فاصله مجاز محدود می‌شود
    stop_loss = round(
        min(raw_stop, current_price + max_distance),
        8
    )

    risk = stop_loss - current_price

    if risk <= 0:
        return None

    result = {
        "entry": round(current_price, 8),
        "stop_loss": stop_loss,
    }

    # قیمت هرگز نمی‌تواند منفی یا صفر شود؛ از یک سطح به بعد دیگر TP تولید نمی‌شود
    for i in range(1, 5):
        target = current_price - risk * i
        if target <= 0:
            break
        result[f"tp{i}"] = round(target, 8)

    return result


def analyze_level_breakout(
    current_price,
    closes,
    resistance,
    support,
    direction
):
    last_close = closes[-1] if closes else current_price
    prev_close = closes[-2] if len(closes) >= 2 else last_close

    if direction == "LONG":

        level = resistance

        if not level or level <= 0:
            return {"status": "normal"}

        confirmed = (
            last_close > level * (1 + BREAKOUT_CONFIRM_PCT / 100)
            and prev_close > level
        )

        distance_pct = (level - current_price) / current_price * 100

        if confirmed:
            return {
                "status": "confirmed_break",
                "level_type": "مقاومت",
                "level_price": round(level, 8),
            }

        if 0 <= distance_pct <= NEAR_LEVEL_PCT:

            pullback_base = (
                support if support and support < current_price
                else current_price * 0.95
            )

            entry2 = round(
                current_price - (current_price - pullback_base) * 0.5,
                8
            )

            breakout_entry = round(level * 1.01, 8)
            breakout_stop = round(level * 0.97, 8)
            breakout_risk = breakout_entry - breakout_stop

            rejection_stop = round(pullback_base * 0.97, 8)
            rejection_risk = entry2 - rejection_stop

            return {
                "status": "near_level",
                "level_type": "مقاومت",
                "level_price": round(level, 8),
                "entry1": round(current_price, 8),
                "entry2": entry2,
                "scenario_breakout": {
                    "entry": breakout_entry,
                    "stop_loss": breakout_stop,
                    "tp1": round(breakout_entry + breakout_risk * 1, 8),
                    "tp2": round(breakout_entry + breakout_risk * 2, 8),
                    "tp3": round(breakout_entry + breakout_risk * 3, 8),
                    "tp4": round(breakout_entry + breakout_risk * 4, 8),
                },
                "scenario_rejection": {
                    "entry": entry2,
                    "stop_loss": rejection_stop,
                    "tp1": round(entry2 + rejection_risk * 1, 8) if rejection_risk > 0 else None,
                    "tp2": round(entry2 + rejection_risk * 2, 8) if rejection_risk > 0 else None,
                },
            }

        return {"status": "normal"}

    # SHORT
    level = support

    if not level or level <= 0:
        return {"status": "normal"}

    confirmed = (
        last_close < level * (1 - BREAKOUT_CONFIRM_PCT / 100)
        and prev_close < level
    )

    distance_pct = (current_price - level) / current_price * 100

    if confirmed:
        return {
            "status": "confirmed_break",
            "level_type": "حمایت",
            "level_price": round(level, 8),
        }

    if 0 <= distance_pct <= NEAR_LEVEL_PCT:

        pullback_base = (
            resistance if resistance and resistance > current_price
            else current_price * 1.05
        )

        entry2 = round(
            current_price + (pullback_base - current_price) * 0.5,
            8
        )

        breakout_entry = round(level * 0.99, 8)
        breakout_stop = round(level * 1.03, 8)
        breakout_risk = breakout_stop - breakout_entry

        rejection_stop = round(pullback_base * 1.03, 8)
        rejection_risk = rejection_stop - entry2

        return {
            "status": "near_level",
            "level_type": "حمایت",
            "level_price": round(level, 8),
            "entry1": round(current_price, 8),
            "entry2": entry2,
            "scenario_breakout": {
                "entry": breakout_entry,
                "stop_loss": breakout_stop,
                "tp1": round(breakout_entry - breakout_risk * 1, 8),
                "tp2": round(breakout_entry - breakout_risk * 2, 8),
                "tp3": round(breakout_entry - breakout_risk * 3, 8),
                "tp4": round(breakout_entry - breakout_risk * 4, 8),
            },
            "scenario_rejection": {
                "entry": entry2,
                "stop_loss": rejection_stop,
                "tp1": round(entry2 - rejection_risk * 1, 8) if rejection_risk > 0 else None,
                "tp2": round(entry2 - rejection_risk * 2, 8) if rejection_risk > 0 else None,
            },
        }

    return {"status": "normal"}


def detect_pattern_label(
    smc_result,
    catalyst_result,
    trendline_result,
    coiling_result,
    level_analysis,
    direction
):

    if level_analysis and level_analysis.get("status") == "confirmed_break":
        return (
            f"✅ شکست قطعی {level_analysis['level_type']} "
            f"({level_analysis['level_price']})"
        )

    if level_analysis and level_analysis.get("status") == "near_level":
        return (
            f"⏳ نزدیک {level_analysis['level_type']} - هنوز شکسته نشده "
            f"({level_analysis['level_price']})"
        )

    if trendline_result and trendline_result.get("break_confirmed"):
        return "📐 شکست ساختار بلندمدت (Trendline Break)"

    structure_signal = (smc_result or {}).get("structure_signal")

    if structure_signal == "CHOCH_BULLISH":
        return "🔄 تغییر ساختار صعودی (CHoCH)"
    if structure_signal == "CHOCH_BEARISH":
        return "🔄 تغییر ساختار نزولی (CHoCH)"
    if structure_signal == "BOS_BULLISH":
        return "📈 شکست ساختار صعودی (BOS)"
    if structure_signal == "BOS_BEARISH":
        return "📉 شکست ساختار نزولی (BOS)"

    sweep = (smc_result or {}).get("liquidity_sweep") or {}
    if sweep.get("swept") == "low" and direction == "LONG":
        return "💧 شکار نقدینگی کف (Liquidity Sweep)"
    if sweep.get("swept") == "high" and direction == "SHORT":
        return "💧 شکار نقدینگی سقف (Liquidity Sweep)"

    if catalyst_result and catalyst_result.get("match"):
        return "🚀 جهش کاتالیزوری (Catalyst Breakout)"

    if coiling_result and coiling_result.get("match"):
        return "🌀 فشردگی پیش از شکست (Pre-Breakout Coiling)"

    obs = (smc_result or {}).get("order_blocks") or {}
    if direction == "LONG" and obs.get("bullish_ob"):
        return "🧱 نزدیک Order Block صعودی"
    if direction == "SHORT" and obs.get("bearish_ob"):
        return "🧱 نزدیک Order Block نزولی"

    if (smc_result or {}).get("fvgs"):
        return "⬜ داخل Fair Value Gap"

    return "📊 تأیید چندگانه اندیکاتورها (بدون الگوی کلاسیک خاص)"


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
            or
            np.isinf(value)
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
        or
        len(df) < 60
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
        -
        previous_close
    ).abs()

    tr3 = (
        low
        -
        previous_close
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

        and

        current_atr
        <
        old_atr * 0.80

    )

    bb_mid = close.rolling(
        20
    ).mean()

    bb_std = close.rolling(
        20
    ).std()

    bb_upper = (
        bb_mid
        +
        bb_std * 2
    )

    bb_lower = (
        bb_mid
        -
        bb_std * 2
    )

    bb_width = (

        (
            bb_upper
            -
            bb_lower
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

        and

        current_bb_width
        <
        historical_bb_width * 0.75

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

        and

        volume_ratio <= 2.50

    )

    price_change = close.diff()

    direction = np.where(

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
            direction,
            index=data.index
        )

        *

        volume

    ).cumsum()

    obv_recent = _safe_float(
        obv.iloc[-1]
    )

    obv_old = _safe_float(
        obv.iloc[-20]
    )

    obv_rising = (

        obv_recent
        >
        obv_old

    )

    price_3d_change = (

        (

            close.iloc[-1]
            /
            close.iloc[-4]

        )

        -

        1

    ) * 100

    price_7d_change = (

        (

            close.iloc[-1]
            /
            close.iloc[-8]

        )

        -

        1

    ) * 100

    price_not_overextended = (

        price_3d_change < 15

        and

        price_7d_change < 25

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
            -
            current_price

        )

        /

        current_price

        *

        100

        if current_price > 0

        else 999

    )

    near_resistance = (

        0
        <=
        resistance_distance
        <=
        8

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
            "قیمت هنوز وارد پامپ شدید نشده"
        )

    if near_resistance:

        score += 15

        reasons.append(
            "قیمت به مقاومت مهم نزدیک است"
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

        and

        score >= 60

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

            current_atr
            /
            old_atr,
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

        or

        structure_df is None

        or

        len(structure_df) < 30

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

    total_score += ind_result["score"]

    reasons.extend(

        ind_result["reasons"]

    )

    risks.extend(

        ind_result["risks"]

    )

    smc_result = analyze_smc(

        structure_df,

        direction=direction

    )

    total_score += smc_result["score"]

    reasons.extend(

        smc_result["reasons"]

    )

    risks.extend(

        smc_result["risks"]

    )

    mtf_result = _mtf_alignment_score(

        get_klines_fn,

        symbol,

        direction

    )

    total_score += mtf_result["score"]

    reasons.extend(

        mtf_result["reasons"]

    )

    risks.extend(

        mtf_result["risks"]

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

    swing_low_20d = (

        min(

            lows[-21:-1]

        )

        if len(lows) >= 21

        else min(

            lows[:-1]

        )

    )

    swing_high_20d = (

        max(

            highs[-21:-1]

        )

        if len(highs) >= 21

        else max(

            highs[:-1]

        )

    )

    trade_levels = calculate_trade_levels(

        current_price,

        swing_low_20d,

        swing_high_20d,

        direction

    )

    signal_bar = (

        min_signal_score

        if min_signal_score is not None

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

    level_analysis = analyze_level_breakout(
        current_price,
        closes,
        swing_high_20d,
        swing_low_20d,
        direction
    )

    pattern_label = detect_pattern_label(
        smc_result,
        catalyst_result,
        trendline_result,
        coiling_result,
        level_analysis,
        direction
    )

    return {

        "symbol": symbol,

        "direction": direction,

        "score": total_score,

        "decision": decision,

        "reasons": reasons[:8],

        "risks": risks[:5],

        "trade_levels": trade_levels,

        "pattern": pattern_label,

        "level_analysis": level_analysis,

        "current_price": round(

            current_price,

            8

        ),

        "structure_signal": smc_result.get(

            "structure_signal"

        ),

        "smart_money_alert": extra_result.get(

            "whale_alert",

            False

        ),

        "funding_rate": extra_result.get(

            "funding_rate"

        ),

        "open_interest": extra_result.get(

            "open_interest"

        ),

        "long_short_ratio": extra_result.get(

            "long_short_ratio"

        ),

        "catalyst_breakout": catalyst_result,

        "trendline_break": trendline_result,

        "coiling_setup": coiling_result,

        "breakdown": {

            "indicators": ind_result["score"],

            "smc": smc_result["score"],

            "mtf": mtf_result["score"],

            "extra": extra_result.get(

                "score",

                0

            ),

        },

    }
