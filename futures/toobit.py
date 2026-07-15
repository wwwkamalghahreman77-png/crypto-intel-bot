import os
import requests


BASE_URL = "https://api.toobit.com"

ACCESS_KEY = os.getenv("TOOBIT_ACCESS_KEY", "")


def get_futures_symbols():

    try:

        url = BASE_URL + "/api/v1/futures/market/tickers"

        headers = {
            "X-BB-ACCESSKEY": ACCESS_KEY
        }

        r = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        print("TOOBIT STATUS:", r.status_code)

        print("TOOBIT TEXT:", r.text[:1000])

        data = r.json()


        if isinstance(data, dict):

            data = (
                data.get("data")
                or data.get("result")
                or data.get("list")
                or []
            )


        if isinstance(data, list):
            return data


        return []


    except Exception as e:

        print("TOOBIT ERROR:", e)

        return []



def get_futures_opportunities():

    markets = get_futures_symbols()

    signals = []


    for coin in markets:

        symbol = coin.get("symbol", "")


        if not symbol.endswith("USDT"):
            continue


        try:

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


        except:

            continue



        if abs(change) < 0.5:
            continue



        signals.append(
            {
                "symbol": symbol,
                "type": "LONG" if change > 0 else "SHORT",
                "change": change,
                "volume": volume,
                "score": 60,
                "reasons": [
                    "حرکت قیمت"
                ]
            }
        )


    print(
        "FUTURES SIGNALS:",
        len(signals)
    )


    return signals
