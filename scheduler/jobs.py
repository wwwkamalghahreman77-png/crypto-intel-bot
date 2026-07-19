"""
scheduler/jobs.py
"""

from telegram_bot.bot import send_message

from telegram_bot.formatters import (
    format_market_signal_v2,
    format_futures_signal,
    format_spot_signal,
    format_catalyst_alert,
    format_trendline_alert,
    format_coiling_alert,
)

from database.db import db, now_str
from database.signal_history import already_sent, mark_sent

from config.settings import settings


MIN_SIGNAL_SCORE = 55


def save_active_signal(
    signal,
    message_id=None
):

    levels = (
        signal.get(
            "trade_levels",
            {}
        )
    )

    data = {

        "symbol":
            signal.get(
                "symbol"
            ),

        "signal_type":
            signal.get(
                "direction",
                "LONG"
            ),

        "entry_price":
            levels.get(
                "entry",
                0
            ),

        "tp1":
            levels.get(
                "tp1",
                0
            ),

        "tp2":
            levels.get(
                "tp2",
                0
            ),

        "tp3":
            levels.get(
                "tp3",
                0
            ),

        "tp4":
            levels.get(
                "tp4",
                0
            ),

        "stop_loss":
            levels.get(
                "stop_loss",
                0
            ),

        "telegram_chat_id":
            settings.telegram_chat_id,

        "telegram_message_id":
            message_id,

        "status":
            "active",

        "hit_tp1":
            0,

        "hit_tp2":
            0,

        "hit_tp3":
            0,

        "hit_tp4":
            0,

        "hit_stop":
            0,

        "date_found":
            now_str(),
    }

    db.insert(
        "active_signals",
        data
    )


def active_signal_exists(
    symbol
):

    try:

        rows = db.fetch_all(
            "active_signals",
            limit=500
        )

        for row in rows:

            if (
                row.get(
                    "symbol"
                )
                == symbol
                and
                row.get(
                    "status"
                )
                == "active"
            ):

                return True

    except Exception as e:

        print(
            "[Active Signal Check]",
            e
        )

    return False


def log_telegram_message(
    message_type,
    symbol,
    message_id,
    reply_to=None,
    preview=""
):

    try:

        db.insert(
            "telegram_messages",
            {

                "message_type":
                    message_type,

                "symbol":
                    symbol,

                "telegram_chat_id":
                    settings.telegram_chat_id,

                "telegram_message_id":
                    message_id,

                "reply_to_message_id":
                    reply_to,

                "content_preview":
                    preview[:200],

                "date_sent":
                    now_str(),
            }
        )

    except Exception as e:

        print(
            "[TelegramMessages]",
            e
        )


def check_special_alerts(
    signal
):

    symbol = signal.get(
        "symbol"
    )

    alerts = [

        (
            "catalyst_breakout",
            "CATALYST_BREAKOUT",
            format_catalyst_alert,
            "catalyst_breakout",
        ),

        (
            "trendline_break",
            "TRENDLINE_BREAK",
            format_trendline_alert,
            "trendline_break",
        ),

        (
            "coiling_setup",
            "PRE_BREAKOUT_COILING",
            format_coiling_alert,
            "pre_breakout_coiling",
        ),

    ]

    for key, sent_type, formatter, message_type in alerts:

        alert = (
            signal.get(
                key
            )
            or {}
        )

        confirmed = (
            alert.get(
                "match"
            )
            or
            alert.get(
                "break_confirmed"
            )
        )

        if not confirmed:

            continue

        if already_sent(
            symbol,
            sent_type,
            0,
            0
        ):

            continue

        mark_sent(
            symbol,
            sent_type,
            0,
            0
        )

        text = formatter(
            signal
        )

        message_id = send_message(
            text
        )

        log_telegram_message(
            message_type,
            symbol,
            message_id,
            preview=text
        )


def process_confluence_signal(
    signal,
    formatter
):

    symbol = signal.get(
        "symbol"
    )

    check_special_alerts(
        signal
    )

    if (
        signal.get(
            "decision"
        )
        != "SIGNAL"
    ):

        return

    if active_signal_exists(
        symbol
    ):

        return

    signal_type = (
        signal.get(
            "structure_signal"
        )
        or
        signal.get(
            "direction",
            "UNKNOWN"
        )
    )

    score = signal.get(
        "score",
        0
    )

    if already_sent(
        symbol,
        signal_type,
        score,
        score
    ):

        return

    mark_sent(
        symbol,
        signal_type,
        score,
        score
    )

    text = formatter(
        signal
    )

    message_id = send_message(
        text
    )

    log_telegram_message(
        "signal",
        symbol,
        message_id,
        preview=text
    )

    save_active_signal(
        signal,
        message_id
    )


