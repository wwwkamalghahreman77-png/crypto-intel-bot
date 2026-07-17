"""
analysis/smc.py

تشخیص الگوریتمیک مفاهیم Smart Money Concepts روی کندل‌های OHLC:
    - Break Of Structure (BOS) / Change of Character (CHOCH)
    - Order Blocks (آخرین کندل مخالف قبل از حرکت قوی)
    - Fair Value Gaps (FVG) - شکاف قیمتی بین کندل‌های ۱ و ۳
    - Liquidity Sweep - شکار نقدینگی بالای/پایین سوئینگ قبلی و بازگشت

ورودی: DataFrame با ستون‌های open/high/low/close/volume (خروجی indicators.klines_to_df)
همه توابع fail-soft هستند: در نبود داده کافی dict خالی/None برمی‌گردانند.
"""


def find_swings(df, lookback=3):
    """پیدا کردن نقاط سوئینگ های/لو (فرکتال ساده)"""

    highs, lows = df["high"].tolist(), df["low"].tolist()
    swing_highs, swing_lows = [], []

    for i in range(lookback, len(df) - lookback):
        window_h = highs[i - lookback:i + lookback + 1]
        window_l = lows[i - lookback:i + lookback + 1]

        if highs[i] == max(window_h):
            swing_highs.append((i, highs[i]))
        if lows[i] == min(window_l):
            swing_lows.append((i, lows[i]))

    return swing_highs, swing_lows


def detect_structure(df) -> dict:
    """
    تشخیص BOS / CHOCH بر اساس آخرین دو سوئینگ های و لو.
    BOS = شکست ساختار هم‌جهت با روند غالب (ادامه‌دهنده)
    CHOCH = شکست ساختار خلاف روند غالب (احتمال تغییر روند)
    """

    if len(df) < 20:
        return {"signal": None}

    swing_highs, swing_lows = find_swings(df, lookback=3)

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"signal": None}

    last_close = df["close"].iloc[-1]

    last_high_idx, last_high_val = swing_highs[-1]
    prev_high_idx, prev_high_val = swing_highs[-2]
    last_low_idx, last_low_val = swing_lows[-1]
    prev_low_idx, prev_low_val = swing_lows[-2]

    higher_highs = last_high_val > prev_high_val
    higher_lows = last_low_val > prev_low_val
    uptrend_structure = higher_highs and higher_lows

    lower_highs = last_high_val < prev_high_val
    lower_lows = last_low_val < prev_low_val
    downtrend_structure = lower_highs and lower_lows

    signal = None
    detail = ""

    if uptrend_structure and last_close > last_high_val:
        signal = "BOS_BULLISH"
        detail = "شکست ساختار صعودی (BOS) - ادامه روند بالا"
    elif downtrend_structure and last_close < last_low_val:
        signal = "BOS_BEARISH"
        detail = "شکست ساختار نزولی (BOS) - ادامه روند پایین"
    elif downtrend_structure and last_close > last_high_val:
        signal = "CHOCH_BULLISH"
        detail = "تغییر کاراکتر بازار (CHOCH) - احتمال برگشت به صعودی"
    elif uptrend_structure and last_close < last_low_val:
        signal = "CHOCH_BEARISH"
        detail = "تغییر کاراکتر بازار (CHOCH) - احتمال برگشت به نزولی"

    return {
        "signal": signal,
        "detail": detail,
        "last_swing_high": last_high_val,
        "last_swing_low": last_low_val,
    }


def find_order_blocks(df, lookahead_move_pct=1.5) -> dict:
    """
    Order Block ساده: آخرین کندل مخالف (نزولی قبل از حرکت صعودی، یا برعکس)
    قبل از یک حرکت قوی. بازگشت آخرین OB صعودی و نزولی فعال.
    """

    if len(df) < 15:
        return {"bullish_ob": None, "bearish_ob": None}

    bullish_ob, bearish_ob = None, None

    for i in range(len(df) - 10, len(df) - 1):
        if i < 1:
            continue

        candle = df.iloc[i]
        move_start_price = candle["close"]
        move_end_price = df["close"].iloc[min(i + 3, len(df) - 1)]

        if move_start_price == 0:
            continue

        move_pct = (move_end_price - move_start_price) / move_start_price * 100

        is_bearish_candle = candle["close"] < candle["open"]
        is_bullish_candle = candle["close"] > candle["open"]

        if is_bearish_candle and move_pct >= lookahead_move_pct:
            bullish_ob = {"high": round(candle["high"], 8), "low": round(candle["low"], 8), "index": i}

        if is_bullish_candle and move_pct <= -lookahead_move_pct:
            bearish_ob = {"high": round(candle["high"], 8), "low": round(candle["low"], 8), "index": i}

    return {"bullish_ob": bullish_ob, "bearish_ob": bearish_ob}


