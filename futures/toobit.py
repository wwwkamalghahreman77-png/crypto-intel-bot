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


        print(
            "[Toobit Response Type]",
            type(data)
        )


        if isinstance(data, dict):

            print(
                "[Toobit Keys]",
                data.keys()
            )


            # بعضی API ها لیست را داخل data می‌گذارند
            if "data" in data:
                data = data["data"]


            elif "result" in data:
                data = data["result"]



        if not isinstance(data, list):

            print(
                "[Toobit Error] پاسخ لیست نیست"
            )

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



        if volume < 100000:

            continue



        position = (
            "LONG"
            if change > 0
            else "SHORT"
        )



        signals.append({

            "symbol": symbol,

            "type": position,

            "change": change,

            "volume": volume,

            "score": 60,

            "reasons": [
                "حرکت غیرعادی قیمت",
                "حجم معاملات مناسب"
            ]

        })



    print(
        f"[Toobit Futures] {len(signals)} سیگنال پیدا شد"
    )


    return signals
