"""
futures/derivatives.py

دیتای مشتقات از توبیت:
Funding Rate, Open Interest, Long/Short Ratio.

اندپوینت‌ها:
    GET /api/v1/futures/fundingRate
    GET /quote/v1/openInterest
    GET /quote/v1/globalLongShortAccountRatio

نکته:
این اندپوینت‌ها فقط برای نمادهای فیوچرز
(فرمت BTC-SWAP-USDT) کار می‌کنند.
"""

import requests

from database.db import (
    db,
    now_str,
)


BASE_URL = (
    "https://api.toobit.com"
)


def get_funding_rate(
    symbol: str
) -> "dict | None":

    try:

        url = (
            BASE_URL
            + "/api/v1/futures/fundingRate"
        )

        resp = requests.get(
            url,
            params={
                "symbol": symbol
            },
            timeout=10
        )

        data = resp.json()

        if (
            isinstance(data, list)
            and data
        ):

            row = data[0]

            return {
                "rate": float(
                    row.get(
                        "rate",
                        0
                    )
                ),

                "next_funding_time":
                    row.get(
                        "nextFundingTime"
                    ),
            }

        return None

    except Exception as e:

        print(
            f"[Derivatives] "
            f"خطا در دریافت فاندینگ ریت "
            f"{symbol}: {e}"
        )

        return None


def get_open_interest(
    symbol: str
) -> "float | None":

    try:

        url = (
            BASE_URL
            + "/quote/v1/openInterest"
        )

        resp = requests.get(
            url,
            params={
                "symbol": symbol
            },
            timeout=10
        )

        data = resp.json()

        rows = (
            data.get(
                "openInterestList",
                []
            )
            if isinstance(
                data,
                dict
            )
            else []
        )

        for row in rows:

            if (
                row.get(
                    "symbol"
                )
                == symbol
            ):

                return float(
                    row.get(
                        "size",
                        0
                    )
                )

        if rows:

            return float(
                rows[0].get(
                    "size",
                    0
                )
            )

        return None

    except Exception as e:

        print(
            f"[Derivatives] "
            f"خطا در دریافت Open Interest "
            f"{symbol}: {e}"
        )

        return None


def get_long_short_ratio(
    symbol: str,
    period: str = "1h"
) -> "dict | None":

    try:

        url = (
            BASE_URL
            + "/quote/v1/globalLongShortAccountRatio"
        )

        resp = requests.get(
            url,
            params={
                "symbol": symbol,
                "period": period,
                "limit": 1
            },
            timeout=10
        )

        data = resp.json()

        if (
            isinstance(data, list)
            and data
        ):

            row = data[0]

            return {
                "ratio": float(
                    row.get(
                        "longShortRatio",
                        0
                    )
                ),

                "long_account": float(
                    row.get(
                        "longAccount",
                        0
                    )
                ),

                "short_account": float(
                    row.get(
                        "shortAccount",
                        0
                    )
                ),
            }

        return None

    except Exception as e:

        print(
            f"[Derivatives] "
            f"خطا در دریافت Long/Short Ratio "
            f"{symbol}: {e}"
        )

        return None


def get_previous_oi(
    symbol: str
) -> "float | None":

    rows = db.fetch_by_token(
        "derivatives_snapshot",
        symbol
    )

    if not rows:
        return None

    return rows[-1].get(
        "open_interest"
    )


def save_oi_snapshot(
    symbol: str,
    open_interest: float,
    funding_rate: float
):

    try:

        db.insert(
            "derivatives_snapshot",
            {
                "token": symbol,
                "open_interest": open_interest,
                "funding_rate": funding_rate,
                "date_found": now_str(),
            }
        )

    except Exception as e:

        print(
            "[Derivatives] "
            "خطا در ذخیره snapshot:",
            e
        )


def analyze_derivatives(
    symbol: str,
    direction: str = "LONG"
) -> dict:

    reasons = []
    risks = []

    score = 0.0

    is_long = (
        direction == "LONG"
    )

    funding = get_funding_rate(
        symbol
    )

    oi = get_open_interest(
        symbol
    )

    ls_ratio = get_long_short_ratio(
        symbol
    )

    if funding is not None:

        rate = funding[
            "rate"
        ]

        if is_long:

            if rate < 0:

                score += 3

                reasons.append(
                    f"فاندینگ ریت منفی "
                    f"({round(rate * 100, 4)}%) "
                    f"- شورت‌ها هزینه می‌دهند"
                )

            elif rate > 0.05:

                risks.append(
                    f"فاندینگ ریت بسیار مثبت "
                    f"({round(rate * 100, 4)}%) "
                    f"- ازدحام لانگ"
                )

        else:

            if rate > 0:

                score += 3

                reasons.append(
                    f"فاندینگ ریت مثبت "
                    f"({round(rate * 100, 4)}%) "
                    f"- لانگ‌ها هزینه می‌دهند"
                )

            elif rate < -0.05:

                risks.append(
                    f"فاندینگ ریت بسیار منفی "
                    f"({round(rate * 100, 4)}%) "
                    f"- ازدحام شورت"
                )

    if ls_ratio is not None:

        ratio = ls_ratio[
            "ratio"
        ]

        if (
            is_long
            and ratio < 1.0
        ):

            score += 3

            reasons.append(
                f"اکثریت معامله‌گران شورت هستند "
                f"(L/S={ratio}) "
                f"- فضای رشد برای لانگ باقی است"
            )

        elif (
            not is_long
            and ratio > 1.5
        ):

            score += 3

            reasons.append(
                f"اکثریت معامله‌گران لانگ هستند "
                f"(L/S={ratio}) "
                f"- فضای ریزش برای شورت باقی است"
            )

        elif (
            is_long
            and ratio > 3
        ):

            risks.append(
                f"اکثریت شدید معامله‌گران لانگ هستند "
                f"(L/S={ratio}) "
                f"- ریسک تخلیه لانگ"
            )

        elif (
            not is_long
            and ratio < 0.5
        ):

            risks.append(
                f"اکثریت شدید معامله‌گران شورت هستند "
                f"(L/S={ratio}) "
                f"- ریسک اسکوییز شورت"
            )

    if oi is not None:

        prev_oi = get_previous_oi(
            symbol
        )

        if (
            prev_oi
            and prev_oi > 0
        ):

            oi_change_pct = (
                (
                    oi - prev_oi
                )
                / prev_oi
                * 100
            )

            if oi_change_pct >= 3:

                score += 4

                reasons.append(
                    f"Open Interest "
                    f"در حال افزایش "
                    f"({round(oi_change_pct, 1)}%) "
                    f"- ورود سرمایه تازه"
                )

            elif oi_change_pct <= -3:

                risks.append(
                    f"Open Interest "
                    f"در حال کاهش "
                    f"({round(oi_change_pct, 1)}%) "
                    f"- خروج سرمایه"
                )

        save_oi_snapshot(
            symbol,
            oi,
            funding["rate"]
            if funding
            else 0
        )

    whale_alert = False

    if (
        ls_ratio is not None
        and
        (
            ls_ratio["ratio"] > 4
            or
            ls_ratio["ratio"] < 0.25
        )
    ):

        whale_alert = True

    return {

        "score": round(
            min(
                score,
                15
            ),
            1
        ),

        "reasons": reasons,

        "risks": risks,

        "funding_rate":
            funding["rate"]
            if funding
            else None,

        "open_interest": oi,

        "long_short_ratio":
            ls_ratio["ratio"]
            if ls_ratio
            else None,

        "whale_alert":
            whale_alert,
    }
