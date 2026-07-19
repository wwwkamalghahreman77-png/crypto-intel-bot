def clean_symbol(symbol: str) -> str:
    """حذف SWAP از نماد و تبدیل به فرمت BASE/QUOTE"""
    s = (symbol or "").replace("-SWAP-", "-").strip("-")
    if "-" in s:
        s = s.replace("-", "/")
    elif s.endswith("USDT"):
        s = s[:-4] + "/USDT"
    return s


def suggest_leverage(score: int, risks: list) -> str:
    """اهرم پیشنهادی بر اساس قدرت سیگنال و وجود ریسک"""
    if risks:
        return "2x"
    if score >= 90:
        return "5x"
    if score >= 80:
        return "3x"
    return "2x"


def build_badges(signal: dict) -> str:
    """حداکثر ۴ نشونه‌ی کوتاه بر اساس نوع سیگنال"""
    badges = []

    status_label = signal.get("status_label", "")
    if status_label:
        badges.append(status_label.split(" ")[0])  # فقط ایموجی اول

    if signal.get("smart_money_alert"):
        badges.append("🐋")

    if signal.get("volume", 0) >= 5_000_000:
        badges.append("💰")

    if signal.get("score", 0) >= 90:
        badges.append("⭐")

    return "".join(badges[:4])


def build_short_reason(signal: dict) -> str:
    """یک عبارت کوتاه برای دلیل تایید سیگنال"""
    parts = []

    if signal.get("change", 0) >= 15:
        parts.append("جهش شدید قیمت")

    if signal.get("volume", 0) >= 5_000_000:
        parts.append("حجم بسیار بالا")
    elif signal.get("volume", 0) >= 1_000_000:
        parts.append("حجم بالا")

    if signal.get("smart_money_alert"):
        parts.append("پول هوشمند")

    structure_signal = signal.get("structure_signal")
    if structure_signal == "BREAKOUT_HIGH":
        parts.append("شکست سقف")
    elif structure_signal == "BOTTOM_REVERSAL":
        parts.append("بازگشت از کف")
    elif structure_signal in ("TREND_FLIP_LONG", "TREND_FLIP_SHORT"):
        parts.append("تغییر روند")

    return " + ".join(parts[:2]) if parts else "سیگنال ترکیبی"


def format_dex_discovery(discovery: dict) -> str:

    record = discovery["record"]
    symbol = clean_symbol(record.token)

    return (
        f"🚨 کشف DEX | {symbol}\n"
        f"شبکه: {record.network}\n"
        f"نقدینگی: ${record.liquidity:,.0f} | حجم: ${record.volume:,.0f}\n"
        f"امنیت: {record.security_score}/100 | امتیاز: {record.dex_score}/100"
    )


def format_crypto_report(report: dict) -> str:

    symbol = clean_symbol(report.get("token", ""))

    return (
        f"🧠 گزارش تحلیل | {symbol}\n"
        f"بازار: {report.get('market','نامشخص')}\n"
        f"امتیاز: {report['total_score']}/100 | وضعیت: {report['status']}"
    )


def format_market_signal(signal: dict) -> str:

    symbol = clean_symbol(signal.get("symbol", ""))
    reason = build_short_reason(signal)

    return (
        f"🚨 {symbol} | {signal.get('type','?')}\n"
        f"قیمت: {signal.get('price',0)} | حجم: {signal.get('volume',0):,.0f}\n"
        f"{reason} | امتیاز: {signal.get('score',0)}/100"
    )


def _format_scanner_signal(signal: dict, title: str, is_futures: bool = False) -> str:

    symbol = clean_symbol(signal.get("symbol", ""))

    signal_type = (signal.get("direction") or signal.get("type") or "").upper()

    if signal_type == "LONG":
        direction = "🟢 LONG"
    elif signal_type == "SHORT":
        direction = "🔴 SHORT"
    else:
        direction = "⚪ " + signal_type


    levels = signal.get("trade_levels") or {}

    entry = levels.get("entry", signal.get("price", "—"))
    stop_loss = levels.get("stop_loss", "—")

    tp1 = levels.get("tp1", "—")
    tp2 = levels.get("tp2", "—")
    tp3 = levels.get("tp3", "—")
    tp4 = levels.get("tp4", "—")


    score = min(
        signal.get("score", 0),
        100
    )


    leverage_line = ""

    if is_futures:

        leverage = suggest_leverage(
            score,
            signal.get("risks", [])
        )

        leverage_line = (
            f"\n⚡ اهرم پیشنهادی\n"
            f"{leverage}"
        )


    reasons = signal.get("reasons") or []
    risks = signal.get("risks") or []

    if reasons:

        reason_text = "\n".join(
            [
                f"✅ {r}"
                for r in reasons[:5]
            ]
        )

    else:

        reason_text = (
            "✅ تحلیل ترکیبی بازار\n"
            "✅ بررسی حجم و روند قیمت"
        )

    risk_block = ""
    if risks:
        risk_lines = "\n".join([f"⚠ {r}" for r in risks[:3]])
        risk_block = f"\n\n⚠️ ریسک\n\n{risk_lines}"

    trend = "صعودی 📈" if signal_type == "LONG" else "نزولی 📉"

    return f"""
{direction} | {symbol}

💰 ورود
{entry}

🎯 اهداف سود

🥇 TP1: {tp1}
🥈 TP2: {tp2}
🥉 TP3: {tp3}
🏆 TP4: {tp4}

🛑 حد ضرر
{stop_loss}
{leverage_line}

📊 اطمینان
{score}/100

📈 روند
{trend}

🧠 دلیل سیگنال

{reason_text}
{risk_block}

⚠️ مدیریت سرمایه را رعایت کنید.
"""

