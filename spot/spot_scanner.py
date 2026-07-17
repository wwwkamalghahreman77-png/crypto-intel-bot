"""
spot/spot_scanner.py

اسکنر اسپات - نسخه‌ی مبتنی بر موتور کانفلوئنس (analysis/confluence.py).
مشابه futures_scanner ولی بدون داده مشتقات (فاندینگ/OI/Long-Short که مخصوص فیوچرز است)
و به‌جای آن از امتیاز حجم/تغییر قیمت استفاده می‌شود.
"""

from spot.toobit import get_spot_opportunities, get_klines
from analysis.confluence import run_confluence_analysis

STATUS_LABELS = {
    "BOS_BULLISH": "📈 BOS - ادامه روند صعودی",
    "BOS_BEARISH": "📉 BOS - ادامه روند نزولی",
    "CHOCH_BULLISH": "🔄 CHOCH - برگشت احتمالی به صعودی",
    "CHOCH_BEARISH": "🔄 CHOCH - برگشت احتمالی به نزولی",
    None: "🔥 سیگنال کانفلوئنس",
}


def _prefilter(signals, min_change=3, min_volume=200_000):

    shortlist = []
    for signal in signals:
        change = abs(signal.get("change", 0))
        volume = signal.get("volume", 0)

        if change < min_change or volume < min_volume:
            continue

        shortlist.append(signal)

    shortlist.sort(key=lambda s: abs(s.get("change", 0)) * (s.get("volume", 0) ** 0.1), reverse=True)
    return shortlist[:40]


def scan_spot(max_results=15):

    signals = get_spot_opportunities()
    shortlist = _prefilter(signals)

    print(f"[SpotScanner] {len(shortlist)} کاندید اولیه پس از پیش‌فیلتر")

    results = []

    for signal in shortlist:
        symbol = signal["symbol"]

        analysis = run_confluence_analysis(
            symbol,
            get_klines,
            signal_meta=signal,
            direction="LONG",  # اسپات فقط LONG (بدون شورت)
        )

        if analysis is None or analysis["decision"] == "REJECT":
            continue

        signal.update(analysis)
        signal["status_label"] = STATUS_LABELS.get(analysis.get("structure_signal"), STATUS_LABELS[None])
        results.append(signal)

    results.sort(key=lambda s: s["score"], reverse=True)

    signal_count = sum(1 for r in results if r["decision"] == "SIGNAL")
    watch_count = sum(1 for r in results if r["decision"] == "WATCHLIST")
    print(f"[SpotScanner] {signal_count} سیگنال نهایی / {watch_count} واچ‌لیست")

    return results[:max_results]
