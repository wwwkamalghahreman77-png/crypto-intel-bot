from futures.toobit import get_futures_opportunities


def scan_futures():

    signals = get_futures_opportunities()

    results = []


    for signal in signals:

        score = 0
        reasons = []


        change = signal.get("change", 0)
        volume = signal.get("volume", 0)


        if abs(change) >= 3:
            score += 30
            reasons.append("حرکت قوی قیمت")


        if volume >= 10000000:
            score += 40
            reasons.append("حجم بالای معاملات")


        elif volume >= 1000000:
            score += 20
            reasons.append("افزایش حجم")


        if score >= 20:

            signal["score"] = score

            signal["reasons"] = reasons

            results.append(signal)


    return results
