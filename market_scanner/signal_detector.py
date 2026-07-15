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

        change = coin.get("change", 0)
        volume = coin.get("volume", 0)

        # حرکت قیمت
        if change >= 3:
            score += 20
            reasons.append("حرکت قیمتی مثبت")

        # حجم غیرعادی
        if volume >= 10000000:
            score += 40
            reasons.append("ورود حجم سنگین")

        elif volume >= 1000000:
            score += 25
            reasons.append("افزایش حجم معاملات")

        # خریدهای سنگین
        if coin.get("buys", 0) > coin.get("sells", 0):
            score += 20
            reasons.append("قدرت خریدار بیشتر است")

        # نقدینگی
        if coin.get("liquidity", 0) >= 500000:
            score += 20
            reasons.append("نقدینگی مناسب")


        if score >= 50:

            signals.append({

                "symbol": coin["symbol"],

                "type": (
                    "LONG"
                    if change >= 0
                    else "SHORT"
                ),

                "price": coin.get("price", 0),

                "score": score,

                "reasons": reasons,

                "change": change,

                "volume": volume

            })


    return signals
