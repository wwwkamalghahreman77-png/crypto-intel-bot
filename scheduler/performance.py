"""
scheduler/performance.py

محاسبه آمار عملکرد ربات از روی جدول closed_trades:
    - نرخ برد (Win Rate)
    - میانگین ریسک به ریوارد (Average RR)
    - میانگین مدت زمان معامله
    - سود ماهانه (Monthly Profit)
    - بهترین و بدترین ستاپ‌ها
"""

from datetime import datetime, timedelta
from database.db import db


def get_performance_summary(days: int = 30) -> dict:

    trades = db.fetch_all("closed_trades", limit=1000)

    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_rr": 0,
            "avg_duration_hours": 0,
            "monthly_profit_pct": 0,
            "best_trade": None,
            "worst_trade": None,
        }

    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = []

    for t in trades:
        try:
            closed_at = datetime.strptime(t.get("date_closed", ""), "%Y-%m-%d %H:%M:%S")
        except Exception:
            closed_at = None

        if closed_at is None or closed_at >= cutoff:
            recent.append(t)

    pool = recent if recent else trades

    total = len(pool)
    wins = [t for t in pool if (t.get("result_pct") or 0) > 0]
    win_rate = round(len(wins) / total * 100, 1) if total else 0

    rr_values = [t["risk_reward"] for t in pool if t.get("risk_reward")]
    avg_rr = round(sum(rr_values) / len(rr_values), 2) if rr_values else 0

    durations = [t["duration_hours"] for t in pool if t.get("duration_hours")]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0

    monthly_profit_pct = round(sum(t.get("result_pct", 0) for t in pool), 2)

    sorted_by_result = sorted(pool, key=lambda t: t.get("result_pct", 0), reverse=True)
    best_trade = sorted_by_result[0] if sorted_by_result else None
    worst_trade = sorted_by_result[-1] if sorted_by_result else None

    return {
        "total_trades": total,
        "win_rate": win_rate,
        "avg_rr": avg_rr,
        "avg_duration_hours": avg_duration,
        "monthly_profit_pct": monthly_profit_pct,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
    }


def format_performance_report(days: int = 30) -> str:

    stats = get_performance_summary(days)

    if stats["total_trades"] == 0:
        return "📊 هنوز معامله بسته‌شده‌ای برای گزارش عملکرد ثبت نشده است."

    best = stats["best_trade"]
    worst = stats["worst_trade"]

    best_line = f"{best['symbol']} ({best['result_pct']}%)" if best else "—"
    worst_line = f"{worst['symbol']} ({worst['result_pct']}%)" if worst else "—"

    return f"""
📊 گزارش عملکرد ({days} روز اخیر)

🔢 تعداد معاملات: {stats['total_trades']}
🎯 نرخ برد: {stats['win_rate']}%
⚖️ میانگین ریسک/ریوارد: {stats['avg_rr']}
⏱ میانگین مدت معامله: {stats['avg_duration_hours']} ساعت
💰 مجموع سود/زیان: {stats['monthly_profit_pct']}%

🏆 بهترین معامله: {best_line}
📉 بدترین معامله: {worst_line}
"""
