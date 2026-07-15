import requests


BASE_URL = "https://api.toobit.com"


def get_futures_symbols():

    try:

        url = BASE_URL + "/quote/v1/contract/ticker/price"

        response = requests.get(
            url,
            timeout=15
        )

        print("========== TOOBIT FUTURES ==========")
        print("Status:", response.status_code)

        print(response.text[:2000])


        data = response.json()


        if isinstance(data, dict):

            if "data" in data:
                data = data["data"]

            elif "result" in data:
                data = data["result"]


        if not isinstance(data, list):
            return []


        return data


    except Exception as e:

        print(
            "[TOOBIT FUTURES ERROR]",
            e
        )

        return []



def get_futures_opportunities():

    markets = get_futures_symbols()

    signals = []


    for coin in markets:

        if not isinstance(coin, dict):
            continue


        symbol = coin.get(
            "symbol",
            ""
        )


        if not symbol.endswith("USDT"):
            continue


        try:

            price = float(
                coin.get(
                    "price",
                    0
                )
            )


        except:

            continue


        signals.append({

            "symbol": symbol,

            "type": "LONG",

            "change": 0,

            "volume": 0,

            "score": 50,

            "reasons": [
                "دریافت موفق داده از Toobit"
            ]

        })


    print(
        "[TOOBIT FUTURES SIGNALS]",
        len(signals)
    )


    return signals
