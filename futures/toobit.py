import os
import requests
import json


BASE_URL = "https://api.toobit.com"


ACCESS_KEY = os.getenv("TOOBIT_ACCESS_KEY", "")



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


        try:

            data = response.json()

        except Exception:

            print(response.text)

            return []



        print(
            "[TOOBIT FUTURES DATA]"
        )

        print(
            json.dumps(
                data,
                indent=2
            )[:5000]
        )



        if isinstance(data, dict):

            if "data" in data:

                data = data["data"]

            elif "result" in data:

                data = data["result"]

            elif "list" in data:

                data = data["list"]



        if not isinstance(data, list):

            print(
                "[TOOBIT FUTURES] لیست دریافت نشد"
            )

            return []



        print(
            f"[TOOBIT FUTURES COUNT] {len(data)}"
        )


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


        except Exception:

            continue



        # تست اولیه؛ فیلتر سخت نیست

        if abs(change) < 0.5:

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
                "
