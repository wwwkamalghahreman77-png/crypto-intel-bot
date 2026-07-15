"""
جلوگیری از ارسال سیگنال تکراری برای یک ارز با وضعیت و امتیاز مشابه
"""

from database.db import db, now_str


def already_sent(symbol: str, signal_type: str, price: float, score: float) -> bool:
    try:
        rows = db.fetch_by_token("signal_history", symbol)
    except Exception:
        return False

    for row in rows:
        if row.get("signal_type") == signal_type and abs(row.get("score", 0) - score) < 5:
            return True

    return False


def mark_sent(symbol: str, signal_type: str, price: float, score: float):
    try:
        db.insert("signal_history", {
            "token": symbol,
            "signal_type": signal_type,
            "price": price,
            "score": score,
            "date_found": now_str(),
        })
    except Exception as e:
        print("[SignalHistory] خطا در ذخیره:", e)
