def format_dex_discovery(discovery: dict) -> str:

    record = discovery["record"]

    reasons = discovery.get("reasons") or ["اطلاعات کافی نیست"]
    risks = discovery.get("risks") or ["ریسک قابل توجهی یافت نشد"]

    reasons_text = "\n".join([f"✅ {r}" for r in reasons])
    risks_text = "\n".join([f"⚠️ {r}" for r in risks])

    return f"""
🚨 کشف DEX

ارز:
{record.token}

شبکه:
{record.network}

نقدینگی:
${record.liquidity:,.0f}

حجم:
${record.volume:,.0f}

امنیت:
{record.security_score}/100

امتیاز DEX:
{record.dex_score}/100

دلایل:
{reasons_text}

ریسک‌ها:
{risks_text}
"""


def format_crypto_report(report: dict) -> str:

    reasons_text = "\n".join([f"✅ {r}" for r in report.get("reasons", [])]) or "موردی ثبت نشده"
    risks_text = "\n".join([f"⚠️ {r}" for r in report.get("risks", [])]) or "ریسک قابل توجهی یافت نشد"

    return f"""
🧠 گزارش تحلیل ارز

ارز:
{report['token']}

بازار:
{report.get('market','نامشخص')}

امتیاز:
{report['total_score']}/100

دلایل:
{reasons_text}

ریسک‌ها:
{risks_text}

وضعیت:
{report['status']}
"""


def format_market_signal(signal: dict) -> str:

    reasons = "\n".join([f"✅ {r}" for r in signal.get("reasons", [])])

    return f"""
🚨 سیگنال بازار

ارز:
{signal.get('symbol')}

نوع:
{signal.get('type','نامشخص')}

قیمت ورود:
{signal.get('price',0)}

تغییر:
{signal.get('change',0)}%

حجم:
{signal.get('volume',0):,.0f} USDT

قدرت:
{signal.get('score',0)}/100

دلایل:
{reasons}
"""


def _format_scanner_signal(signal: dict, title: str) -> str:
    """فرمت کوتاه سیگنال Futures/Spot همراه با نقاط ورود/خروج/استاپ‌لاس"""

    status_label = signal.get("status_label", "🔥 PUMP")
    smart_money = "🐋 پول هوشمند شناسایی شد\n" if signal.get("smart_money_alert") else ""

    rsi = signal.get("rsi")
    rsi_text = f"{rsi}" if rsi is not None else "—"

    volume_spike = signal.get("volume_spike_ratio")
    volume_spike_text = f"{volume_spike}×" if volume_spike is not None else "—"

    levels = signal.get("trade_levels") or {}
    entry = levels.get("entry", "—")
    stop_loss = levels.get("stop_loss", "—")
    tp1 = levels.get("tp1", "—")
    tp2 = levels.get("tp2", "—")
    tp3 = levels.get("tp3", "—")

    top_reasons = signal.get("reasons", [])[:3]
    reasons_text = " | ".join(top_reasons) if top_reasons else "—"

    return (
        f"{status_label}\n"
        f"{smart_money}"
        f"{title} | {signal.get('symbol')} | {signal.get('type','?')}\n"
        f"تغییر: {signal.get('change',0)}% | حجم: {signal.get('volume',0):,.0f} | "
        f"RSI: {rsi_text} | نسبت حجم: {volume_spike_text}\n"
        f"─────────\n"
        f"ورود: {entry}\n"
        f"استاپ‌لاس: {stop_loss}\n"
        f"حد سود ۱: {tp1}\n"
        f"حد سود ۲: {tp2}\n"
        f"حد سود ۳: {tp3}\n"
        f"─────────\n"
        f"امتیاز: {min(signal.get('score',0), 100)}/100\n"
        f"{reasons_text}\n"
        f"⚠️ تحلیلی است، نه تضمین سود. مدیریت سرمایه با خودتان است."
    )


def format_futures_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "Futures")


def format_spot_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "Spot")
