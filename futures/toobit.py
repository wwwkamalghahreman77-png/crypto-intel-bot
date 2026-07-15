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


        data = response.json()


        if not isinstance(data, list):

            print("[TOOBIT] DATA NOT LIST")

            return []


        print(
            "[TOOBIT COUNT]",
            len(data)
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


        symbol = coin.get(
            "s",
            ""
        )


        if "USDT" not in symbol:

            continue



        try:

            price = float(
                coin.get(
                    "p",
                    0
                )
            )


        except:

            continue



        if price <= 0:

            continue



        signals.append({

            "symbol": symbol,

            "type": "LONG",

            "change": 0,

            "volume": 0,

            "score": 60,

            "reasons": [

                "دریافت قیمت از Toobit Futures",

                "بررسی اولیه بازار"

            ]

        })



    print(
        "[TOOBIT FUTURES SIGNALS]",
        len(signals)
    )


    return signals
