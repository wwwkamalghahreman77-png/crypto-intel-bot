"""
scheduler/jobs.py

وظایف اصلی که یا توسط GitHub Actions (اجرای دوره‌ای یک‌باره) یا
توسط APScheduler (در صورت اجرای دائمی روی یک سرور رایگان) فراخوانی می‌شوند.
"""

from dex.gem_scanner import run_full_scan
from telegram_bot.bot import send_message
from telegram_bot.formatters import format_dex_discovery, format_crypto_report
from analysis.technical import analyze_technical
from analysis.fundamental import analyze_fundamental
from analysis.scoring import calculate_total_score, classify_status
from news.news_fetcher import analyze_news_for_token, fetch_all_news
from database.db import db, now_str
from database.models import CryptoReport


def job_dex_scan():
    """ماژول ۱: اسکن توکن‌های جدید و ارسال گزارش کشف‌ها به تلگرام."""
    print("[Job] شروع DEX Gem Scan ...")
    discoveries = run_full_scan()
    for d in discoveries:
        send_message(format_dex_discovery(d))
    print(f"[Job] پایان اسکن - {len(discoveries)} مورد کشف شد.")
    return discoveries


def analyze_project(coin_id: str, token_symbol: str, market: str = "N/A"):
    """
    ماژول ۲: تحلیل کامل یک پروژه شناخته‌شده (coin_id باید شناسه CoinGecko باشد،
    مثلاً 'bitcoin', 'ethereum', 'solana').

    نکات امنیتی و Community-score کامل در این تابع ساده‌سازی شده و
    قابل توسعه با داده‌های دقیق‌تر (مثل تحلیل عمیق‌تر شبکه اجتماعی) است.
    """
    print(f"[Job] تحلیل پروژه: {token_symbol} ({coin_id})")

    fundamental = analyze_fundamental(coin_id)
    technical = analyze_technical(coin_id)

    all_news = fetch_all_news()
    news = analyze_news_for_token(token_symbol, coin_id, all_news)

    # امتیاز Community از داده فاندامنتال استخراج می‌شود (توییتر/تلگرام)
    community_score = 0
    if fundamental.get("available"):
        if fundamental.get("twitter_followers", 0) > 50000:
            community_score += 50
        if (fundamental.get("telegram_users") or 0) > 10000:
            community_score += 50
        community_score = min(100, community_score)

    # امنیت پایه (در این ماژول، صرفاً بر اساس در دسترس بودن اطلاعات؛
    # برای بررسی امنیتی عمیق‌تر از ماژول dex/security.py روی قرارداد استفاده می‌شود)
    security_score = 70 if fundamental.get("available") else 30

    # Narrative score: اگر دسته‌بندی مشخص شد امتیاز کامل، وگرنه نصف
    narrative_score = 100 if fundamental.get("narrative", "Uncategorized") != "Uncategorized" else 40

    scores = {
        "security": security_score,
        "fundamental": fundamental.get("score", 0),
        "news": news.get("score", 0),
        "narrative": narrative_score,
        "technical": technical.get("score", 0),
        "community": community_score,
        "liquidity": 50,  # TODO: می‌توان از داده حجم بازار CoinGecko دقیق‌تر محاسبه کرد
    }

    total_score = calculate_total_score(scores)
    status = classify_status(total_score)

    reasons = fundamental.get("reasons", []) + news.get("reasons", [])
    risks = fundamental.get("risks", []) + news.get("risks", [])

    report = CryptoReport(
        token=token_symbol.upper(),
        date_found=now_str(),
        total_score=total_score,
        security=security_score,
        fundamental=fundamental.get("score", 0),
        news=news.get("score", 0),
        technical=technical.get("score", 0),
        community=community_score,
        status=status,
    )

    db.insert("crypto_reports", report.to_dict())

    report_dict = report.to_dict()
    report_dict["narrative"] = fundamental.get("narrative", "نامشخص")
    report_dict["market"] = market
    report_dict["reasons"] = reasons
    report_dict["risks"] = risks

    return report_dict


def job_intelligence_analysis(watchlist_coins: list):
    """
    ماژول ۲: اجرای تحلیل روی لیستی از پروژه‌ها.
    watchlist_coins: لیستی از دیکشنری‌ها مثل [{"coin_id": "solana", "symbol": "SOL"}, ...]
    """
    print("[Job] شروع Crypto Intelligence Analysis ...")
    reports = []
    for coin in watchlist_coins:
        report = analyze_project(coin["coin_id"], coin["symbol"], coin.get("market", "N/A"))
        send_message(format_crypto_report(report))
        reports.append(report)
    print(f"[Job] پایان تحلیل - {len(reports)} گزارش تولید شد.")
    return reports

def job_market_scan():
    """
    اسکن فرصت‌های احتمالی قبل از پامپ
    """

    print("[Job] شروع Market Scanner ...")

    from market_scanner.signal_detector import scan_for_signals

    signals = scan_for_signals()

    for signal in signals:

        message = f"""
🟢 فرصت احتمالی بازار

ارز: {signal['symbol']}

تغییر:
{signal['change']}%

حجم:
{signal['volume']:,.0f} USDT

امتیاز:
{signal['score']}/100

دلایل:
{', '.join(signal['reasons'])}
"""

        send_message(message)

    print(f"[Job] پایان Market Scanner - {len(signals)} مورد")