def find_fair_value_gaps(df, min_gap_pct=0.2) -> list:
    """
    Fair Value Gap: شکاف بین high کندل i-1 و low کندل i+1 (برای FVG صعودی)
    یا بین low کندل i-1 و high کندل i+1 (برای FVG نزولی) که کندل میانی آن را پر نکرده.
    """

    gaps = []
    if len(df) < 5:
        return gaps

    highs, lows, closes = df["high"].tolist(), df["low"].tolist(), df["close"].tolist()

    for i in range(1, len(df) - 1):
        prev_high, prev_low = highs[i - 1], lows[i - 1]
        next_high, next_low = highs[i + 1], lows[i + 1]

        if prev_high <= 0:
            continue

        # FVG صعودی: کف کندل بعدی بالاتر از سقف کندل قبلی
        if next_low > prev_high:
            gap_pct = (next_low - prev_high) / prev_high * 100
            if gap_pct >= min_gap_pct:
                gaps.append({"type": "bullish", "top": round(next_low, 8), "bottom": round(prev_high, 8), "index": i})

        # FVG نزولی: سقف کندل بعدی پایین‌تر از کف کندل قبلی
        if next_high < prev_low:
            gap_pct = (prev_low - next_high) / prev_low * 100
            if gap_pct >= min_gap_pct:
                gaps.append({"type": "bearish", "top": round(prev_low, 8), "bottom": round(next_high, 8), "index": i})

    return gaps[-3:]  # فقط ۳ گپ اخیر مهم است


def detect_liquidity_sweep(df, lookback=15) -> dict:
    """
    Liquidity Sweep: قیمت به‌طور موقت از سوئینگ های/لو قبلی عبور می‌کند
    (شکار استاپ‌لاس‌ها) و سپس در همان یا کندل بعد برمی‌گردد داخل رنج.
    """

    if len(df) < lookback + 3:
        return {"swept": None}

    recent = df.iloc[-(lookback + 3):-2]
    last_candles = df.iloc[-2:]

    prior_high = recent["high"].max()
    prior_low = recent["low"].min()

    for _, candle in last_candles.iterrows():
        if candle["high"] > prior_high and candle["close"] < prior_high:
            return {
                "swept": "high",
                "level": round(prior_high, 8),
                "detail": f"شکار نقدینگی بالای سقف قبلی ({round(prior_high, 8)}) و بازگشت - احتمال SHORT",
            }
        if candle["low"] < prior_low and candle["close"] > prior_low:
            return {
                "swept": "low",
                "level": round(prior_low, 8),
                "detail": f"شکار نقدینگی زیر کف قبلی ({round(prior_low, 8)}) و بازگشت - احتمال LONG",
            }

    return {"swept": None}


def analyze_smc(df, direction: str = "LONG") -> dict:
    """
    ترکیب همه‌ی سیگنال‌های SMC و تولید امتیاز (۰ تا ۲۰) + دلایل/ریسک‌ها.
    """

    if df is None or len(df) < 20:
        return {"score": 0, "reasons": [], "risks": []}

    reasons, risks = [], []
    score = 0.0
    is_long = direction == "LONG"

    structure = detect_structure(df)
    sig = structure.get("signal")
    if sig == "BOS_BULLISH" and is_long:
        score += 7
        reasons.append(structure["detail"])
    elif sig == "BOS_BEARISH" and not is_long:
        score += 7
        reasons.append(structure["detail"])
    elif sig == "CHOCH_BULLISH" and is_long:
        score += 8
        reasons.append(structure["detail"])
    elif sig == "CHOCH_BEARISH" and not is_long:
        score += 8
        reasons.append(structure["detail"])
    elif sig in ("BOS_BEARISH", "CHOCH_BEARISH") and is_long:
        risks.append("ساختار بازار مخالف جهت LONG است")
    elif sig in ("BOS_BULLISH", "CHOCH_BULLISH") and not is_long:
        risks.append("ساختار بازار مخالف جهت SHORT است")

    obs = find_order_blocks(df)
    current_price = df["close"].iloc[-1]

    if is_long and obs.get("bullish_ob"):
        ob = obs["bullish_ob"]
        if ob["low"] * 0.995 <= current_price <= ob["high"] * 1.02:
            score += 5
            reasons.append(f"قیمت نزدیک Order Block صعودی ({ob['low']}-{ob['high']})")

    if not is_long and obs.get("bearish_ob"):
        ob = obs["bearish_ob"]
        if ob["low"] * 0.98 <= current_price <= ob["high"] * 1.005:
            score += 5
            reasons.append(f"قیمت نزدیک Order Block نزولی ({ob['low']}-{ob['high']})")

    gaps = find_fair_value_gaps(df)
    for gap in gaps:
        if is_long and gap["type"] == "bullish" and gap["bottom"] <= current_price <= gap["top"] * 1.03:
            score += 3
            reasons.append(f"داخل Fair Value Gap صعودی ({gap['bottom']}-{gap['top']})")
        if not is_long and gap["type"] == "bearish" and gap["bottom"] * 0.97 <= current_price <= gap["top"]:
            score += 3
            reasons.append(f"داخل Fair Value Gap نزولی ({gap['bottom']}-{gap['top']})")

    sweep = detect_liquidity_sweep(df)
    if sweep.get("swept") == "low" and is_long:
        score += 5
        reasons.append(sweep["detail"])
    elif sweep.get("swept") == "high" and not is_long:
        score += 5
        reasons.append(sweep["detail"])
    elif sweep.get("swept") == "high" and is_long:
        risks.append("شکار نقدینگی بالای سقف - احتمال ریزش کوتاه‌مدت")
    elif sweep.get("swept") == "low" and not is_long:
        risks.append("شکار نقدینگی زیر کف - احتمال رشد کوتاه‌مدت")

    return {
        "score": round(min(score, 20), 1),
        "reasons": reasons,
        "risks": risks,
        "structure_signal": sig,
        "order_blocks": obs,
        "fvgs": gaps,
        "liquidity_sweep": sweep,
    }
