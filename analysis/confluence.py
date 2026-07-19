"""
analysis/confluence.py

موتور امتیازدهی کانفلوئنس (Confluence Score) روی مقیاس ۰ تا ۱۰۰.
ترکیب می‌کند:
    - اندیکاتورهای تکنیکال (RSI, MACD, EMAها, Ichimoku, SuperTrend, ADX, CCI, OBV, MFI, CMF, Bollinger, VWAP) → حداکثر ۴۵
    - Smart Money Concepts (BOS/CHOCH, Order Block, FVG, Liquidity Sweep) → حداکثر ۲۰
    - هم‌راستایی چند تایم‌فریمه (Multi Timeframe Confirmation) → حداکثر ۲۰
    - داده تکمیلی (فاندینگ/OI/Long-Short برای فیوچرز، یا حجم/پول هوشمند برای اسپات) → حداکثر ۱۵

تصمیم نهایی بر اساس امتیاز کل:
    >= 55   → SIGNAL      (سیگنال معاملاتی کامل ارسال شود)
    < 55    → REJECT      (سیگنال ضعیف - نادیده گرفته شود)

توجه: ویژگی WATCHLIST (سیگنال‌های نزدیک به تایید) به درخواست کاربر حذف شد -
دیگر پیامی برای این حالت ارسال نمی‌شود و در دیتابیس هم ثبت نمی‌شود.
futures_scanner.py و spot_scanner.py و market_scanner/signal_detector.py
همچنان امتیاز max/avg هر اسکن رو لاگ می‌کنن تا اگه بازم لازم بود، این عدد
را دقیق (نه حدسی) روی داده‌ی واقعی تنظیم کنیم.

علاوه بر امتیاز کانفلوئنس، دو بررسی مستقل دیگر هم روی هر نماد انجام و در
خروجی برگردانده می‌شود (مستقل از SIGNAL/REJECT، چون ممکنه هنوز امتیاز کامل
نگرفته باشن ولی الگوی رفتاری مهمی نشون بدن):
    - catalyst_breakout: الگوی جهش شبیه AKE/BANK (پایه‌ی فشرده + جهش حجم + شکست + رشد اخیر)
    - trendline_break: شکست خط روند بلندمدت (۹۰ و ۱۸۰ روزه)
"""

import time
from analysis.indicators import klines_to_df, compute_indicators, score_indicator_bundle
from analysis.smc import analyze_smc
from analysis.catalyst_breakout import analyze_catalyst_breakout
from analysis.trendline import detect_trendline_break

MIN_SIGNAL_SCORE = 55

TIMEFRAMES_MTF = ["15m", "1h", "4h", "1d", "1w"]


def _is_rising(closes, min_ratio=0.55):
    if len(closes) < 5:
        return False
    rising = sum(1 for i in range(1, len(closes)) if closes[i] >= closes[i - 1])
    return (rising / (len(closes) - 1)) >= min_ratio


def _mtf_alignment_score(get_klines_fn, symbol, direction) -> dict:
    """هم‌راستایی روند در چند تایم‌فریم؛ حداکثر ۲۰ امتیاز"""

    is_long = direction == "LONG"
    tf_results = {}

    for tf in TIMEFRAMES_MTF:
        candles = get_klines_fn(symbol, interval=tf, limit=25)
        if not candles or len(candles) < 8:
            tf_results[tf] = None
            continue
        closes = [float(c[4]) for c in candles]
        rising = _is_rising(closes)
        tf_results[tf] = rising if is_long else (not rising)
        time.sleep(0.1)

    available = [v for v in tf_results.values() if v is not None]
    if len(available) < 3:
        return {"score": 0, "reasons": [], "risks": ["داده تایم‌فریم کافی نبود"], "aligned_count": 0, "available_count": 0}

    aligned = sum(1 for v in available if v)
    ratio = aligned / len(available)

    reasons, risks = [], []
    if ratio == 1:
        score = 20
        reasons.append("روند در تمام تایم‌فریم‌ها هم‌راستاست")
    elif ratio >= 0.6:
        score = 12
        reasons.append(f"روند در اکثر تایم‌فریم‌ها هم‌راستاست ({aligned}/{len(available)})")
    else:
        score = 0
        risks.append(f"تایم‌فریم‌ها هم‌راستا نیستند ({aligned}/{len(available)})")

    return {"score": score, "reasons": reasons, "risks": risks, "aligned_count": aligned, "available_count": len(available)}


def _default_volume_bonus(signal_meta: dict, direction: str) -> dict:
    """جایگزین بخش مشتقات برای بازار اسپات: بر اساس حجم و تغییر قیمت ۲۴ساعته"""

    reasons, risks = [], []
    score = 0.0

    volume = signal_meta.get("volume", 0)
    change = signal_meta.get("change", 0)

    if volume >= 10_000_000:
        score += 8
        reasons.append("حجم معاملات ۲۴ ساعته بسیار بالا")
    elif volume >= 3_000_000:
        score += 5
        reasons.append("حجم معاملات ۲۴ ساعته بالا")
    elif volume >= 500_000:
        score += 2

    if abs(change) >= 15:
        score += 7
        reasons.append(f"جهش قیمت شدید ({change}%)")
    elif abs(change) >= 7:
        score += 4
        reasons.append(f"جهش قیمت قابل توجه ({change}%)")

    return {"score": round(min(score, 15), 1), "reasons": reasons, "risks": risks, "whale_alert": volume >= 10_000_000}


