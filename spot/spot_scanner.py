import time
from spot.toobit import get_spot_opportunities, get_klines


def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None

    gains = []
    losses = []

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


def confirm_multi_timeframe(symbol):
    reasons = []
    risks = []
    score_bonus = 0

    tf_results = {}
    for tf in ["15m", "1h", "4h"]:
        candles = get_klines(symbol, interval=tf, limit=20)
        if not candles or len(candles) < 10:
            tf_results[tf] = None
            continue
        closes = [float(c[4]) for c in candles]
        tf_results[tf] = {
            "rising": is_rising(closes),
            "closes": closes,
        }
        time.sleep(0.1)

    aligned_count = sum(1 for tf in tf_results.values() if tf and tf["rising"])

    if aligned_count == 3:
        score_bonus += 30
        reasons.append("روند صعودی در هر ۳ تایم‌فریم (۱۵د/۱ساعت/۴ساعت) هم‌راستاست")
    elif aligned_count == 2:
        score_bonus += 15
        reasons.append("روند صعودی در ۲ از ۳ تایم‌فریم تایید شد")
    else:
        risks.append("تایم‌فریم‌های مختلف روند یکسانی نشان نمی‌دهند (احتمال نوسان کاذب)")

    rsi = None
    if tf_results.get("1h"):
        rsi = calculate_rsi(tf_results["1h"]["closes"])
        if rsi is not None:
            if rsi >= 85:
                risks.append(f"RSI ساعتی بسیار بالا ({rsi}) - ریسک اشباع خرید")
            elif rsi >= 50:
                reasons.append(f"RSI ساعتی در محدوده قدرت روند ({rsi})")

    volume_spike = get_volume_spike_ratio(symbol)
    if volume_spike is not None:
        if volume_spike >= 5:
            score_bonus += 30
            reasons.append(f"حجم معاملات {volume_spike}× بیشتر از میانگین اخیر (احتمال ورود نقدینگی جدید)")
        elif volume_spike >= 2:
            score_bonus += 15
            reasons.append(f"حجم معاملات {volume_spike}× بالاتر از میانگین اخیر")

    return score_bonus, rsi, volume_spike, reasons, risks


def scan_spot(min_score=70, max_results=15):
    signals = get_spot_opportunities()

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

        if volume >= 50_000_000:
            score += 25
            reasons.append("حجم معاملات ۲۴ ساعته بسیار بالا")
        elif volume >= 10_000_000:
            score += 15
            reasons.append("حجم معاملات ۲۴ ساعته بالا")
        elif volume >= 1_000_000:
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

    print(f"[SpotScanner] {len(shortlist)} کاندید برای تحلیل چندتایم‌فریمی")

    confirmed_results = []

    for signal in shortlist:
        bonus, rsi, vol_spike, mt_reasons, mt_risks = confirm_multi_timeframe(signal["symbol"])

        signal["score"] += bonus
        signal["rsi"] = rsi
        signal["volume_spike_ratio"] = vol_spike
        signal["reasons"].extend(mt_reasons)
        signal["risks"].extend(mt_risks)

        if signal["score"] >= min_score:
            confirmed_results.append(signal)

    confirmed_results.sort(key=lambda s: s["score"], reverse=True)
    print(f"[SpotScanner] {len(confirmed_results)} سیگنال نهایی تایید شد")
    return confirmed_results[:max_results]
