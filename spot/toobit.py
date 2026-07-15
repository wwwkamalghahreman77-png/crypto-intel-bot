import requests


BASE_URL = "https://api.toobit.com"


def get_spot_opportunities():

    try:
        url = BASE_URL + "/quote/v1/ticker/24hr"

        response = requests.get(url, timeout=15)

        print("========== TOOBIT SPOT 24HR ==========")
        print("Status:", response.status_code)

        data = response.json()

        if not isinstance(data, list):
            print("[TOOBIT SPOT] DATA NOT LIST")
            return []

        print("[TOOBIT SPOT COUNT]", len(data))

    except Exception as e:
        print("[TOOBIT SPOT ERROR]", e)
        return []

    signals = []

    for coin in data:
        symbol = coin.get("s", "")

        if "USDT" not in symbol:
            continue

        try:
            change_percent = float(coin.get("pcp", 0))
            quote_volume = float(coin.get("qv", 0))
        except:
            continue

        signals.append({
            "symbol": symbol,
            "type": "LONG",
            "change": change_percent,
            "volume": quote_volume,
            "score": 60,
            "reasons": [
                "دریافت قیمت از Toobit Spot",
                "بررسی اولیه بازار"
            ]
        })

    print("[TOOBIT SPOT SIGNALS]", len(signals))

    return signals


def get_klines(symbol, interval="15m", limit=20):
    try:
        url = BASE_URL + "/quote/v1/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        response = requests.get(url, params=params, timeout=15)

        data = response.json()

        if not isinstance(data, list):
            return []

        return data

    except Exception as e:
        print("[TOOBIT SPOT KLINES ERROR]", e)
        return []
