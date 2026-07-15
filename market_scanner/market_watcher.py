import requests


def get_market_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"[Market API Error] Status: {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, list):
            print("[Market API Error] پاسخ معتبر نیست")
            return []

        markets = []

        for item in data:
            if not isinstance(item, dict):
                continue

            symbol = item.get("symbol", "")

            if not symbol.endswith("USDT"):
                continue

            markets.append({
                "symbol": symbol,
                "change": float(item.get("priceChangePercent", 0)),
                "volume": float(item.get("quoteVolume", 0))
            })

        return markets

    except Exception as e:
        print(f"[Market Scanner Error] {e}")
        return []


def find_unusual_moves():

    markets = get_market_data()

    results = []

    for coin in markets:

        if coin["change"] >= 5 and coin["volume"] >= 1000000:
            results.append(coin)

    return results
