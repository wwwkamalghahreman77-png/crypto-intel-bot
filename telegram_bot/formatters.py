"""
telegram_bot/formatters.py

ساخت متن پیام‌های تلگرام دقیقاً بر اساس فرمت خواسته‌شده در پروژه.
"""


def format_dex_discovery(discovery: dict) -> str:
    record = discovery["record"]
    reasons = discovery["reasons"] or ["اطلاعات کافی نیست"]
    risks = discovery["risks"] or ["ریسک قابل توجهی یافت نشد"]

    reasons_text = "\n".join([f"✅ {r}" for r in reasons])
    risks_text = "\n".join([f"⚠️ {r}" for r in risks])

    return f"""🚨 DEX GEM DISCOVERY

Token: {record.token}
Network: {record.network}
Liquidity: ${record.liquidity:,.0f}
Volume: ${record.volume:,.0f}

Security Score: {record.security_score}/100
DEX Score: {record.dex_score}/100

Reasons:
{reasons_text}

Risks:
{risks_text}

Status: {record.status}"""


def format_crypto_report(report: dict) -> str:
    reasons_text = "\n".join([f"✅ {r}" for r in report.get("reasons", [])]) or "✅ موردی ثبت نشده"
    risks_text = "\n".join([f"⚠️ {r}" for r in report.get("risks", [])]) or "⚠️ ریسک قابل توجهی یافت نشد"

    return f"""🧠 CRYPTO INTELLIGENCE REPORT

Token: {report['token']}
Category: {report.get('narrative', 'نامشخص')}
Market: {report.get('market', 'نامشخص')}

Total Score: {report['total_score']}/100

Security: {report['security']}/100
Fundamental: {report['fundamental']}/100
News: {report['news']}/100
Technical: {report['technical']}/100
Community: {report['community']}/100

Reasons:
{reasons_text}

Risks:
{risks_text}

Status: {report['status']}"""
