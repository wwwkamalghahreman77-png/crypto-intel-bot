from market_scanner.market_watcher import find_unusual_moves


def scan_for_signals():

    coins = find_unusual_moves()

    signals = []

    sample = sorted(coins, key=lambda c: c.get("volume", 0), reverse=True)[:5]
    for c in sample:
        print(f"[DEBUG MARKET] {c['symbol']} change={c['change']} volume={c['volume']}")

    for coin in coins:

        score = 0
        reasons = []

        change = coin.get("change", 0)
        volume = coin.get("volume", 0)

        if 2 <= change <= 15:
            score += 25
            reasons.append("حرکت اولیه قیمت")

        if change > 15:
            continue

        if volume >= 1000000:
            score += 35
            reasons.append("ورود حجم سنگین")

        elif volume >= 300000:
            score += 20
            reasons.append("افزایش حجم")

        if score >= 40:

            signals.append({

                "symbol": coin["symbol"],

                "type": "LONG",

                "price": coin.get("price", 0),

                "score": score,

                "reasons": reasons,

                "change": change,

                "volume": volume

            })

    return signals
