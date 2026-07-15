import requests
import json

BASE_URL = "https://api.toobit.com"


def get_futures_symbols():

    try:

        url = BASE_URL + "/api/v1/futures/market/tickers"

        response = requests.get(
            url,
            timeout=15
        )

        print("========== TOOBIT ==========")
        print("Status:", response.status_code)

        try:
            data = response.json()
        except Exception:
            print(response.text)
            return []

        print(json.dumps(data, indent=2)[:5000])
        print("========== END ==========")

        if isinstance(data, dict):

            if "data" in data:
                data = data["data"]

            elif "result" in data:
                data = data["result"]

            elif "list" in data:
                data = data["list"]

        if not isinstance(data, list):
            return []

        return data

    except Exception as e:

        print("[TOOBIT ERROR]", e)

        return []



def get_futures_opportunities():

    markets = get_futures_symbols()

    signals = []

    for coin in markets:

        if not isinstance(coin, dict):
            continue

        symbol = coin.get("symbol", "")

        if not symbol.endswith("USDT"):
            continue

        try:

            change = float(
                coin.get(
                    "priceChangePercent",
                    coin.get("changePercent", 0)
                )
            )

            volume = float(
                coin.get(
                    "quoteVolume",
                    coin.get("volume", 0)
                )
            )

        except Exception:
            continue

        if abs(change) < 1:
            continue

        signals.append({

            "symbol": symbol,
            "type": "LONG" if change > 0 else "SHORT",
            "change": change,
            "volume": volume,
            "score": 60,
            "reasons": [
                "تست اتصال Toobit"
            ]
