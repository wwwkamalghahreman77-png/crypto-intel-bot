"""
analysis/indicators.py

مجموعه کامل اندیکاتورهای تکنیکال، محاسبه‌شده روی داده OHLCV (کندل).
ورودی این ماژول، دیتای kline استاندارد توبیت است:
[open_time, open, high, low, close, volume, close_time, quote_volume, trades, ...]

خروجی هر تابع یک دیکشنری امن (fail-soft) است؛ اگر داده کافی نباشد
مقدار None برمی‌گردد و بقیه‌ی سیستم باید این حالت را مدیریت کند.
"""

import pandas as pd
import numpy as np


def klines_to_df(candles) -> "pd.DataFrame | None":
    """تبدیل خروجی خام get_klines به DataFrame با ستون‌های open/high/low/close/volume"""

    if not candles or len(candles) < 5:
        return None

    try:
        df = pd.DataFrame(candles).iloc[:, :6]
        df.columns = ["open_time", "open", "high", "low", "close", "volume"]
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df
    except Exception as e:
        print("[Indicators] خطا در تبدیل کندل به DataFrame:", e)
        return None


def compute_indicators(df: "pd.DataFrame") -> dict:
    """
    محاسبه تمام اندیکاتورها روی یک DataFrame از کندل‌ها (یک تایم‌فریم).
    برمی‌گرداند: دیکشنری مقادیر آخرین کندل + چند سیگنال بولی کمکی.
    """

    from ta.momentum import RSIIndicator
    from ta.trend import MACD, EMAIndicator, ADXIndicator, CCIIndicator, IchimokuIndicator
    from ta.volatility import BollingerBands, AverageTrueRange
    from ta.volume import OnBalanceVolumeIndicator, MFIIndicator, ChaikinMoneyFlowIndicator

    out = {"available": False}

    if df is None or len(df) < 25:
        return out

    high, low, close, volume = df["high"], df["low"], df["close"], df["volume"]
    n = len(df)

    try:
        out["rsi"] = round(RSIIndicator(close=close, window=14).rsi().iloc[-1], 2)
    except Exception:
        out["rsi"] = None

    try:
        macd_calc = MACD(close=close)
        out["macd_line"] = round(macd_calc.macd().iloc[-1], 6)
        out["macd_signal"] = round(macd_calc.macd_signal().iloc[-1], 6)
        out["macd_hist"] = round(macd_calc.macd_diff().iloc[-1], 6)
    except Exception:
        out["macd_line"] = out["macd_signal"] = out["macd_hist"] = None

    for period in (20, 50, 100, 200):
        try:
            window = min(period, n - 1)
            if window < 5:
                out[f"ema{period}"] = None
                continue
            out[f"ema{period}"] = round(EMAIndicator(close=close, window=window).ema_indicator().iloc[-1], 8)
        except Exception:
            out[f"ema{period}"] = None

    try:
        bb = BollingerBands(close=close, window=20, window_dev=2)
        out["bb_high"] = round(bb.bollinger_hband().iloc[-1], 8)
        out["bb_low"] = round(bb.bollinger_lband().iloc[-1], 8)
        out["bb_mid"] = round(bb.bollinger_mavg().iloc[-1], 8)
    except Exception:
        out["bb_high"] = out["bb_low"] = out["bb_mid"] = None

    try:
        atr_window = min(14, n - 1)
        out["atr"] = round(AverageTrueRange(high=high, low=low, close=close, window=atr_window).average_true_range().iloc[-1], 8)
    except Exception:
        out["atr"] = None

    try:
        adx_window = min(14, n - 1)
        adx_calc = ADXIndicator(high=high, low=low, close=close, window=adx_window)
        out["adx"] = round(adx_calc.adx().iloc[-1], 2)
        out["adx_pos"] = round(adx_calc.adx_pos().iloc[-1], 2)
        out["adx_neg"] = round(adx_calc.adx_neg().iloc[-1], 2)
    except Exception:
        out["adx"] = out["adx_pos"] = out["adx_neg"] = None

    try:
        cci_window = min(20, n - 1)
        out["cci"] = round(CCIIndicator(high=high, low=low, close=close, window=cci_window).cci().iloc[-1], 2)
    except Exception:
        out["cci"] = None

    try:
        mfi_window = min(14, n - 1)
        out["mfi"] = round(MFIIndicator(high=high, low=low, close=close, volume=volume, window=mfi_window).money_flow_index().iloc[-1], 2)
    except Exception:
        out["mfi"] = None

    try:
        cmf_window = min(20, n - 1)
        out["cmf"] = round(ChaikinMoneyFlowIndicator(high=high, low=low, close=close, volume=volume, window=cmf_window).chaikin_money_flow().iloc[-1], 4)
    except Exception:
        out["cmf"] = None

    try:
        obv_series = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        out["obv"] = round(obv_series.iloc[-1], 2)
        out["obv_rising"] = bool(obv_series.iloc[-1] > obv_series.iloc[-min(6, n - 1)])
    except Exception:
        out["obv"] = None
        out["obv_rising"] = None

    try:
        typical_price = (high + low + close) / 3
        vwap_series = (typical_price * volume).cumsum() / volume.cumsum()
        out["vwap"] = round(vwap_series.iloc[-1], 8)
    except Exception:
        out["vwap"] = None

    try:
        if n >= 60:
            ich_window1 = min(9, n - 1)
            ich_window2 = min(26, n - 1)
            ich_window3 = min(52, n - 1)
            ichi = IchimokuIndicator(high=high, low=low, window1=ich_window1, window2=ich_window2, window3=ich_window3)
            out["ichimoku_conversion"] = round(ichi.ichimoku_conversion_line().iloc[-1], 8)
            out["ichimoku_base"] = round(ichi.ichimoku_base_line().iloc[-1], 8)
            out["ichimoku_span_a"] = round(ichi.ichimoku_a().iloc[-1], 8)
            out["ichimoku_span_b"] = round(ichi.ichimoku_b().iloc[-1], 8)
        else:
            out["ichimoku_conversion"] = out["ichimoku_base"] = None
            out["ichimoku_span_a"] = out["ichimoku_span_b"] = None
    except Exception:
        out["ichimoku_conversion"] = out["ichimoku_base"] = None
        out["ichimoku_span_a"] = out["ichimoku_span_b"] = None

    # SuperTrend (پیاده‌سازی دستی؛ در کتابخانه ta موجود نیست)
    try:
        out["supertrend_direction"] = compute_supertrend(df)
    except Exception:
        out["supertrend_direction"] = None

    out["current_price"] = round(close.iloc[-1], 8)
    out["available"] = True
    return out


