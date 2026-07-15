from market_scanner.market_watcher import find_unusual_moves


def scan_for_signals():

    coins = find_unusual_moves()

    signals = []


    for coin in coins:

        score = 0
        reasons = []


        change = coin.get("change", 0)
        volume = coin.get("volume", 0)
        trades = coin.get("trades", 0)


        # حرکت اولیه اما نه پامپ شده
        if 2 <= change <= 15:
            score += 25
            reasons.append("حرکت اولیه قیمت")


        # حذف ارزهایی که قبلا پامپ سنگین کرده‌اند
        if change > 15:
            continue


        # ورود حجم واقعی
        if volume >= 10000000:
            score += 35
            reasons.append("ورود حجم سنگین")

        elif volume >= 3000000:
            score += 20
            reasons.append("افزایش حجم")


        # تعداد معاملات
        if trades >= 50000:
            score += 20
            reasons.append("فعالیت بالای معامله‌گران")


        # فقط سیگنال قوی
        if score >= 70:

            signals.append({

                "symbol": coin["symbol"],

                "type": "LONG",

                "price": coin.get("price",0),

                "score": score,

                "reasons": reasons,

                "change": change,

                "volume": volume

            })


    return signals
