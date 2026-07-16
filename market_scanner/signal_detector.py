from market_scanner.market_watcher import find_unusual_moves
from spot.spot_scanner import confirm_multi_timeframe, STATUS_LABELS


def scan_for_signals(min_score=75, max_results=15):

    coins = find_unusual_moves()

    shortlist = []

    for coin in coins:

        score = 0
        reasons = []

        change = coin.get("change", 0)
        volume = coin.get("volume", 0)

        if change >= 20:
            score += 40
            reasons.append("جهش بسیار قوی قیمت")
        elif change >= 10:
            score += 30
            reasons.append("جهش قوی قیمت")
        elif change >= 5:
            score += 20
            reasons.append("حرکت قابل‌توجه قیمت")
        elif change >= 2:
            score += 10
            reasons.append("حرکت اولیه قیمت")
        else:
            continue

        if volume >= 10_000_000:
            score += 40
            reasons.append("حجم فوق‌سنگین")
        elif volume >= 3_000_000:
            score += 30
            reasons.append("حجم سنگین")
        elif volume >= 1_000_000:
            score += 20
            reasons.append("حجم بالا")
        elif volume >= 300_000:
            score += 10
            reasons.append("حجم متوسط")
        else:
            continue

        if change >= 10 and volume >= 3_000_000:
            score += 20
            reasons.append("هم‌راستایی قیمت و حجم")

        score = min(100, score)

        coin["score"] = score
        coin["reasons"] = reasons
        coin["risks"] = []
        coin["type"] = "LONG"

        shortlist.append(coin)

    shortlist.sort(key=lambda s: s["score"], reverse=True)
    shortlist = shortlist[:40]

    print(f"[MarketScanner] {len(shortlist)} کاندید اولیه")

    confirmed_results = []

    for signal in shortlist:

        result = confirm_multi_timeframe(signal["symbol"], direction="LONG")

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
        signal["risks"] = result["risks"]

        if signal["score"] >= min_score:
            confirmed_results.append(signal)

    confirmed_results.sort(key=lambda s: s["score"], reverse=True)

    print(f"[MarketScanner] {len(confirmed_results)} سیگنال نهایی تایید شد")

    return confirmed_results[:max_results]
