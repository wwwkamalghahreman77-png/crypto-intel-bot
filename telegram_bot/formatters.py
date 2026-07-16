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
    badges = build_badges(signal)
    reason = build_short_reason(signal)

    levels = signal.get("trade_levels") or {}
    entry = levels.get("entry", "—")
    stop_loss = levels.get("stop_loss", "—")
    tp1 = levels.get("tp1", "—")
    tp2 = levels.get("tp2", "—")
    tp3 = levels.get("tp3", "—")

    leverage_line = ""
    if is_futures:
        leverage = suggest_leverage(signal.get("score", 0), signal.get("risks", []))
        leverage_line = f"اهرم پیشنهادی: {leverage}\n"

    return (
        f"{badges} {title} | {symbol} | {signal.get('type','?')}\n"
        f"{reason}\n"
        f"ورود: {entry} | استاپ: {stop_loss}\n"
        f"TP: {tp1} / {tp2} / {tp3}\n"
        f"{leverage_line}"
        f"امتیاز: {min(signal.get('score',0), 100)}/100\n"
        f"⚠️ تحلیلی است، نه تضمین سود."
    )


def format_futures_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "Futures", is_futures=True)


def format_spot_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "Spot", is_futures=False)
