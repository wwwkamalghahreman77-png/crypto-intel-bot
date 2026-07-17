"""
market_scanner/signal_detector.py

اسکنر عمومی بازار (حرکات غیرعادی) - به‌روزرسانی‌شده برای استفاده از موتور کانفلوئنس مشترک.
قبلا از confirm_multi_timeframe در spot_scanner استفاده می‌کرد که در بازنویسی حذف شد؛
اکنون مستقیما از analysis.confluence.run_confluence_analysis استفاده می‌شود.
"""

from market_scanner.market_watcher import find_unusual_moves
from spot.toobit import get_klines
from analysis.confluence import run_confluence_analysis

STATUS_LABELS = {
    "BOS_BULLISH": "📈 BOS - ادامه روند صعودی",
    "BOS_BEARISH": "📉 BOS - ادامه روند نزولی",
    "CHOCH_BULLISH": "🔄 CHOCH - برگشت احتمالی به صعودی",
    "CHOCH_BEARISH": "🔄 CHOCH - برگشت احتمالی به نزولی",
    None: "🔥 سیگنال کانفلوئنس",
}


def scan_for_signals(max_results=15):

    coins = find_unusual_moves()

    shortlist = [c for c in coins if c.get("change", 0) >= 2 and c.get("volume", 0) >= 300_000]
    shortlist.sort(key=lambda s: s.get("score", 0), reverse=True)
    shortlist = shortlist[:40]

    print(f"[MarketScanner] {len(shortlist)} کاندید اولیه")

    results = []

    for signal in shortlist:
        symbol = signal["symbol"]

        analysis = run_confluence_analysis(
            symbol,
            get_klines,
            signal_meta=signal,
            direction="LONG",
        )

        if analysis is None or analysis["decision"] == "REJECT":
            continue

        signal.update(analysis)
        signal["status_label"] = STATUS_LABELS.get(analysis.get("structure_signal"), STATUS_LABELS[None])
        results.append(signal)

    results.sort(key=lambda s: s["score"], reverse=True)

    print(f"[MarketScanner] {len(results)} سیگنال/واچ‌لیست نهایی")

    return results[:max_results]
