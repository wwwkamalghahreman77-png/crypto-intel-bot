from database.db import db, now_str


def already_sent(symbol, signal_type, entry_price, score):

    rows = db.fetch_all(
        "signal_history",
        limit=100
    )

    for row in rows:

        if (
            row["symbol"] == symbol
            and row["signal_type"] == signal_type
            and abs((row["entry_price"] or 0) - entry_price) < 1
            and abs((row["score"] or 0) - score) < 5
        ):
            return True

    return False



def mark_sent(symbol, signal_type, entry_price, score):

    db.insert(
        "signal_history",
        {
            "symbol": symbol,
            "signal_type": signal_type,
            "entry_price": entry_price,
            "score": score,
            "created_at": now_str()
        }
    )
