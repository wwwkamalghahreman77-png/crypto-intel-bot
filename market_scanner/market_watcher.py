import requests


def get_market_data():

    url = "https://api.binance.com/api/v3/ticker/24hr"

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:
            print(
                f"[Market API Error] Status: {response.status_code}"
            )
            return []


        data = response.json()


        if not isinstance(data, list):

            print(
                "[Market API Error] پاسخ معتبر نیست"
            )

            return []


        markets = []


        for item in data:


            if not isinstance(item, dict):
                continue


            symbol = item.get(
                "symbol",
                ""
            )


            if not symbol.endswith("USDT"):
                continue



            markets.append({

                "symbol": symbol,

                "change": float(
                    item.get(
                        "priceChangePercent",
                        0
                    )
                ),

                "volume": float(
                    item.get(
                        "quoteVolume",
                        0
                    )
                ),

                "price": float(
                    item.get(
                        "lastPrice",
                        0
                    )
                ),

                "high": float(
                    item.get(
                        "highPrice",
                        0
                    )
                ),

                "low": float(
                    item.get(
                        "lowPrice",
                        0
                    )
                ),

                "trades": int(
                    item.get(
                        "count",
                        0
                    )
                )

            })


        return markets



    except Exception as e:

        print(
            f"[Market Scanner Error] {e}"
        )

        return []




def find_unusual_moves():


    markets = get_market_data()


    results = []


    for coin in markets:


        score = 0


        # حرکت اولیه قیمت
        if coin["change"] >= 2:
            score += 20


        # حجم بالا
        if coin["volume"] >= 10000000:
            score += 40

        elif coin["volume"] >= 1000000:
            score += 20



        # تعداد معاملات بالا
        if coin["trades"] >= 50000:
            score += 20



        # نزدیک سقف روزانه (قدرت حرکت)
        if coin["high"] > 0:

            position = (
                coin["price"] - coin["low"]
            ) / (
                coin["high"] - coin["low"]
                + 0.00000001
            )

            if position >= 0.8:
                score += 20



        if score >= 50:

            coin["score"] = score

            results.append(coin)



    return results
