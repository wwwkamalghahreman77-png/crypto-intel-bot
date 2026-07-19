"""
analysis/technical.py

تحلیل تکنیکال پایه با داده‌های CoinGecko.
"""

import requests
import pandas as pd

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands


COINGECKO_BASE = (
    "https://api.coingecko.com/api/v3"
)


def fetch_market_chart(
    coin_id: str,
    days: int = 200,
    vs_currency: str = "usd"
):

    url = (
        f"{COINGECKO_BASE}"
        f"/coins/{coin_id}"
        f"/market_chart"
    )

    try:

        resp = requests.get(
            url,
            params={
                "vs_currency": vs_currency,
                "days": days
            },
            timeout=10
        )

        resp.raise_for_status()

        data = resp.json()

        prices = data.get(
            "prices",
            []
        )

        volumes = data.get(
            "total_volumes",
            []
        )

        if not prices:

            return None

        df = pd.DataFrame(
            prices,
            columns=[
                "timestamp",
                "price"
            ]
        )

        if volumes:

            vol_df = pd.DataFrame(
                volumes,
                columns=[
                    "timestamp",
                    "volume"
                ]
            )

            df["volume"] = (
                vol_df["volume"]
                .reindex(
                    range(
                        len(df)
                    )
                )
                .fillna(0)
                .values
            )

        else:

            df["volume"] = 0.0

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df["volume"] = pd.to_numeric(
            df["volume"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "price"
            ]
        )

        return df

    except requests.RequestException as e:

        print(
            f"[Technical] "
            f"خطا در دریافت داده قیمتی "
            f"{coin_id}: {e}"
        )

        return None

    except Exception as e:

        print(
            f"[Technical] "
            f"خطای پردازش داده "
            f"{coin_id}: {e}"
        )

        return None


def analyze_technical(
    coin_id: str
) -> dict:

    df = fetch_market_chart(
        coin_id,
        days=200
    )

    if (
        df is None
        or len(df) < 50
    ):

        return {
            "available": False,
            "reason":
                "داده قیمتی کافی برای تحلیل تکنیکال موجود نیست",
            "score": 0
        }

    try:

        close = df[
            "price"
        ]

        rsi_series = (
            RSIIndicator(
                close=close,
                window=14
            )
            .rsi()
        )

        rsi = rsi_series.iloc[-1]

        macd_calc = MACD(
            close=close
        )

        macd_line = (
            macd_calc
            .macd()
            .iloc[-1]
        )

        macd_signal = (
            macd_calc
            .macd_signal()
            .iloc[-1]
        )

        ema20 = (
            EMAIndicator(
                close=close,
                window=20
            )
            .ema_indicator()
            .iloc[-1]
        )

        ema50 = (
            EMAIndicator(
                close=close,
                window=50
            )
            .ema_indicator()
            .iloc[-1]
        )

        ema100 = (
            EMAIndicator(
                close=close,
                window=min(
                    100,
                    len(close) - 1
                )
            )
            .ema_indicator()
            .iloc[-1]
        )

        ema200 = None

        if len(close) >= 200:

            ema200 = (
                EMAIndicator(
                    close=close,
                    window=200
                )
                .ema_indicator()
                .iloc[-1]
            )

        bb = BollingerBands(
            close=close,
            window=20,
            window_dev=2
        )

        bb_high = (
            bb
            .bollinger_hband()
            .iloc[-1]
        )

        bb_low = (
            bb
            .bollinger_lband()
            .iloc[-1]
        )

        current_price = (
            close.iloc[-1]
        )

        recent_high = (
            close
            .tail(30)
            .max()
        )

        recent_low = (
            close
            .tail(30)
            .min()
        )

        trend = (
            "صعودی"
            if ema20 > ema50
            else "نزولی"
        )

        breakout = (
            current_price
            >= recent_high * 0.99
        )

        score = 0

        if 40 <= rsi <= 65:

            score += 25

        elif rsi < 30:

            score += 15

        if macd_line > macd_signal:

            score += 25

        if ema20 > ema50:

            score += 25

        if breakout:

            score += 25

        return {

            "available": True,

            "rsi": round(
                rsi,
                2
            ),

            "macd_line": round(
                macd_line,
                5
            ),

            "macd_signal": round(
                macd_signal,
                5
            ),

            "ema20": round(
                ema20,
                6
            ),

            "ema50": round(
                ema50,
                6
            ),

            "ema100": round(
                ema100,
                6
            ),

            "ema200":
                round(
                    ema200,
                    6
                )
                if ema200 is not None
                else None,

            "bollinger_high": round(
                bb_high,
                6
            ),

            "bollinger_low": round(
                bb_low,
                6
            ),

            "current_price": round(
                current_price,
                6
            ),

            "recent_high_30d": round(
                recent_high,
                6
            ),

            "recent_low_30d": round(
                recent_low,
                6
            ),

            "trend": trend,

            "breakout": breakout,

            "score": round(
                min(
                    100,
                    score
                ),
                1
            )

        }

    except Exception as e:

        print(
            f"[Technical] "
            f"خطا در تحلیل تکنیکال "
            f"{coin_id}: {e}"
        )

        return {
            "available": False,
            "reason": str(e),
            "score": 0
        }
