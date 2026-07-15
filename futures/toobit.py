import os
import requests


BASE_URL = "https://api.toobit.com"


ACCESS_KEY = os.getenv("TOOBIT_ACCESS_KEY", "")
SECRET_KEY = os.getenv("TOOBIT_SECRET_KEY", "")



def get_futures_symbols():

    try:

        url = BASE_URL + "/api/v1/futures/market/tickers"


        headers = {
            "X-BB-ACCESSKEY": ACCESS_KEY
        }


        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )


        print("========== TOOBIT FUTURES ==========")
        print("Status:", response.status_code)


        data = response.json()



        if isinstance(data, dict):

            if "data" in data:
                data = data["data"]

            elif "result" in data:
                data = data["result"]

            elif "list" in data:
                data = data["list"]



        if not isinstance(data, list):

            print(
                "[Toobit Futures] داده معتبر نیست"
            )

            return []



        return data



    except Exception as e:

        print(
            "[Toobit Futures Error]",
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

            change = float(
                coin.get(
                    "priceChangePercent",
                    coin.get(
                        "changePercent",
                        0
                    )
                )
            )


            volume = float(
                coin.get(
                    "quoteVolume",
                    coin.get(
                        "volume",
                        0
                    )
                )
            )


        except:

            continue



        if abs(change) < 1:

            continue



        signals.append({

            "symbol": symbol,

            "type":
                "LONG"
                if change > 0
                else "SHORT",

            "change": change,

            "volume": volume,

            "score": 60,

            "reasons": [
                "حرکت غیرعادی قیمت",
                "حجم مناسب"
            ]

        })



    print(
        f"[Toobit Futures] {len(signals)} سیگنال"
    )


    return signals
