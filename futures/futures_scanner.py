import time
from futures.toobit import get_futures_opportunities, get_klines


STATUS_LABELS = {
    "BREAKOUT_HIGH": "⚡ BREAKOUT - سقف بلندمدت شکسته شد",
    "BOTTOM_REVERSAL": "🔄 BOTTOM REVERSAL - بازگشت از کف بلندمدت",
    "TREND_FLIP_LONG": "📈 TREND FLIP - تغییر روند کلی به سمت لانگ",
    "TREND_FLIP_SHORT": "📉 TREND FLIP - تغییر روند کلی به سمت شورت",
    None: "🔥 PUMP CONFIRMED",
}


def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def is_rising(closes, min_ratio=0.5):
    if len(closes) < 5:
        return False
    rising_count = sum(1 for i in range(1, len(closes)) if closes[i] >= closes[i - 1])
    return (rising_count / (len(closes) - 1)) >= min_ratio


def get_volume_spike_ratio(symbol):
    candles = get_klines(symbol, interval="4h", limit=20)
    if not candles or len(candles) < 10:
        return None
    volumes = [float(c[5]) for c in candles]
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
    last_volume = volumes[-1]
    if avg_volume <= 0:
        return None
    return round(last_volume / avg_volume, 2)


def analyze_price_structure(symbol):
    candles = get_klines(symbol, interval="1d", limit=90)
    if not candles or len(candles) < 30:
        return None

    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]

    current_price = closes[-1]
    lookback_closes = closes[:-1]
    lookback_highs = highs[:-1]
    lookback_lows = lows[:-1]

    prev_high = max(lookback_highs)
    prev_low = min(lookback_lows)

    third = max(1, len(lookback_closes) // 3)
    early_avg = sum(lookback_closes[:third]) / third
    late_avg = sum(lookback_closes[-third:]) / third
    long_term_trend = "up" if late_avg > early_avg else "down"

    recent_closes = closes[-8:]
    recent_trend_up = recent_closes[-1] > recent_closes[0]

    structure_signal = None
    detail = ""

    if current_price > prev_high:
        structure_signal = "BREAKOUT_HIGH"
        detail = f"سقف ۹۰ روزه شکسته شد (سقف قبلی: {round(prev_high, 6)})"
    else:
        was_near_low = any(c <= prev_low * 1.05 for c in closes[-10:-1]) if prev_low > 0 else False
        if was_near_low and recent_trend_up and current_price > closes[-8]:
            structure_signal = "BOTTOM_REVERSAL"
            detail = f"قیمت نزدیک کف ۹۰ روزه بود ({round(prev_low, 6)}) و اکنون بازگشت صعودی دارد"
        elif long_term_trend == "down" and recent_trend_up:
            structure_signal = "TREND_FLIP_LONG"
            detail = "روند بلندمدت نزولی بود، اما روند کوتاه‌مدت به صعودی تغییر کرد"
        elif long_term_trend == "up" and not recent_trend_up:
            structure_signal = "TREND_FLIP_SHORT"
            detail = "روند بلندمدت صعودی بود، اما روند کوتاه‌مدت به نزولی تغییر کرد"

    swing_low_20d = min(lows[-21:-1]) if len(lows) >= 21 else min(lookback_lows)
    swing_high_20d = max(highs[-21:-1]) if len(highs) >= 21 else max(lookback_highs)

    return {
        "current_price": current_price,
        "prev_high_90d": prev_high,
        "prev_low_90d": prev_low,
        "swing_low_20d": swing_low_20d,
        "swing_high_20d": swing_high_20d,
        "long_term_trend": long_term_trend,
        "structure_signal": structure_signal,
        "detail": detail,
    }


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
        }


