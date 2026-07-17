"""
analysis/confluence.py

Confluence Engine v2

ترکیب:
- Technical Indicators (45)
- Smart Money Concepts (20)
- Multi Timeframe Confirmation (20)
- Market Data / Derivatives (15)

Decision:
>=80  SIGNAL
60-79 WATCHLIST
<60   REJECT
"""

from typing import Optional
import math

from analysis.indicators import (
    klines_to_df,
    compute_indicators,
    score_indicator_bundle
)

from analysis.smc import analyze_smc


MIN_SIGNAL_SCORE = 55
MIN_WATCHLIST_SCORE = 35

TIMEFRAMES_MTF = [
    "15m",
    "1h",
    "4h",
    "1d"
]


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _is_rising(closes, ratio=0.55):

    if len(closes) < 5:
        return False

    ups = 0

    for i in range(1, len(closes)):
        if closes[i] >= closes[i - 1]:
            ups += 1

    return (ups / (len(closes)-1)) >= ratio


def _atr(df, period=14):

    try:
        highs = df["high"].tolist()
        lows = df["low"].tolist()
        closes = df["close"].tolist()

        trs = []

        for i in range(1, len(closes)):

            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )

            trs.append(tr)

        if len(trs) < period:
            return None

        return sum(trs[-period:]) / period

    except Exception:
        return None


def _calculate_trade_levels(
        current_price,
        df,
        direction
):

    atr = _atr(df)

    if not atr or atr <= 0:
        atr = current_price * 0.03


    # محدود کردن ATR غیرمنطقی
    atr_percent = atr / current_price

    if atr_percent > 0.25:
        atr = current_price * 0.08


    risk_distance = atr * 1.5


    if direction == "LONG":

        stop_loss = current_price - risk_distance

        if stop_loss <= 0:
            stop_loss = current_price * 0.92


        levels = {

            "entry": round(current_price,8),

            "stop_loss": round(stop_loss,8),

            "tp1": round(current_price + risk_distance,8),

            "tp2": round(current_price + risk_distance*2,8),

            "tp3": round(current_price + risk_distance*3,8),

            "tp4": round(current_price + risk_distance*4,8)
        }


    else:

        stop_loss = current_price + risk_distance


        levels = {

            "entry": round(current_price,8),

            "stop_loss": round(stop_loss,8),

            "tp1": round(
                max(current_price-risk_distance,0.00000001),
                8
            ),

            "tp2": round(
                max(current_price-risk_distance*2,0.00000001),
                8
            ),

            "tp3": round(
                max(current_price-risk_distance*3,0.00000001),
                8
            ),

            "tp4": round(
                max(current_price-risk_distance*4,0.00000001),
                8
            )
        }


    return levels


def _mtf_alignment_score(
        get_klines_fn,
        symbol,
        direction
):

    aligned = 0
    total = 0

    is_long = direction == "LONG"


    for tf in TIMEFRAMES_MTF:

        try:

            candles = get_klines_fn(
                symbol,
                interval=tf,
                limit=50
            )

            if not candles or len(candles)<10:
                continue


            closes = [
                float(x[4])
                for x in candles
            ]

            rising = _is_rising(closes)


            if (is_long and rising) or (
                not is_long and not rising
            ):
                aligned += 1


            total += 1


        except Exception:
            continue


    if total < 3:

        return {
            "score":0,
            "reasons":[],
            "risks":[
                "تعداد تایم‌فریم کافی نبود"
            ]
        }


    ratio = aligned / total


    if ratio >=0.75:

        return {
            "score":20,
            "reasons":[
                "تایید چند تایم‌فریمه"
            ],
            "risks":[]
        }


    if ratio >=0.5:

        return {
            "score":10,
            "reasons":[
                "بخشی از تایم‌فریم‌ها تایید هستند"
            ],
            "risks":[]
        }


    return {
        "score":0,
        "reasons":[],
        "risks":[
            "عدم هماهنگی تایم‌فریم‌ها"
        ]
    }


def _market_bonus(signal_meta: dict, extra_result: dict = None):

    reasons = []
    risks = []

    score = 0


    if extra_result:

        score += _safe_float(
            extra_result.get("score",0)
        )

        reasons.extend(
            extra_result.get("reasons",[])
        )

        risks.extend(
            extra_result.get("risks",[])
        )


        oi_change = extra_result.get(
            "open_interest_change"
        )


        if oi_change is not None:

            oi_change = _safe_float(
                oi_change
            )


            if oi_change < -10:

                score -= 5

                risks.append(
                    f"کاهش Open Interest ({oi_change}%)"
                )


            elif oi_change > 10:

                score += 3

                reasons.append(
                    "افزایش Open Interest"
                )


        funding = extra_result.get(
            "funding_rate"
        )


        if funding is not None:

            funding = _safe_float(
                funding
            )


            if abs(funding) > 0.1:

                risks.append(
                    "Funding غیرعادی"
                )

                score -= 3


    else:

        volume = _safe_float(
            signal_meta.get(
                "volume",
                0
            )
        )


        change = _safe_float(
            signal_meta.get(
                "change",
                0
            )
        )


        if volume >= 10000000:

            score += 8

            reasons.append(
                "حجم معاملات بسیار بالا"
            )


        elif volume >= 3000000:

            score += 5

            reasons.append(
                "حجم معاملات بالا"
            )


        if abs(change)>=15:

            score += 5

            reasons.append(
                "حرکت قوی قیمت"
            )


    return {

        "score":max(
            0,
            min(score,15)
        ),

        "reasons":reasons,

        "risks":risks

    }



