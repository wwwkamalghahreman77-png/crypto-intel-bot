from market_scanner.market_watcher import find_unusual_moves


def scan_for_signals(min_score=75):

    coins = find_unusual_moves()

    signals = []

    for coin in coins:

        score = 0
        reasons = []

        change = coin.get("change", 0)
        volume = coin.get("volume", 0)

        # قدرت حرکت قیمت
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

        # حجم معاملات
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

        # پاداش ترکیبی: هم قیمت و هم حجم قوی باشند
        if change >= 10 and volume >= 3_000_000:
            score += 20
            reasons.append("هم‌راستایی قیمت و حجم")

        score = min(100, score)

        if score >= min_score:

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
