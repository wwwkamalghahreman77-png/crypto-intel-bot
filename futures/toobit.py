import requests


BASE_URL = "https://api.toobit.com"


def get_futures_opportunities():

    try:
        url = BASE_URL + "/quote/v1/contract/ticker/24hr"

        response = requests.get(url, timeout=15)

        print("========== TOOBIT FUTURES 24HR ==========")
        print("Status:", response.status_code)

        data = response.json()

        if not isinstance(data, list):
            print("[TOOBIT] DATA NOT LIST")
            return []

        print("[TOOBIT COUNT]", len(data))

    except Exception as e:
        print("[TOOBIT FUTURES ERROR]", e)
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
            "type": "LONG" if change_percent >= 0 else "SHORT",
            "change": change_percent,
            "volume": quote_volume,
            "score": 60,
            "reasons": [
                "دریافت قیمت از Toobit Futures",
                "بررسی اولیه بازار"
            ]
        })

    print("[TOOBIT FUTURES SIGNALS]", len(signals))

    return signals


def get_klines(symbol, interval="15m", limit=20):
    try:
        url = BASE_URL + "/quote/v1/contract/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        response = requests.get(url, params=params, timeout=15)
        payload = response.json()

        raw = payload.get("data", []) if isinstance(payload, dict) else payload
        if not isinstance(raw, list):
            return []

        candles = []
        for item in raw:
            candles.append([
                item.get("time"),
                item.get("open"),
                item.get("high"),
                item.get("low"),
                item.get("close"),
                item.get("volume"),
            ])
        return candles

    except Exception as e:
        print("[TOOBIT FUTURES KLINES ERROR]", e)
        return []