def calculate_trade_levels(current_price, swing_low, swing_high, direction):

    if direction == "LONG":
        stop_loss = round(swing_low * 0.98, 8)
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
    else:
        stop_loss = round(swing_high * 1.02, 8)
        risk = stop_loss - current_price
        if risk <= 0:
            return None
        return {
            "entry": round(current_price, 8),
            "stop_loss": stop_loss,
            "tp1": round(current_price - risk * 1, 8),
            "tp2": round(current_price - risk * 2, 8),
            "tp3": round(current_price - risk * 3, 8),
            "tp4": round(current_price - risk * 4, 8),
        }


def run_confluence_analysis(symbol, get_klines_fn, signal_meta: dict, direction="LONG", extra_analyzer=None, min_signal_score=None) -> "dict | None":
    """
    تحلیل کامل کانفلوئنس یک نماد.

    get_klines_fn: تابع get_klines(symbol, interval, limit) بورس (فیوچرز یا اسپات توبیت)
    signal_meta: دیکشنری اولیه سیگنال (symbol, type, change, volume, ...)
    extra_analyzer: تابع اختیاری (symbol, direction) -> dict با score/reasons/risks (مثل derivatives.analyze_derivatives)
    min_signal_score: اختیاری - اگر پاس داده نشود، از مقدار پیش‌فرض ماژول (MIN_SIGNAL_SCORE)
        استفاده می‌شود. برای اینکه یک بازار (مثلا فیوچرز) بتواند سخت‌گیرتر از بقیه باشد،
        بدون تغییر آستانه‌ی مشترک.
    """

    primary_candles = get_klines_fn(symbol, interval="4h", limit=100)
    structure_candles = get_klines_fn(symbol, interval="1d", limit=90)

    primary_df = klines_to_df(primary_candles)
    structure_df = klines_to_df(structure_candles)

    if primary_df is None or structure_df is None or len(structure_df) < 30:
        return None

    reasons, risks = [], []
    total_score = 0.0

    # ۱) اندیکاتورهای تکنیکال روی تایم‌فریم ۴ ساعته (حداکثر ۴۵)
    ind = compute_indicators(primary_df)
    ind_result = score_indicator_bundle(ind, direction=direction)
    total_score += ind_result["score"]
    reasons.extend(ind_result["reasons"])
    risks.extend(ind_result["risks"])

    # ۲) Smart Money Concepts روی تایم‌فریم روزانه (حداکثر ۲۰)
    smc_result = analyze_smc(structure_df, direction=direction)
    total_score += smc_result["score"]
    reasons.extend(smc_result["reasons"])
    risks.extend(smc_result["risks"])

    # ۳) هم‌راستایی چند تایم‌فریمه (حداکثر ۲۰)
    mtf_result = _mtf_alignment_score(get_klines_fn, symbol, direction)
    total_score += mtf_result["score"]
    reasons.extend(mtf_result["reasons"])
    risks.extend(mtf_result["risks"])

    # ۴) داده تکمیلی: مشتقات (فیوچرز) یا حجم/پول هوشمند (اسپات) - حداکثر ۱۵
    if extra_analyzer:
        extra_result = extra_analyzer(symbol, direction)
    else:
        extra_result = _default_volume_bonus(signal_meta, direction)

    total_score += extra_result.get("score", 0)
    reasons.extend(extra_result.get("reasons", []))
    risks.extend(extra_result.get("risks", []))

    total_score = round(min(total_score, 100), 1)

    # سطوح معامله بر اساس سوئینگ ۲۰ روزه
    closes = structure_df["close"].tolist()
    highs = structure_df["high"].tolist()
    lows = structure_df["low"].tolist()

    current_price = closes[-1]
    swing_low_20d = min(lows[-21:-1]) if len(lows) >= 21 else min(lows[:-1])
    swing_high_20d = max(highs[-21:-1]) if len(highs) >= 21 else max(highs[:-1])

    trade_levels = calculate_trade_levels(current_price, swing_low_20d, swing_high_20d, direction)

    signal_bar = min_signal_score if min_signal_score is not None else MIN_SIGNAL_SCORE

    decision = "SIGNAL" if total_score >= signal_bar else "REJECT"

    # ۵) الگوی جهش کاتالیزوری شبیه AKE/BANK (از همان structure_df، بدون فراخوانی اضافه API)
    catalyst_result = analyze_catalyst_breakout(structure_df)

    # ۶) شکست خط روند بلندمدت - نیازمند تاریخچه‌ی طولانی‌تر (۲۰۰ کندل روزانه)
    long_term_candles = get_klines_fn(symbol, interval="1d", limit=200)
    long_term_df = klines_to_df(long_term_candles)
    trendline_result = detect_trendline_break(long_term_df)

    return {
        "symbol": symbol,
        "direction": direction,
        "score": total_score,
        "decision": decision,
        "reasons": reasons[:8],
        "risks": risks[:5],
        "trade_levels": trade_levels,
        "current_price": round(current_price, 8),
        "structure_signal": smc_result.get("structure_signal"),
        "smart_money_alert": extra_result.get("whale_alert", False),
        "funding_rate": extra_result.get("funding_rate"),
        "open_interest": extra_result.get("open_interest"),
        "long_short_ratio": extra_result.get("long_short_ratio"),
        "catalyst_breakout": catalyst_result,
        "trendline_break": trendline_result,
        "breakdown": {
            "indicators": ind_result["score"],
            "smc": smc_result["score"],
            "mtf": mtf_result["score"],
            "extra": extra_result.get("score", 0),
        },
    }
    
