from market_scanner.market_watcher import find_unusual_moves


def scan_for_signals():
    """
    پیدا کردن فرصت‌های غیرعادی بازار
    """

    coins = find_unusual_moves()

    signals = []

    for coin in coins:

        score = 0
        reasons = []

        # رشد قیمت
        if coin["change"] >= 5:
            score += 30
            reasons.append("افزایش قیمت")

        # حجم بالا
        if coin["volume"] >= 10000000:
            score += 40
            reasons.append("حجم معاملات بالا")
        elif coin["volume"] >= 1000000:
            score += 20
            reasons.append("افزایش حجم")

        if score >= 50:
            signals.append({
                "symbol": coin["symbol"],
                "score": score,
                "reasons": reasons,
                "change": coin["change"],
                "volume": coin["volume"]
            })

    return signals