def compute_supertrend(df: "pd.DataFrame", period: int = 10, multiplier: float = 3.0) -> "str | None":
    """
    محاسبه دستی SuperTrend. خروجی: 'up' یا 'down' برای جهت روند فعلی.
    """

    from ta.volatility import AverageTrueRange

    if len(df) < period + 5:
        return None

    high, low, close = df["high"], df["low"], df["close"]
    atr = AverageTrueRange(high=high, low=low, close=close, window=period).average_true_range()

    hl2 = (high + low) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    direction = True  # True = uptrend
    final_upper = upper_band.iloc[0]
    final_lower = lower_band.iloc[0]

    for i in range(1, len(df)):
        curr_close = close.iloc[i]

        if upper_band.iloc[i] < final_upper or close.iloc[i - 1] > final_upper:
            final_upper = upper_band.iloc[i]

        if lower_band.iloc[i] > final_lower or close.iloc[i - 1] < final_lower:
            final_lower = lower_band.iloc[i]

        if direction and curr_close < final_lower:
            direction = False
        elif not direction and curr_close > final_upper:
            direction = True

    return "up" if direction else "down"


def score_indicator_bundle(ind: dict, direction: str = "LONG") -> dict:
    """
    امتیازدهی وزن‌دار بر پایه اندیکاتورهای محاسبه‌شده یک تایم‌فریم.
    خروجی: {"score": 0-45, "reasons": [...], "risks": [...]}
    این بخش، «دسته‌ی روند + مومنتوم + نوسان/حجم» را از کل امتیاز کانفلوئنس پوشش می‌دهد.
    """

    reasons, risks = [], []
    score = 0.0
    is_long = direction == "LONG"

    if not ind.get("available"):
        return {"score": 0, "reasons": [], "risks": ["داده اندیکاتور کافی نبود"]}

    # --- روند: EMA Alignment (وزن ۱۰) ---
    ema20, ema50, ema100, ema200 = ind.get("ema20"), ind.get("ema50"), ind.get("ema100"), ind.get("ema200")
    if ema20 and ema50:
        aligned = (ema20 > ema50) if is_long else (ema20 < ema50)
        if aligned:
            score += 6
            reasons.append("EMA20/50 هم‌راستا با روند")
        if ema100 and ((ema50 > ema100) if is_long else (ema50 < ema100)):
            score += 2
        if ema200 and ((ema100 or ema50) and ((ema50 > ema200) if is_long else (ema50 < ema200))):
            score += 2
            reasons.append("چیدمان کامل EMA (۲۰/۵۰/۱۰۰/۲۰۰) تایید شد")

    # --- Ichimoku (وزن ۵) ---
    conv, base = ind.get("ichimoku_conversion"), ind.get("ichimoku_base")
    price = ind.get("current_price")
    span_a, span_b = ind.get("ichimoku_span_a"), ind.get("ichimoku_span_b")
    if conv and base and price:
        cloud_top = max(span_a, span_b) if (span_a and span_b) else None
        cloud_bottom = min(span_a, span_b) if (span_a and span_b) else None
        if is_long and conv > base and cloud_top and price > cloud_top:
            score += 5
            reasons.append("قیمت بالای ابر ایچیموکو و تنکان بالای کیجون")
        elif not is_long and conv < base and cloud_bottom and price < cloud_bottom:
            score += 5
            reasons.append("قیمت زیر ابر ایچیموکو و تنکان زیر کیجون")

    # --- SuperTrend (وزن ۵) ---
    st_dir = ind.get("supertrend_direction")
    if st_dir:
        if (st_dir == "up" and is_long) or (st_dir == "down" and not is_long):
            score += 5
            reasons.append("SuperTrend هم‌جهت با سیگنال")
        else:
            risks.append("SuperTrend خلاف جهت سیگنال است")

    # --- مومنتوم: RSI (وزن ۴) ---
    rsi = ind.get("rsi")
    if rsi is not None:
        if is_long:
            if 45 <= rsi <= 68:
                score += 4
                reasons.append(f"RSI در محدوده سالم صعودی ({rsi})")
            elif rsi >= 80:
                risks.append(f"RSI اشباع خرید ({rsi})")
        else:
            if 32 <= rsi <= 55:
                score += 4
                reasons.append(f"RSI در محدوده سالم نزولی ({rsi})")
            elif rsi <= 20:
                risks.append(f"RSI اشباع فروش ({rsi})")

    # --- MACD (وزن ۴) ---
    macd_line, macd_signal = ind.get("macd_line"), ind.get("macd_signal")
    if macd_line is not None and macd_signal is not None:
        if (macd_line > macd_signal) == is_long:
            score += 4
            reasons.append("MACD هم‌جهت با سیگنال")

    # --- CCI (وزن ۳) ---
    cci = ind.get("cci")
    if cci is not None:
        if is_long and cci > 0:
            score += 3
        elif not is_long and cci < 0:
            score += 3
        if abs(cci) > 200:
            risks.append(f"CCI در منطقه افراطی ({cci})")

    # --- ADX: قدرت روند (وزن ۴) ---
    adx = ind.get("adx")
    if adx is not None:
        if adx >= 25:
            score += 4
            reasons.append(f"ADX روند قوی را تایید می‌کند ({adx})")
        elif adx < 15:
            risks.append(f"ADX پایین - روند ضعیف ({adx})")

    # --- حجم: OBV / MFI / CMF (وزن ۸) ---
    if ind.get("obv_rising") is True and is_long:
        score += 3
        reasons.append("OBV صعودی - ورود پول به بازار")
    elif ind.get("obv_rising") is False and not is_long:
        score += 3
        reasons.append("OBV نزولی - خروج پول از بازار")

    mfi = ind.get("mfi")
    if mfi is not None:
        if is_long and 50 <= mfi <= 80:
            score += 3
        elif not is_long and 20 <= mfi <= 50:
            score += 3
        elif mfi >= 90 or mfi <= 10:
            risks.append(f"MFI در منطقه افراطی ({mfi})")

    cmf = ind.get("cmf")
    if cmf is not None:
        if (cmf > 0.05 and is_long) or (cmf < -0.05 and not is_long):
            score += 2
            reasons.append("CMF جریان نقدینگی مثبت را تایید می‌کند")

    # --- نوسان: ATR / Bollinger / VWAP (وزن ۴) ---
    bb_high, bb_low = ind.get("bb_high"), ind.get("bb_low")
    if price and bb_high and bb_low:
        if is_long and price >= bb_high:
            score += 2
            reasons.append("شکست باند بالایی بولینگر")
        elif not is_long and price <= bb_low:
            score += 2
            reasons.append("شکست باند پایینی بولینگر")

    vwap = ind.get("vwap")
    if price and vwap:
        if (price > vwap) == is_long:
            score += 2
            reasons.append("قیمت هم‌جهت با VWAP")

    return {
        "score": round(min(score, 45), 1),
        "reasons": reasons,
        "risks": risks,
        "indicators": ind,
    }
