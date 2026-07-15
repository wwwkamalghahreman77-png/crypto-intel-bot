import requests


BASE_URL = "https://api.toobit.com"


def get_market_data():

    url = BASE_URL + "/api/v1/spot/market/tickers"

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            print(
                f"[Toobit Market Error] Status: {response.status_code}"
            )

            return []


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
                "[Toobit Market Error] پاسخ معتبر نیست"
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



            try:

                markets.append({

                    "symbol": symbol,

                    "change": float(
                        item.get(
                            "priceChangePercent",
                            item.get(
                                "changePercent",
                                0
                            )
                        )
                    ),

                    "volume": float(
                        item.get(
                            "quoteVolume",
                            item.get(
                                "volume",
                                0
                            )
                        )
                    ),

                    "price": float(
                        item.get(
                            "lastPrice",
                            item.get(
                                "price",
                                0
                            )
                        )
                    ),

                    "high": float(
                        item.get(
                            "highPrice",
                            item.get(
                                "high",
                                0
                            )
                        )
                    ),

                    "low": float(
                        item.get(
                            "lowPrice",
                            item.get(
                                "low",
                                0
                            )
                        )
                    ),

                    "trades": int(
                        item.get(
                            "count",
                            0
                        )
                    )

                })


            except Exception:

                continue



        return markets



    except Exception as e:

        print(
            f"[Toobit Market Scanner Error] {e}"
        )

        return []





def find_unusual_moves():


    markets = get_market_data()


    results = []



    for coin in markets:


        score = 0



        if coin["change"] >= 2:

            score += 20



        if coin["volume"] >= 10000000:

            score += 40


        elif coin["volume"] >= 1000000:

            score += 20



        if coin["trades"] >= 50000:

            score += 20



        if coin["high"] > coin["low"]:


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



    print(
        f"[Toobit Market Scanner] {len(results)} فرصت پیدا شد"
    )


    return results
