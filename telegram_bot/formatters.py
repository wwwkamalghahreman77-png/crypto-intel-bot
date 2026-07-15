def format_dex_discovery(discovery: dict) -> str:

    record = discovery["record"]

    reasons = discovery.get("reasons") or [
        "اطلاعات کافی نیست"
    ]

    risks = discovery.get("risks") or [
        "ریسک قابل توجهی یافت نشد"
    ]

    reasons_text = "\n".join(
        [f"✅ {r}" for r in reasons]
    )

    risks_text = "\n".join(
        [f"⚠️ {r}" for r in risks]
    )

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

    reasons_text = "\n".join(
        [f"✅ {r}" for r in report.get("reasons", [])]
    ) or "موردی ثبت نشده"


    risks_text = "\n".join(
        [f"⚠️ {r}" for r in report.get("risks", [])]
    ) or "ریسک قابل توجهی یافت نشد"


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

    reasons = "\n".join(
        [
            f"✅ {r}"
            for r in signal.get("reasons", [])
        ]
    )

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
    """تابع مشترک برای فرمت سیگنال‌های Futures و Spot (چون ساختارشون یکیه)."""

    reasons = "\n".join(
        [f"✅ {r}" for r in signal.get("reasons", [])]
    ) or "موردی ثبت نشده"

    risks = "\n".join(
        [f"⚠️ {r}" for r in signal.get("risks", [])]
    ) or "ریسک قابل توجهی یافت نشد"

    status_label = signal.get("status_label", "🔥 PUMP CONFIRMED")

    rsi = signal.get("rsi")
    rsi_text = f"{rsi}" if rsi is not None else "نامشخص"

    volume_spike = signal.get("volume_spike_ratio")
    volume_spike_text = f"{volume_spike}×" if volume_spike is not None else "نامشخص"

    return f"""
{status_label}

{title}

ارز:
{signal.get('symbol')}

نوع معامله:
{signal.get('type','نامشخص')}

تغییر ۲۴ ساعته:
{signal.get('change',0)}%

حجم ۲۴ ساعته:
{signal.get('volume',0):,.0f} USDT

نسبت حجم به میانگین:
{volume_spike_text}

RSI ساعتی:
{rsi_text}

قدرت سیگنال (امتیاز نهایی):
{signal.get('score',0)}/100

دلایل:
{reasons}

ریسک‌ها:
{risks}

⚠️ این یک سیگنال تحلیلی است، نه توصیه سرمایه‌گذاری یا تضمین سود.
"""


def format_futures_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "بازار Futures")


def format_spot_signal(signal: dict) -> str:
    return _format_scanner_signal(signal, "بازار Spot")
