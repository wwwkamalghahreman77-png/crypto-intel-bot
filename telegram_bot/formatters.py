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
    def format_futures_signal(signal: dict) -> str:

    return f"""
🚨 سیگنال فیوچرز

ارز:
{signal.get('symbol')}

نوع معامله:
{signal.get('type')}

تغییر:
{signal.get('change')}%

حجم:
{signal.get('volume',0):,.0f} USDT

قدرت سیگنال:
{signal.get('score')}/100

دلایل:
{chr(10).join(['✅ '+r for r in signal.get('reasons',[])])}
"""
