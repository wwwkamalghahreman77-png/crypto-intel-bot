"""
وظایف اصلی ربات
"""

from dex.gem_scanner import run_full_scan
from telegram_bot.bot import send_message
from telegram_bot.formatters import (
    format_dex_discovery,
    format_crypto_report,
    format_market_signal_v2,
    format_futures_signal,
    format_spot_signal
)

from analysis.technical import analyze_technical
from analysis.fundamental import analyze_fundamental
from analysis.scoring import calculate_total_score, classify_status

from news.news_fetcher import analyze_news_for_token, fetch_all_news

from config.settings import settings
from database.db import db, now_str
from database.models import CryptoReport

from database.signal_history import already_sent, mark_sent


MIN_SIGNAL_SCORE = 80


def save_active_signal(signal, message_id=None):

    levels = signal.get("trade_levels", {})

    data = {
        "symbol": signal.get("symbol"),
        "signal_type": signal.get("type", "LONG"),

        "entry_price": levels.get("entry", 0),

        "tp1": levels.get("tp1", 0),
        "tp2": levels.get("tp2", 0),
        "tp3": levels.get("tp3", 0),
        "tp4": levels.get("tp4", 0),

        "stop_loss": levels.get("stop_loss", 0),

        "telegram_chat_id": settings.telegram_chat_id,
        "telegram_message_id": message_id,

        "status": "active",

        "hit_tp1": 0,
        "hit_tp2": 0,
        "hit_tp3": 0,
        "hit_tp4": 0,
        "hit_stop": 0,

        "date_found": now_str()
    }

    db.insert("active_signals", data)



def active_signal_exists(symbol):

    try:

        rows = db.fetch_all(
            "active_signals",
            limit=500
        )

        for row in rows:

            if (
                row.get("symbol") == symbol
                and row.get("status") == "active"
            ):
                return True

    except Exception as e:

        print(
            "[Active Signal Check]",
            e
        )

    return False




def job_dex_scan():

    print("[Job] شروع DEX Gem Scan ...")

    discoveries = run_full_scan()

    for d in discoveries:

        send_message(
            format_dex_discovery(d)
        )


    print(
        f"[Job] پایان اسکن - {len(discoveries)} مورد"
    )

    return discoveries





def analyze_project(
    co
