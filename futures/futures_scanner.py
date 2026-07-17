"""
futures/futures_scanner.py

اسکنر فیوچرز - نسخه‌ی مبتنی بر موتور کانفلوئنس (analysis/confluence.py).
منطق قدیمی امتیازدهی ساده حذف و با امتیازدهی چندبعدی (اندیکاتور + SMC + MTF + مشتقات) جایگزین شد.
خروجی هر آیتم شامل کلید "decision" است: SIGNAL / WATCHLIST / REJECT (فقط دو مورد اول برگردانده می‌شوند).

فیوچرز عمداً سخت‌گیرتر از پیش‌فرض مشترک (۵۵) تنظیم شده: ۷۰ برای SIGNAL،
چون تست واقعی نشون داد با ۵۵ نسبت بالایی از کاندیدها سیگنال کامل می‌گرفتن
(۱۱ از ۱۶). هدف اینه تعداد کمتر ولی قوی‌تر باشه.
"""

from futures.toobit import get_futures_opportunities, get_klines
from futures.derivatives import analyze_derivatives
from analysis.confluence import run_confluence_analysis

STATUS_LABELS = {
    "BOS_BULLISH": "📈 BOS - ادامه روند صعودی",
    "BOS_BEARISH": "📉 BOS - ادامه روند نزولی",
    "CHOCH_BULLISH": "🔄 CHOCH - برگشت احتمالی به صعودی",
    "CHOCH_BEARISH": "🔄 CHOCH - برگشت احتمالی به نزولی",
    None: "🔥 سیگنال کانفلوئنس",
}


def _prefilter(signals, min_change=3, min_volume=200_000):
    """پیش‌فیلتر سریع و ارزان قبل از تحلیل سنگین کانفلوئنس (کاهش تعداد فراخوانی API)"""

    shortlist = []
    for signal in signals:
        change = abs(signal.get("change", 0))
        volume = signal.get("volume", 0)

        if change < min_change or volume < min_volume:
            continue

        shortlist.append(signal)

    shortlist.sort(key=lambda s: abs(s.get("change", 0)) * (s.get("volume", 0) ** 0.1), reverse=True)
    return shortlist[:40]


def scan_futures(max_results=15):

    signals = get_futures_opportunities()
    shortlist = _prefilter(signals)

    print(f"[FuturesScanner] {len(shortlist)} کاندید اولیه پس از پیش‌فیلتر")

    results = []
    all_scores = []

    for signal in shortlist:
        symbol = signal["symbol"]
        direction = signal.get("type", "LONG")

        analysis = run_confluence_analysis(
            symbol,
            get_klines,
            signal_meta=signal,
            direction=direction,
            extra_analyzer=analyze_derivatives,
            min_signal_score=70,     # فیوچرز سخت‌گیرتر از پیش‌فرض (۵۵) - کمتر ولی قوی‌تر
            min_watchlist_score=50,
        )

        if analysis is None:
            continue

        all_scores.append(analysis["score"])

        if analysis["decision"] == "REJECT":
            continue

        signal.update(analysis)
        signal["status_label"] = STATUS_LABELS.get(analysis.get("structure_signal"), STATUS_LABELS[None])
        results.append(signal)

    results.sort(key=lambda s: s["score"], reverse=True)

    if all_scores:
        print(f"[FuturesScanner] امتیازها: max={max(all_scores)} avg={round(sum(all_scores)/len(all_scores), 1)} (n={len(all_scores)})")

    signal_count = sum(1 for r in results if r["decision"] == "SIGNAL")
    watch_count = sum(1 for r in results if r["decision"] == "WATCHLIST")
    print(f"[FuturesScanner] {signal_count} سیگنال نهایی / {watch_count} واچ‌لیست")

    return results[:max_results]
