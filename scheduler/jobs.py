باشه. فقط فایل بعدی که واقعاً باید تغییر کند:

# scheduler/jobs.py

from dex.gem_scanner import run_full_scan

from telegram_bot.bot import send_message

from telegram_bot.formatters import (
    format_dex_discovery,
    format_market_signal_v2,
    format_futures_signal,
    format_spot_signal,
    format_catalyst_alert,
    format_trendline_alert,
    format_coiling_alert,
)

from analysis.technical import (
    analyze_technical
)

from analysis.fundamental import (
    analyze_fundamental
)

from analysis.scoring import (
    calculate_total_score,
    classify_status
)

from news.news_fetcher import (
    analyze_news_for_token,
    fetch_all_news
)

from config.settings import settings

from database.db import (
    db,
    now_str
)

from database.models import (
    CryptoReport
)

from database.signal_history import (
    already_sent,
    mark_sent
)


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
        or {}
    )

    data = {

        "symbol":
            signal.get(
                "symbol"
            ),

        "signal_type":
            signal.get(
                "type",
                signal.get(
                    "direction",
                    "LONG"
                )
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

        "hit_tp1": 0,
        "hit_tp2": 0,
        "hit_tp3": 0,
        "hit_tp4": 0,
        "hit_stop": 0,

        "date_found":
            now_str()
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
            "[TelegramMessages] "
            "خطا در ثبت پیام:",
            e
        )


def check_catalyst_and_trendline_alerts(
    signal
):

    symbol = signal.get(
        "symbol"
    )

    catalyst = (
        signal.get(
            "catalyst_breakout"
        )
        or {}
    )

    if catalyst.get(
        "match"
    ):

        if not already_sent(
            symbol,
            "CATALYST_BREAKOUT",
            0,
            0
        ):

            mark_sent(
                symbol,
                "CATALYST_BREAKOUT",
                0,
                0
            )

            text = format_catalyst_alert(
                signal
            )

            message_id = send_message(
                text
            )

            log_telegram_message(
                "catalyst_breakout",
                symbol,
                message_id,
                preview=text
            )

    trendline = (
        signal.get(
            "trendline_break"
        )
        or {}
    )

    if trendline.get(
        "break_confirmed"
    ):

        if not already_sent(
            symbol,
            "TRENDLINE_BREAK",
            0,
            0
        ):

            mark_sent(
                symbol,
                "TRENDLINE_BREAK",
                0,
                0
            )

            text = format_trendline_alert(
                signal
            )

            message_id = send_message(
                text
            )

            log_telegram_message(
                "trendline_break",
                symbol,
                message_id,
                preview=text
            )

    coiling = (
        signal.get(
            "coiling_setup"
        )
        or {}
    )

    if coiling.get(
        "match"
    ):

        if not already_sent(
            symbol,
            "PRE_BREAKOUT_COILING",
            0,
            0
        ):

            mark_sent(
                symbol,
                "PRE_BREAKOUT_COILING",
                0,
                0
            )

            text = format_coiling_alert(
                signal
            )

            message_id = send_message(
                text
            )

            log_telegram_message(
                "pre_breakout_coiling",
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

    decision = signal.get(
        "decision"
    )

    check_catalyst_and_trendline_alerts(
        signal
    )

    if decision != "SIGNAL":
        return

    if active_signal_exists(
        symbol
    ):

        return

    signal_type = (
        signal.get(
            "structure_signal"
        )
        or signal.get(
            "direction"
        )
        or "UNKNOWN"
    )

    score = signal.get(
        "score",
        0
    )

    if score < MIN_SIGNAL_SCORE:

        return

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
        {
            **signal,
            "type":
                signal.get(
                    "direction",
                    "LONG"
                )
        },
        message_id
    )


def job_market_scan():

    print(
        "[Job] شروع Market Scanner"
    )

    from market_scanner.signal_detector import (
        scan_for_signals
    )

    signals = scan_for_signals()

    for signal in signals:

        if "decision" in signal:

            process_confluence_signal(
                signal,
                format_market_signal_v2
            )

            continue

        if signal.get(
            "score",
            0
        ) < MIN_SIGNAL_SCORE:

            continue

        symbol = signal.get(
            "symbol"
        )

        if active_signal_exists(
            symbol
        ):

            continue

        message_text = format_market_signal_v2(
            signal
        )

        message_id = send_message(
            message_text
        )

        log_telegram_message(
            "signal",
            symbol,
            message_id,
            preview=message_text
        )

        save_active_signal(
            signal,
            message_id
        )

    print(
        f"[Job] پایان Market Scanner - "
        f"{len(signals)} مورد"
    )


def job_futures_scan():

    print(
        "[Job] شروع Futures Scanner"
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
        f"[Job] پایان Futures Scanner - "
        f"{len(signals)} مورد"
    )


def job_spot_scan():

    print(
        "[Job] شروع Spot Scanner"
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
        f"[Job] پایان Spot Scanner - "
        f"{len(signals)} مورد"
    )
