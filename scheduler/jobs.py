"""
وظایف اصلی ربات
"""

from dex.gem_scanner import run_full_scan
from telegram_bot.bot import send_message
from telegram_bot.formatters import (
    format_dex_discovery,
    format_crypto_report,
    format_market_signal,
    format_futures_signal,
    format_spot_signal
)

from analysis.technical import analyze_technical
from analysis.fundamental import analyze_fundamental
from analysis.scoring import calculate_total_score, classify_status

from news.news_fetcher import analyze_news_for_token, fetch_all_news

from database.db import db, now_str
from database.models import CryptoReport

from database.signal_history import already_sent, mark_sent



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

        "telegram_chat_id": None,
        "telegram_message_id": message_id,

        "status": "active",

        "hit_tp1": 0,
        "hit_tp2": 0,
        "hit_tp3": 0,
        "hit_tp4": 0,
        "hit_stop": 0,

        "date_found": now_str()
    }

    db.insert(
        "active_signals",
        data
    )



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
    coin_id,
    token_symbol,
    market="N/A"
):

    print(
        f"[Job] تحلیل پروژه: {token_symbol}"
    )


    fundamental = analyze_fundamental(
        coin_id
    )

    technical = analyze_technical(
        coin_id
    )


    news_data = fetch_all_news()


    news = analyze_news_for_token(
        token_symbol,
        coin_id,
        news_data
    )



    scores = {

        "security": 70 if fundamental.get("available") else 30,

        "fundamental": fundamental.get("score",0),

        "news": news.get("score",0),

        "technical": technical.get("score",0),

        "community": 0,

        "liquidity": 50,

        "narrative": 50
    }



    total = calculate_total_score(
        scores
    )


    status = classify_status(
        total
    )



    report = CryptoReport(

        token=token_symbol.upper(),

        date_found=now_str(),

        total_score=total,

        security=scores["security"],

        fundamental=scores["fundamental"],

        news=scores["news"],

        technical=scores["technical"],

        community=scores["community"],

        status=status

    )


    db.insert(
        "crypto_reports",
        report.to_dict()
    )



    result = report.to_dict()

    result["market"] = market

    result["reasons"] = (
        fundamental.get("reasons",[])
        +
        news.get("reasons",[])
    )

    result["risks"] = (
        fundamental.get("risks",[])
        +
        news.get("risks",[])
    )


    return result





def job_market_scan():

    print(
        "[Job] شروع Market Scanner"
    )


    from market_scanner.signal_detector import scan_for_signals


    signals = scan_for_signals()



    for signal in signals:


        symbol = signal.get(
            "symbol"
        )


        if active_signal_exists(symbol):

            continue



        if already_sent(
            symbol,
            signal.get("type","UNKNOWN"),
            signal.get("price",0),
            signal.get("score",0)
        ):

            continue



        mark_sent(
            symbol,
            signal.get("type","UNKNOWN"),
            signal.get("price",0),
            signal.get("score",0)
        )



        send_message(
            format_market_signal(signal)
        )



    print(
        f"[Job] پایان Market Scanner - {len(signals)} مورد"
    )





def job_futures_scan():

    print(
        "[Job] شروع Futures Scanner"
    )


    from futures.futures_scanner import scan_futures


    signals = scan_futures()



    for signal in signals:


        symbol = signal.get(
            "symbol"
        )


        if active_signal_exists(symbol):

            continue



        if already_sent(
            symbol,
            signal.get("structure_signal")
            or signal.get("type","UNKNOWN"),

            signal.get("score",0),

            signal.get("score",0)
        ):

            continue



        mark_sent(
            symbol,
            signal.get("structure_signal")
            or signal.get("type","UNKNOWN"),

            signal.get("score",0),

            signal.get("score",0)
        )



        message_id = send_message(
            format_futures_signal(signal)
        )



        save_active_signal(
            signal,
            message_id
        )



    print(
        f"[Job] پایان Futures Scanner - {len(signals)} مورد"
    )






def job_spot_scan():

    print(
        "[Job] شروع Spot Scanner"
    )


    from spot.spot_scanner import scan_spot


    signals = scan_spot()



    for signal in signals:


        symbol = signal.get(
            "symbol"
        )


        if active_signal_exists(symbol):

            continue



        if already_sent(
            symbol,
            signal.get("structure_signal")
            or signal.get("type","UNKNOWN"),

            signal.get("score",0),

            signal.get("score",0)

        ):

            continue



        mark_sent(
            symbol,
            signal.get("structure_signal")
            or signal.get("type","UNKNOWN"),

            signal.get("score",0),

            signal.get("score",0)

        )



        message_id = send_message(
            format_spot_signal(signal)
        )


        save_active_signal(
            signal,
            message_id
        )



    print(
        f"[Job] پایان Spot Scanner - {len(signals)} مورد"
    )