def job_market_scan():

    print(
        "[Job] شروع Toobit Market Scanner"
    )

    from market_scanner.signal_detector import (
        scan_for_signals
    )

    signals = scan_for_signals()

    for signal in signals:

        process_confluence_signal(
            signal,
            format_market_signal_v2
        )

    print(
        "[Job] پایان Market Scanner -",
        len(signals),
        "مورد"
    )


def job_futures_scan():

    print(
        "[Job] شروع Toobit Futures Scanner"
    )

    from futures.futures_scanner import (
        scan_futures
    )

    signals = scan_futures()

    for signal in signals:

        process_confluence_signal(
            signal,
            format_futures_signal
        )

    print(
        "[Job] پایان Futures Scanner -",
        len(signals),
        "مورد"
    )


def job_spot_scan():

    print(
        "[Job] شروع Toobit Spot Scanner"
    )

    from spot.spot_scanner import (
        scan_spot
    )

    signals = scan_spot()

    for signal in signals:

        process_confluence_signal(
            signal,
            format_spot_signal
        )

    print(
        "[Job] پایان Spot Scanner -",
        len(signals),
        "مورد"
    )


def job_send_performance_report():

    from scheduler.performance import (
        format_performance_report
    )

    text = format_performance_report(
        days=30
    )

    message_id = send_message(
        text
    )

    log_telegram_message(
        "performance_report",
        "ALL",
        message_id,
        preview=text
    )

    print(
        "[Job] گزارش عملکرد ارسال شد"
    )


def _calc_profit_pct(
    signal_type,
    entry,
    hit_price
):

    if not entry:

        return 0

    if signal_type == "LONG":

        return round(
            (
                hit_price - entry
            )
            /
            entry
            * 100,
            2
        )

    return round(
        (
            entry - hit_price
        )
        /
        entry
        * 100,
        2
    )


def job_monitor_active_signals():

    from futures.toobit import (
        get_current_price as get_futures_price
    )

    from spot.toobit import (
        get_current_price as get_spot_price
    )

    rows = db.fetch_active(
        "active_signals",
        status="active"
    )

    for row in rows:

        symbol = row.get(
            "symbol"
        )

        signal_type = row.get(
            "signal_type",
            "LONG"
        )

        entry = row.get(
            "entry_price",
            0
        )

        price = get_futures_price(
            symbol
        )

        if price is None:

            price = get_spot_price(
                symbol
            )

        if price is None:

            continue

        stop_loss = row.get(
            "stop_loss",
            0
        )

        stop_hit = (

            (
                signal_type == "LONG"
                and stop_loss
                and price <= stop_loss
            )

            or

            (
                signal_type == "SHORT"
                and stop_loss
                and price >= stop_loss
            )
        )

        if (
            stop_hit
            and not row.get(
                "hit_stop"
            )
        ):

            pct = _calc_profit_pct(
                signal_type,
                entry,
                price
            )

            text = (
                f"🛑 حد ضرر {symbol} فعال شد\n"
                f"نتیجه: {pct}%"
            )

            send_message(
                text,
                chat_id=row.get(
                    "telegram_chat_id"
                ),
                reply_to_message_id=row.get(
                    "telegram_message_id"
                )
            )

            db.update(
                "active_signals",
                row.get(
                    "id"
                ),
                {
                    "status":
                        "closed",

                    "hit_stop":
                        1,
                }
            )

            continue

        targets = [

            (
                "tp1",
                "hit_tp1",
                "🥇 TP1"
            ),

            (
                "tp2",
                "hit_tp2",
                "🥈 TP2"
            ),

            (
                "tp3",
                "hit_tp3",
                "🥉 TP3"
            ),

            (
                "tp4",
                "hit_tp4",
                "🏆 TP4"
            ),

        ]

        final_hit = False

        for tp_key, hit_key, label in targets:

            tp_value = row.get(
                tp_key,
                0
            )

            if (
                not tp_value
                or row.get(
                    hit_key
                )
            ):

                continue

            hit = (

                (
                    signal_type == "LONG"
                    and price >= tp_value
                )

                or

                (
                    signal_type == "SHORT"
                    and price <= tp_value
                )
            )

            if not hit:

                continue

            pct = _calc_profit_pct(
                signal_type,
                entry,
                price
            )

            text = (
                f"✅ {label} برای {symbol} خورد!\n"
                f"سود: {pct}%"
            )

            send_message(
                text,
                chat_id=row.get(
                    "telegram_chat_id"
                ),
                reply_to_message_id=row.get(
                    "telegram_message_id"
                )
            )

            db.update(
                "active_signals",
                row.get(
                    "id"
                ),
                {
                    hit_key:
                        1
                }
            )

            if tp_key == "tp4":

                final_hit = True

        if final_hit:

            db.update(
                "active_signals",
                row.get(
                    "id"
                ),
                {
                    "status":
                        "closed"
                }
            )
