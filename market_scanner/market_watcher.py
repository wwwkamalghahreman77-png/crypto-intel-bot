import requests
import json


BASE_URL = "https://api.toobit.com"


def get_market_data():

    url = BASE_URL + "/quote/v1/ticker/24hr"

    try:

        response = requests.get(
            url,
            timeout=15
        )

        print("========== TOOBIT SPOT ==========")
        print("Status:", response.status_code)

        try:
            data = response.json()

        except Exception:

            print(response.text)

            return []

        if isinstance(data, dict):

            if "data" in data:
                data = data["data"]

            elif "result" in data:
                data = data["result"]

            elif "list" in data:
                data = data["list"]

        if not isinstance(data, list):

            print("[Toobit Error] Data is not list")

            return []

        markets = []

        for item in data:

            if not isinstance(item, dict):

                continue

            symbol = item.get("s", "")

            if not symbol.endswith("USDT"):

                continue

            try:

                markets.append({

                    "symbol": symbol,

                    "change": float(item.get("pcp", 0)) * 100,

                    "volume": float(item.get("qv", 0)),

                    "price": float(item.get("c", 0)),

                    "high": float(item.get("h", 0)),

                    "low": float(item.get("l", 0)),

                    "trades": int(item.get("count", 0))

                })

            except Exception:

                continue

        print(f"[Toobit Markets Count] {len(markets)}")

        return markets

    except Exception as e:

        print("[Toobit Market Error]", e)

        return []


def find_unusual_moves():

    markets = get_market_data()

    results = []

    for coin in markets:

        score = 0

        if coin["change"] >= 1:

            score += 20

        if coin["volume"] >= 100000:

            score += 30

        if coin["trades"] >= 1000:

            score += 20

        if coin["high"] > coin["low"]:

            position = (
                coin["price"] - coin["low"]
            ) / (
                coin["high"] - coin["low"]
                + 0.00000001
            )

            if position >= 0.7:

                score += 20

        if score >= 40:

            coin["score"] = score

            coin["reasons"] = [
                "حرکت قیمت",
                "حجم مناسب"
            ]

            results.append(coin)

    print(f"[Toobit Signals] {len(results)}")

    return results