def confirm_multi_timeframe(symbol, direction="LONG"):
    reasons = []
    risks = []
    score_bonus = 0

    timeframes = ["15m", "1h", "4h", "1d", "1w"]
    tf_results = {}

    for tf in timeframes:
        candles = get_klines(symbol, interval=tf, limit=20)
        if not candles or len(candles) < 8:
            tf_results[tf] = None
            continue
        closes = [float(c[4]) for c in candles]
        tf_results[tf] = {"rising": is_rising(closes), "closes": closes}
        time.sleep(0.1)

    available_count = sum(1 for tf in tf_results.values() if tf is not None)
    if available_count < 3:
        return None

    aligned_count = sum(1 for tf in tf_results.values() if tf and tf["rising"])
    alignment_ratio = aligned_count / available_count

    if alignment_ratio == 1:
        score_bonus += 35
        reasons.append("روند صعودی در تمام تایم‌فریم‌ها هم‌راستاست")
    elif alignment_ratio >= 0.6:
        score_bonus += 20
        reasons.append(f"روند صعودی در اکثر تایم‌فریم‌ها ({aligned_count}/{available_count}) تایید شد")
    else:
        risks.append(f"تایم‌فریم‌ها هم‌راستا نیستند ({aligned_count}/{available_count})")

    rsi = calculate_rsi(tf_results["1h"]["closes"]) if tf_results.get("1h") else None
    if rsi is None:
        return None
    if rsi >= 85:
        risks.append(f"RSI ساعتی بسیار بالا ({rsi}) - ریسک اشباع خرید")
    elif rsi >= 50:
        reasons.append(f"RSI ساعتی در محدوده قدرت روند ({rsi})")

    volume_spike = get_volume_spike_ratio(symbol)
    if volume_spike is None:
        return None

    smart_money_alert = False
    if volume_spike >= 5:
        smart_money_alert = True
        score_bonus += 30
        reasons.append(f"🐋 پول هوشمند شناسایی شد - حجم {volume_spike}× بیشتر از میانگین")
    elif volume_spike >= 2:
        score_bonus += 15
        reasons.append(f"حجم معاملات {volume_spike}× بالاتر از میانگین اخیر")

    structure = analyze_price_structure(symbol)
    if structure is None:
        return None

    if structure["structure_signal"]:
        score_bonus += 25
        reasons.append(structure["detail"])

    trade_levels = calculate_trade_levels(
        structure["current_price"],
        structure["swing_low_20d"],
        structure["swing_high_20d"],
        direction,
    )
    if trade_levels is None:
        return None

    return {
        "score_bonus": score_bonus,
        "rsi": rsi,
        "volume_spike": volume_spike,
        "smart_money_alert": smart_money_alert,
        "structure_signal": structure["structure_signal"],
        "trade_levels": trade_levels,
        "reasons": reasons,
        "risks": risks,
    }


def scan_futures(min_score=70, max_results=15):
    signals = get_futures_opportunities()

    shortlist = []
    for signal in signals:
        score = 0
        reasons = []

        change = signal.get("change", 0)
        volume = signal.get("volume", 0)

        if change >= 15:
            score += 30
            reasons.append(f"جهش قیمت بسیار قوی (+{change}%)")
        elif change >= 8:
            score += 20
            reasons.append(f"جهش قیمت قوی (+{change}%)")
        elif change >= 3:
            score += 10
            reasons.append(f"افزایش قیمت قابل توجه (+{change}%)")
        else:
            continue

        if volume >= 5_000_000:
            score += 25
            reasons.append("حجم معاملات ۲۴ ساعته بسیار بالا")
        elif volume >= 1_000_000:
            score += 15
            reasons.append("حجم معاملات ۲۴ ساعته بالا")
        elif volume >= 200_000:
            score += 5
            reasons.append("حجم معاملات ۲۴ ساعته متوسط")
        else:
            continue

        signal["score"] = score
        signal["reasons"] = reasons
        signal["risks"] = []
        shortlist.append(signal)

    shortlist.sort(key=lambda s: s["score"], reverse=True)
    shortlist = shortlist[:40]

    print(f"[FuturesScanner] {len(shortlist)} کاندید اولیه")

    confirmed_results = []
    for signal in shortlist:
        result = confirm_multi_timeframe(signal["symbol"], direction=signal.get("type", "LONG"))

        if result is None:
            continue

        signal["score"] = min(100, signal["score"] + result["score_bonus"])
        signal["rsi"] = result["rsi"]
        signal["volume_spike_ratio"] = result["volume_spike"]
        signal["smart_money_alert"] = result["smart_money_alert"]
        signal["structure_signal"] = result["structure_signal"]
        signal["status_label"] = STATUS_LABELS.get(result["structure_signal"], STATUS_LABELS[None])
        signal["trade_levels"] = result["trade_levels"]
        signal["reasons"].extend(result["reasons"])
        signal["risks"].extend(result["risks"])

        if signal["score"] >= min_score:
            confirmed_results.append(signal)

    confirmed_results.sort(key=lambda s: s["score"], reverse=True)
    print(f"[FuturesScanner] {len(confirmed_results)} سیگنال نهایی تایید شد")
    return confirmed_results[:max_results]
