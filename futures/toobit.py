import requests


BASE_URL = "https://api.toobit.com"


def get_futures_symbols():

    try:
        url = BASE_URL + "/api/v1/futures/market/tickers"

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        if not isinstance(data, list):
            return []

        return data


    except Exception as e:

        print(
            f"[Toobit Futures Error] {e}"
        )

        return []



def get_futures_opportunities():

    markets = get_futures_symbols()

    signals = []


    for coin in markets:

        symbol = coin.get(
            "symbol",
            ""
        )


        if not symbol.endswith("USDT"):
            continue


        change = float(
            coin.get(
                "priceChangePercent",
                0
            )
        )


        volume = float(
            coin.get(
                "quoteVolume",
                0
            )
        )


        if abs(change) < 3:
            continue


        if volume < 1000000:
            continue



        position = "LONG" if change > 0 else "SHORT"


        signals.append({

            "symbol": symbol,

            "type": position,

            "change": change,

            "volume": volume,

            "score": 60

        })


    return signals