def run_confluence_analysis(
        symbol,
        get_klines_fn,
        signal_meta:dict,
        direction="LONG",
        extra_analyzer=None
):


    try:

        candles_4h = get_klines_fn(
            symbol,
            interval="4h",
            limit=150
        )


        candles_1d = get_klines_fn(
            symbol,
            interval="1d",
            limit=120
        )


    except Exception:

        return None



    primary_df = klines_to_df(
        candles_4h
    )

    structure_df = klines_to_df(
        candles_1d
    )


    if (
        primary_df is None
        or structure_df is None
        or len(primary_df)<50
    ):

        return None



    reasons=[]
    risks=[]

    total_score=0



    # ----------------------------
    # Technical
    # ----------------------------

    try:

        indicators = compute_indicators(
            primary_df
        )


        indicator_result = score_indicator_bundle(
            indicators,
            direction=direction
        )


        total_score += _safe_float(
            indicator_result.get(
                "score"
            )
        )


        reasons.extend(
            indicator_result.get(
                "reasons",
                []
            )
        )


        risks.extend(
            indicator_result.get(
                "risks",
                []
            )
        )


    except Exception as e:

        risks.append(
            "خطا در اندیکاتورها"
        )



    # ----------------------------
    # Smart Money
    # ----------------------------

    try:

        smc_result = analyze_smc(
            structure_df,
            direction=direction
        )


        total_score += _safe_float(
            smc_result.get(
                "score"
            )
        )


        reasons.extend(
            smc_result.get(
                "reasons",
                []
            )
        )


        risks.extend(
            smc_result.get(
                "risks",
                []
            )
        )


    except Exception:

        smc_result={

            "score":0,

            "reasons":[],

            "risks":[
                "SMC در دسترس نیست"
            ]

        }



    # ----------------------------
    # Multi Time Frame
    # ----------------------------

    mtf_result = _mtf_alignment_score(
        get_klines_fn,
        symbol,
        direction
    )


    total_score += mtf_result["score"]


    reasons.extend(
        mtf_result["reasons"]
    )


    risks.extend(
        mtf_result["risks"]
    )



    # ----------------------------
    # Extra market data
    # ----------------------------

    if extra_analyzer:

        try:

            extra_result = extra_analyzer(
                symbol,
                direction
            )

        except Exception:

            extra_result={}

    else:

        extra_result={}



    market_result = _market_bonus(
        signal_meta,
        extra_result
    )


    total_score += market_result["score"]


    reasons.extend(
        market_result["reasons"]
    )


    risks.extend(
        market_result["risks"]
    )



    total_score = round(
        max(
            0,
            min(total_score,100)
        ),
        1
    )



    if total_score >= MIN_SIGNAL_SCORE:

        decision="SIGNAL"


    elif total_score >= MIN_WATCHLIST_SCORE:

        decision="WATCHLIST"


    else:

        decision="REJECT"
    # ----------------------------
    # Trade Levels
    # ----------------------------

    try:

        current_price = float(
            structure_df["close"].iloc[-1]
        )


        trade_levels = _calculate_trade_levels(
            current_price,
            structure_df,
            direction
        )


    except Exception:

        current_price = 0

        trade_levels = None



    return {

        "symbol": symbol,

        "direction": direction,

        "score": total_score,

        "decision": decision,


        "reasons": reasons[:10],

        "risks": risks[:6],


        "trade_levels": trade_levels,


        "current_price": round(
            current_price,
            8
        ),


        "structure_signal": smc_result.get(
            "structure_signal"
        ),


        "smart_money_alert": extra_result.get(
            "whale_alert",
            False
        ),


        "funding_rate": extra_result.get(
            "funding_rate"
        ),


        "open_interest": extra_result.get(
            "open_interest"
        ),


        "open_interest_change": extra_result.get(
            "open_interest_change"
        ),


        "long_short_ratio": extra_result.get(
            "long_short_ratio"
        ),



        "breakdown": {

            "indicators": indicator_result.get(
                "score",
                0
            ),

            "smc": smc_result.get(
                "score",
                0
            ),

            "mtf": mtf_result.get(
                "score",
                0
            ),

            "extra": market_result.get(
                "score",
                0
            )

        }

    }
