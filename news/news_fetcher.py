"""
news/news_fetcher.py

دریافت اخبار کریپتو از منابع RSS رایگان و بررسی وجود کلمات کلیدی مثبت/منفی
مرتبط با یک توکن خاص (Partnership, Listing, Hack, Lawsuit, ...).

منابع RSS استفاده شده (رایگان، بدون کلید):
    - CoinTelegraph
    - CoinDesk
    - Decrypt

# TODO: برای دقت بالاتر می‌توان به NewsAPI.org (نیازمند کلید رایگان با محدودیت روزانه) وصل شد.
"""

import feedparser

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
]

POSITIVE_KEYWORDS = ["partnership", "listing", "listed", "launch", "integration", "adoption", "upgrade", "mainnet"]
NEGATIVE_KEYWORDS = ["hack", "exploit", "lawsuit", "sec charges", "rug pull", "delist", "ban", "investigation"]


def fetch_all_news(limit_per_feed: int = 30):
    """دریافت آخرین خبرهای همه فیدهای RSS تعریف‌شده."""
    all_entries = []
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:limit_per_feed]:
                all_entries.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": feed_url,
                })
        except Exception as e:
            print(f"[News] خطا در خواندن فید {feed_url}: {e}")
    return all_entries


def analyze_news_for_token(token_symbol: str, token_name: str = None, all_news: list = None) -> dict:
    """
    جستجوی نام/نماد توکن در بین اخبار اخیر و تشخیص مثبت یا منفی بودن.
    """
    if all_news is None:
        all_news = fetch_all_news()

    search_terms = [t.lower() for t in [token_symbol, token_name] if t]
    matched_positive = []
    matched_negative = []
    matched_neutral = []

    for entry in all_news:
        text = (entry["title"] + " " + entry["summary"]).lower()
        if not any(term in text for term in search_terms):
            continue

        if any(kw in text for kw in NEGATIVE_KEYWORDS):
            matched_negative.append(entry["title"])
        elif any(kw in text for kw in POSITIVE_KEYWORDS):
            matched_positive.append(entry["title"])
        else:
            matched_neutral.append(entry["title"])

    score = 50  # نقطه شروع خنثی
    reasons = []
    risks = []

    if matched_positive:
        score += min(40, len(matched_positive) * 15)
        reasons.append(f"{len(matched_positive)} خبر مثبت یافت شد (پارتنرشیپ/لیستینگ/آپدیت) ✅")

    if matched_negative:
        score -= min(60, len(matched_negative) * 30)
        risks.append(f"{len(matched_negative)} خبر منفی یافت شد (هک/شکایت/دی‌لیست) ⚠️")

    if not matched_positive and not matched_negative and not matched_neutral:
        risks.append("هیچ خبر اخیری درباره این پروژه یافت نشد ⚠️")

    score = max(0, min(100, score))

    return {
        "score": round(score, 1),
        "positive_news": matched_positive,
        "negative_news": matched_negative,
        "neutral_news": matched_neutral,
        "reasons": reasons,
        "risks": risks,
    }
