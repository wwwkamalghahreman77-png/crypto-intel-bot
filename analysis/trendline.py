"""
analysis/trendline.py

تشخیص شکست خط روند بلندمدت روی تایم‌فریم روزانه.
روش کار:
    - جهت روند غالب هر بازه با شیب کلی قیمت پایانی تعیین می‌شود
    - اگر روند صعودی باشد، یک خط حمایت با اتصال چند سوئینگ‌لوی اخیر رسم می‌شود
    - اگر روند نزولی باشد، یک خط مقاومت با اتصال چند سوئینگ‌های اخیر رسم می‌شود
    - بررسی می‌شود که آیا آخرین قیمت با فاصله‌ی معنادار (بافر ۲٪) آن خط را شکسته یا نه

"از همه زاویه بررسی کنه": برای کاهش شکست‌های کاذب کوتاه‌مدت، این بررسی هم‌زمان
روی دو بازه‌ی ۹۰ روزه و ۱۸۰ روزه انجام می‌شود و فقط وقتی هر دو بازه هم‌جهت
باشند و هر دو "شکسته‌شده" را تایید کنند، شکست نهایی گزارش می‌شود.
"""

import numpy as np
from analysis.smc import find_swings


def _fit_line(points):
    """points: [(index, price), ...] -> (slope, intercept) با رگرسیون خطی"""

    if len(points) < 2:
        return None

    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)

    try:
        slope, intercept = np.polyfit(xs, ys, 1)
        return slope, intercept
    except Exception:
        return None


def _check_period(df, lookback_days, swing_lookback=3, buffer_pct=0.02):
    """بررسی شکست خط روند روی یک بازه‌ی مشخص از انتهای دیتافریم"""

    window = df.tail(lookback_days).reset_index(drop=True)
    if len(window) < 30:
        return None

    swing_highs, swing_lows = find_swings(window, lookback=swing_lookback)

    closes = window["close"].tolist()
    overall_slope = (closes[-1] - closes[0]) / len(closes)
    current_price = closes[-1]
    current_idx = len(window) - 1

    if overall_slope >= 0:
        if len(swing_lows) < 2:
            return None
        points = swing_lows[-4:] if len(swing_lows) >= 4 else swing_lows
        line = _fit_line(points)
        if not line:
            return None
        slope, intercept = line
        trend_value = slope * current_idx + intercept
        broken = current_price < trend_value * (1 - buffer_pct)
        return {
            "trend_direction": "UP",
            "line_type": "support",
            "broken": broken,
            "trend_value": round(trend_value, 8),
            "current_price": round(current_price, 8),
        }

    if len(swing_highs) < 2:
        return None
    points = swing_highs[-4:] if len(swing_highs) >= 4 else swing_highs
    line = _fit_line(points)
    if not line:
        return None
    slope, intercept = line
    trend_value = slope * current_idx + intercept
    broken = current_price > trend_value * (1 + buffer_pct)
    return {
        "trend_direction": "DOWN",
        "line_type": "resistance",
        "broken": broken,
        "trend_value": round(trend_value, 8),
        "current_price": round(current_price, 8),
    }


def detect_trendline_break(long_term_df) -> dict:
    """
    long_term_df: دیتافریم روزانه با حداقل ۱۸۰ کندل (خروجی indicators.klines_to_df)
    خروجی: {"break_confirmed": bool, "trend_direction": "UP"/"DOWN", "label": ..., ...}
    """

    if long_term_df is None or len(long_term_df) < 100:
        return {"break_confirmed": False}

    result_90 = _check_period(long_term_df, 90)
    result_180 = _check_period(long_term_df, 180)

    if not result_90 or not result_180:
        return {"break_confirmed": False}

    same_direction = result_90["trend_direction"] == result_180["trend_direction"]
    both_broken = result_90["broken"] and result_180["broken"]

    if not (same_direction and both_broken):
        return {"break_confirmed": False}

    direction = result_90["trend_direction"]
    label = (
        "شکست نزولی خط روند صعودی بلندمدت (هشدار ریسک/خروج)"
        if direction == "UP"
        else "شکست صعودی خط روند نزولی بلندمدت (احتمال برگشت روند)"
    )

    return {
        "break_confirmed": True,
        "trend_direction": direction,
        "label": label,
        "trend_value_90d": result_90["trend_value"],
        "trend_value_180d": result_180["trend_value"],
        "current_price": result_90["current_price"],
    }
