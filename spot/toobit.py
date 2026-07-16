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

        # --- تشخیص مقیاس pcp و qv ---
        if data:
            changes = []
            volumes = []
            for c in data:
                try:
                    changes.append(float(c.get("pcp", 0)))
                    volumes.append(float(c.get("qv", 0)))
                except:
                    pass
            if changes:
                max_change = max(changes, key=abs)
                count_change_ge_3 = sum(1 for x in changes if abs(x) >= 3)
                count_vol_ge_1m = sum(1 for v in volumes if v >= 1_000_000)
                count_both = sum(1 for x, v in zip(changes, volumes) if abs(x) >= 3 and v >= 1_000_000)
                print(f"[SPOT STATS] max|change|={max_change} | count|change|>=3: {count_change_ge_3} | count volume>=1M: {count_vol_ge_1m} | count both: {count_both}")
        # --- پایان تشخیص ---

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