def format_futures_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "Futures", is_futures=True)


def format_spot_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "Spot", is_futures=False)


def format_market_signal_v2(signal: dict) -> str:
    return _format_scanner_signal(signal, "Market", is_futures=False)


def format_catalyst_alert(signal: dict) -> str:
    """
    هشدار الگوی جهش کاتالیزوری شبیه AKE/BANK - مستقل از امتیاز کانفلوئنس ارسال می‌شود
    (چون این‌طور حرکت‌ها معمولاً سریع‌تر از رسیدن به آستانه‌ی SIGNAL کامل اتفاق می‌افتن).
    """

    symbol = clean_symbol(signal.get("symbol", ""))
    c = signal.get("catalyst_breakout", {}) or {}
    current_price = signal.get("current_price", "—")

    reasons_text = "\n".join(f"• {r}" for r in c.get("reasons", [])) or "—"

    return f"""
🚀 الگوی مشابه AKE/BANK | {symbol}

💰 قیمت فعلی
{current_price}

📊 حجم نسبت به میانگین ۲۰ روزه
{c.get('volume_ratio', '—')}×

📈 رشد ۳ روز اخیر
{c.get('change_3d', '—')}٪

🧠 دلایل تطبیق ({c.get('hits', 0)}/4)
{reasons_text}

⚠️ این یک هشدار الگوی رفتاری است، نه سیگنال معاملاتی کامل با حد سود/ضرر.
قبل از خرید، ریسک/ریوارد و نقدشوندگی رو خودت بررسی کن.
"""


def format_trendline_alert(signal: dict) -> str:
    """
    هشدار شکست خط روند بلندمدت (۹۰ و ۱۸۰ روزه هم‌راستا). اولویت پایین‌تر از
    catalyst_breakout است - صرفا جنبه‌ی اطلاع‌رسانی دارد.
    """

    symbol = clean_symbol(signal.get("symbol", ""))
    t = signal.get("trendline_break", {}) or {}
    current_price = signal.get("current_price", "—")

    direction = t.get("trend_direction")
    icon = "📉" if direction == "UP" else "📈"

    return f"""
📐 شکست خط روند بلندمدت | {symbol}

{icon} {t.get('label', '—')}

💰 قیمت فعلی
{current_price}

📏 مقدار خط روند (بازه ۹۰ روزه)
{t.get('trend_value_90d', '—')}

📏 مقدار خط روند (بازه ۱۸۰ روزه)
{t.get('trend_value_180d', '—')}

ℹ️ این یک هشدار اطلاعاتی است؛ اهمیتش کمتر از هشدار الگوی کاتالیزوری بالاست.
"""

def format_coiling_alert(signal: dict) -> str:
    """
    هشدار Pre-Breakout / Coiling.
    مستقل از SIGNAL و REJECT.
    """

    symbol = clean_symbol(
        signal.get(
            "symbol",
            ""
        )
    )

    coiling = (
        signal.get(
            "coiling_setup"
        )
        or {}
    )

    current_price = signal.get(
        "current_price",
        "—"
    )

    reasons = coiling.get(
        "reasons",
        []
    )

    reasons_text = "\n".join(
        f"• {reason}"
        for reason in reasons
    )

    if not reasons_text:
        reasons_text = "—"

    return f"""
⚡ PRE-BREAKOUT SETUP

🔍 احتمال آماده‌شدن برای حرکت بزرگ

🪙 نماد
{symbol}

💰 قیمت فعلی
{current_price}

📊 امتیاز فشردگی
{coiling.get('score', '—')}/100

📉 فشردگی نوسان
{"✅ تایید شد" if coiling.get("volatility_compression") else "❌ تایید نشد"}

🔻 فشردگی Bollinger Bands
{"✅ تایید شد" if coiling.get("bollinger_squeeze") else "❌ تایید نشد"}

📈 روند حجم
{"✅ افزایش تدریجی" if coiling.get("volume_accumulation") else "❌ تایید نشد"}

🐋 OBV
{"✅ صعودی" if coiling.get("obv_rising") else "❌ تایید نشد"}

🚀 وضعیت قیمت
{"✅ هنوز بیش از حد پامپ نکرده" if coiling.get("price_not_overextended") else "⚠️ احتمالاً حرکت شروع شده"}

📏 فاصله تا مقاومت
{coiling.get("resistance_distance", "—")}%

🧠 دلایل

{reasons_text}

⚠️ این سیگنال خرید قطعی نیست.
این هشدار فقط نشان می‌دهد ارز ممکن است در مرحله فشردگی و آماده‌شدن برای شکست قرار داشته باشد.
"""

