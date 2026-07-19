# futures/derivatives.py

import requests

from database.db import (
    db,
    now_str,
)


BASE_URL = (
    "https://api.toobit.com"
)


REQUEST_TIMEOUT = 10


def _safe_float(
    value,
    default=None
):

    try:

        if value is None:
            return default

        return float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


def get_funding_rate(
    symbol: str
) -> "dict | None":

    try:

        response = requests.get(
            (
                BASE_URL
                + "/api/v1/futures/fundingRate"
            ),
            params={
                "symbol": symbol
            },
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        if (
            isinstance(
                data,
                list
            )
            and data
        ):

            row = data[0]

            rate = _safe_float(
                row.get(
                    "rate"
                )
            )

            if rate is None:

                return None

            return {

                "rate":
                    rate,

                "next_funding_time":
                    row.get(
                        "nextFundingTime"
                    ),
            }

        return None

    except Exception as e:

        print(
            f"[Derivatives] "
            f"Funding error "
            f"{symbol}: {e}"
        )

        return None


def get_open_interest(
    symbol: str
) -> "float | None":

    try:

        response = requests.get(
            (
                BASE_URL
                + "/quote/v1/openInterest"
            ),
            params={
                "symbol": symbol
            },
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

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

        if not rows:

            return None

        for row in rows:

            if (
                row.get(
                    "symbol"
                )
                == symbol
            ):

                return _safe_float(
                    row.get(
                        "size"
                    )
                )

        return _safe_float(
            rows[0].get(
                "size"
            )
        )

    except Exception as e:

        print(
            f"[Derivatives] "
            f"Open Interest error "
            f"{symbol}: {e}"
        )

        return None


def get_long_short_ratio(
    symbol: str,
    period: str = "1h"
) -> "dict | None":

    try:

        response = requests.get(
            (
                BASE_URL
                + "/quote/v1/"
                "globalLongShortAccountRatio"
            ),
            params={
                "symbol": symbol,
                "period": period,
                "limit": 1
            },
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        if (
            not isinstance(
                data,
                list
            )
            or not data
        ):

            return None

        row = data[0]

        ratio = _safe_float(
            row.get(
                "longShortRatio"
            )
        )

        long_account = _safe_float(
            row.get(
                "longAccount"
            )
        )

        short_account = _safe_float(
            row.get(
                "shortAccount"
            )
        )

        if ratio is None:

            return None

        return {

            "ratio":
                ratio,

            "long_account":
                long_account,

            "short_account":
                short_account,
        }

    except Exception as e:

        print(
            f"[Derivatives] "
            f"Long/Short error "
            f"{symbol}: {e}"
        )

        return None


def get_previous_oi(
    symbol: str
) -> "float | None":

    try:

        rows = db.fetch_by_token(
            "derivatives_snapshot",
            symbol
        )

        if not rows:

            return None

        for row in reversed(
            rows
        ):

            value = _safe_float(
                row.get(
                    "open_interest"
                )
            )

            if value is not None:

                return value

        return None

    except Exception as e:

        print(
            "[Derivatives] "
            "خطا در دریافت OI قبلی:",
            e
        )

        return None


def save_oi_snapshot(
    symbol: str,
    open_interest: float,
    funding_rate: float
):

    try:

        db.insert(
            "derivatives_snapshot",
            {

                "token":
                    symbol,

                "open_interest":
                    open_interest,

                "funding_rate":
                    funding_rate,

                "date_found":
                    now_str(),
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
        direction.upper()
        == "LONG"
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

        rate = funding.get(
            "rate"
        )

        if is_long:

            if rate < 0:

                score += 3

                reasons.append(
                    f"Funding منفی "
                    f"({round(rate * 100, 4)}%)"
                )

            elif rate >= 0.0005:

                risks.append(
                    f"Funding مثبت بالا "
                    f"({round(rate * 100, 4)}%)"
                )

        else:

            if rate > 0:

                score += 3

                reasons.append(
                    f"Funding مثبت "
                    f"({round(rate * 100, 4)}%)"
                )

            elif rate <= -0.0005:

                risks.append(
                    f"Funding منفی بالا "
                    f"({round(rate * 100, 4)}%)"
                )

    if ls_ratio is not None:

        ratio = ls_ratio.get(
            "ratio"
        )

        if ratio is not None:

            if (
                is_long
                and ratio < 1.0
            ):

                score += 3

                reasons.append(
                    f"نسبت Long/Short "
                    f"به نفع شورت‌هاست "
                    f"(L/S={round(ratio, 2)})"
                )

            elif (
                not is_long
                and ratio > 1.5
            ):

                score += 3

                reasons.append(
                    f"نسبت Long/Short "
                    f"به نفع لانگ‌هاست "
                    f"(L/S={round(ratio, 2)})"
                )

            if (
                is_long
                and ratio > 3
            ):

                risks.append(
                    f"ازدحام شدید لانگ "
                    f"(L/S={round(ratio, 2)})"
                )

            elif (
                not is_long
                and ratio < 0.5
            ):

                risks.append(
                    f"ازدحام شدید شورت "
                    f"(L/S={round(ratio, 2)})"
                )

    if oi is not None:

        previous_oi = get_previous_oi(
            symbol
        )

        if (
            previous_oi is not None
            and previous_oi > 0
        ):

            oi_change_pct = (
                (
                    oi
                    - previous_oi
                )
                / previous_oi
                * 100
            )

            if oi_change_pct >= 3:

                score += 4

                reasons.append(
                    f"Open Interest "
                    f"{round(oi_change_pct, 1)}٪ "
                    f"افزایش یافته"
                )

            elif oi_change_pct <= -3:

                risks.append(
                    f"Open Interest "
                    f"{round(oi_change_pct, 1)}٪ "
                    f"کاهش یافته"
                )

        save_oi_snapshot(
            symbol,
            oi,
            funding.get(
                "rate",
                0
            )
            if funding
            else 0
        )

    whale_alert = False

    if ls_ratio is not None:

        ratio = ls_ratio.get(
            "ratio"
        )

        if (
            ratio is not None
            and (
                ratio >= 4
                or ratio <= 0.25
            )
        ):

            whale_alert = True

    return {

        "score":
            round(
                min(
                    score,
                    15
                ),
                1
            ),

        "reasons":
            reasons,

        "risks":
            risks,

        "funding_rate":
            funding.get(
                "rate"
            )
            if funding
            else None,

        "open_interest":
            oi,

        "long_short_ratio":
            ls_ratio.get(
                "ratio"
            )
            if ls_ratio
            else None,

        "whale_alert":
            whale_alert,
    }
