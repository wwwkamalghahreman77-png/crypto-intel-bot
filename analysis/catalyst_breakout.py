"""
analysis/catalyst_breakout.py

تشخیص الگوی «جهش کاتالیزوری» شبیه به اتفاقی که برای AKE (Akedo) و BANK (Lorenzo
Protocol) افتاد: یک دوره‌ی نسبتا طولانی تثبیت/رنج فشرده، و بعد یک شکست ناگهانی
همراه با جهش شدید حجم و رشد سریع قیمت در چند روز اخیر.

این یک الگوی رفتاری/آماری است، نه یک "کاتالیزور خبری" واقعی (ایردراپ/لیستینگ) -
ربات به فید خبری لحظه‌ای اکسچنج‌ها دسترسی مستقیم برای این تشخیص ندارد، اما این
۴ ویژگی قابل اندازه‌گیری روی کندل هستند و در هر دو نمونه‌ی واقعی هم‌زمان دیده شدند:

    ۱) قبل از حرکت، یک پایه‌ی فشرده (رنج کم‌نوسان) وجود داشته
    ۲) حجم روزانه چند برابر میانگین ۲۰ روزه اخیر شده
    ۳) قیمت سقف آن پایه/رنج را شکسته
    ۴) رشد قابل توجه در ۳ روز اخیر

ورودی ایده‌آل، همان structure_df (تایم‌فریم روزانه) است که در
analysis/confluence.py از قبل واکشی می‌شود - برای جلوگیری از فراخوانی
تکراری API از همان دیتافریم استفاده می‌کنیم.
"""

MIN_HITS_FOR_MATCH = 3  # حداقل ۳ از ۴ ویژگی باید هم‌زمان برقرار باشند


def analyze_catalyst_breakout(structure_df, min_hits=MIN_HITS_FOR_MATCH) -> dict:
    """
    structure_df: دیتافریم روزانه (ستون‌های open/high/low/close/volume) - حداقل ۴۰ کندل لازم است.
    خروجی: {"match": bool, "reasons": [...], "volume_ratio": .., "range_pct": .., "change_3d": ..}
    """

    if structure_df is None or len(structure_df) < 40:
        return {"match": False, "reasons": []}

    df = structure_df.reset_index(drop=True)
    closes = df["close"].tolist()
    volumes = df["volume"].tolist()
    highs = df["high"].tolist()
    lows = df["low"].tolist()

    reasons = []
    hits = 0

    # ۱) میانگین حجم ۲۰ روز قبل از دیروز، در مقابل حجم امروز
    recent_avg_vol = sum(volumes[-21:-1]) / max(len(volumes[-21:-1]), 1)
    today_vol = volumes[-1]
    volume_ratio = round(today_vol / recent_avg_vol, 2) if recent_avg_vol > 0 else 0

    if volume_ratio >= 2.5:
        reasons.append(f"حجم روزانه {volume_ratio}× میانگین ۲۰ روز اخیر")
        hits += 1

    # ۲) رنج فشرده در ۳۰ روز قبل از ۳ روز اخیر (پایه‌ی تثبیت)
    window_highs = highs[-34:-3] if len(highs) >= 34 else highs[:-3]
    window_lows = lows[-34:-3] if len(lows) >= 34 else lows[:-3]

    range_pct = 999
    if window_highs and window_lows:
        range_high = max(window_highs)
        range_low = min(window_lows)
        if range_low > 0:
            range_pct = round((range_high - range_low) / range_low * 100, 1)

    if range_pct <= 35:
        reasons.append(f"پیش از این حرکت، حدود یک ماه در یک رنج فشرده ({range_pct}٪) تثبیت بوده")
        hits += 1

    # ۳) شکست سقف همان رنج فشرده
    breakout = False
    if window_highs:
        range_high = max(window_highs)
        if closes[-1] > range_high * 1.01:
            breakout = True
            reasons.append("قیمت بالای سقف رنج تثبیت شکسته شده")
            hits += 1

    # ۴) رشد قابل توجه در ۳ روز اخیر
    change_3d = 0
    if len(closes) >= 4 and closes[-4] > 0:
        change_3d = round((closes[-1] / closes[-4] - 1) * 100, 1)

    if change_3d >= 15:
        reasons.append(f"جهش {change_3d}٪ در ۳ روز اخیر")
        hits += 1

    return {
        "match": hits >= min_hits,
        "reasons": reasons,
        "volume_ratio": volume_ratio,
        "range_pct": range_pct,
        "breakout": breakout,
        "change_3d": change_3d,
        "hits": hits,
    }
