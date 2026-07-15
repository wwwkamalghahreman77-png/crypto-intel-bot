import requests


def get_market_data():
    """
    دریافت لیست ارزهایی که بیشترین تغییرات بازار را دارند
    """

    url = "https://api.binance.com/api/v3/ticker/24hr"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        markets = []

        for item in data:
            symbol = item.get("symbol", "")

            if not symbol.endswith("USDT"):
                continue

            change = float(item.get("priceChangePercent", 0))
            volume = float(item.get("quoteVolume", 0))

            markets.append({
                "symbol": symbol,
                "change": change,
                "volume": volume
            })

        return markets

    except Exception as e:
        print(f"[Market Scanner Error] {e}")
        return []


def find_unusual_moves():

    markets = get_market_data()

    results = []

    for coin in markets:

        # حرکت غیرعادی اولیه
        if coin["change"] >= 5 and coin["volume"] >= 1000000:
            results.append(coin)

    return results
