def clean_symbol(symbol: str) -> str:
    s = (symbol or "").replace(
        "-SWAP-",
        "-"
    ).strip("-")

    if "-" in s:
        return s.replace(
            "-",
            "/"
        )

    if s.endswith("USDT"):
        return s[:-4] + "/USDT"

    return s


def _fmt_price(value):

    if value in (
        None,
        "",
        "—"
    ):

        return "—"

    try:

        value = float(
            value
        )

        if value >= 1000:
            return f"{value:,.2f}"

        if value >= 1:
            return f"{value:,.4f}"

        if value >= 0.01:
            return f"{value:.6f}"

        return f"{value:.10f}".rstrip("0")

    except Exception:

        return str(value)


def _pct(entry, target, direction):

    try:

        entry = float(entry)
        target = float(target)

        if not entry:
            return 0

        if direction == "SHORT":

            return round(
                (
                    entry - target
                )
                / entry
                * 100,
                1
            )

        return round(
            (
                target - entry
            )
            / entry
            * 100,
            1
        )

    except Exception:

        return 0


def classify_trade_term(
    signal,
    entry,
    direction="LONG"
):
    """
    افق زمانی معامله را بر اساس فاصله دورترین هدف سود تا نقطه ورود
    تخمین می‌زند و یکی از سه برچسب زیر را برمی‌گرداند.
    """

    targets = _build_targets(
        signal,
        entry,
        direction
    )

    if not targets:
        return "🟩 کوتاه‌مدت"

    farthest = (
        targets.get("tp4")
        or targets.get("tp3")
        or targets.get("tp2")
        or targets.get("tp1")
    )

    pct = abs(
        _pct(
            entry,
            farthest,
            direction
        )
    )

    if pct >= 40:
        return "🟦 بلندمدت"

    if pct >= 15:
        return "🟨 میان‌مدت"

    return "🟩 کوتاه‌مدت"


def _build_targets(
    signal,
    entry=None,
    direction="LONG"
):

    levels = (
        signal.get(
            "trade_levels"
        )
        or {}
    )

    if entry is None:

        entry = (
            levels.get(
                "entry"
            )
            or
            signal.get(
                "current_price"
            )
            or
            signal.get(
                "price"
            )
        )

    if not entry:

        return {}

    targets = {}

    existing = [
        "tp1",
        "tp2",
        "tp3",
        "tp4",
    ]

    for key in existing:

        if levels.get(key):

            targets[key] = levels[key]

    if len(targets) >= 4:

        return targets

    atr = (
        signal.get(
            "atr"
        )
        or
        (
            signal.get(
                "indicators"
            )
            or {}
        ).get(
            "atr"
        )
    )

    try:

        entry = float(
            entry
        )

        if atr:

            atr = float(
                atr
            )

            distances = [
                1.5,
                2.5,
                4.0,
                6.0,
            ]

            for index, distance in enumerate(
                distances,
                start=1
            ):

                key = f"tp{index}"

                if key in targets:
                    continue

                if direction == "SHORT":

                    targets[key] = (
                        entry
                        - atr
                        * distance
                    )

                else:

                    targets[key] = (
                        entry
                        + atr
                        * distance
                    )

        else:

            percentages = [
                5,
                10,
                20,
                35,
            ]

            for index, percentage in enumerate(
                percentages,
                start=1
            ):

                key = f"tp{index}"

                if key in targets:
                    continue

                if direction == "SHORT":

                    targets[key] = (
                        entry
                        * (
                            1
                            - percentage
                            / 100
                        )
                    )

                else:

                    targets[key] = (
                        entry
                        * (
                            1
                            + percentage
                            / 100
                        )
                    )

    except Exception:

        return targets

    return targets


def _build_alert_trade_plan(
    signal
):

    direction = (
        signal.get(
            "direction"
        )
        or
        signal.get(
            "type"
        )
        or
        "LONG"
    ).upper()

    entry = (
        signal.get(
            "current_price"
        )
        or
        signal.get(
            "price"
        )
    )

    levels = (
        signal.get(
            "trade_levels"
        )
        or {}
    )

    if levels.get(
        "entry"
    ):

        entry = levels.get(
            "entry"
        )

    targets = _build_targets(
        signal,
        entry,
        direction
    )

    stop = (
        levels.get(
            "stop_loss"
        )
    )

    try:

        entry_float = float(
            entry
        )

        if not stop:

            if direction == "SHORT":

                stop = (
                    entry_float
                    * 1.06
                )

            else:

                stop = (
                    entry_float
                    * 0.94
                )

    except Exception:

        stop = None

    return (
        direction,
        entry,
        targets,
        stop
    )


def _format_trade_plan(
    signal
):

    direction, entry, targets, stop = (
        _build_alert_trade_plan(
            signal
        )
    )

    if not entry:

        return ""

    direction_text = (
        "🟢 سناریوی صعودی"
        if direction == "LONG"
        else
        "🔴 سناریوی نزولی"
    )

    lines = [
        "",
        "━━━━━━━━━━━━━━",
        direction_text,
        "",
        "💰 نقطه فعال‌شدن سناریو",
        f"{_fmt_price(entry)}",
    ]

    icons = [
        "🥇",
        "🥈",
        "🥉",
        "🏆",
    ]

    target_lines = []

    for index, icon in enumerate(
        icons,
        start=1
    ):

        key = f"tp{index}"

        if key not in targets:

            continue

        target = targets[key]

        profit = _pct(
            entry,
            target,
            direction
        )

        target_lines.append(
            f"{icon} {key.upper()}: "
            f"{_fmt_price(target)} "
            f"(+{profit}%)"
        )

    if target_lines:

        lines.append("")
        lines.append("🎯 اهداف احتمالی حرکت")
        lines.extend(target_lines)

    if stop:

        lines.extend(
            [
                "",
                "🛑 سطح بی‌اعتبار شدن سناریو",
                _fmt_price(stop),
            ]
        )

    return "\n".join(
        lines
    )


def suggest_leverage(
    score: int,
    risks: list
) -> str:

    if risks:
        return "2x"

    if score >= 90:
        return "5x"

    if score >= 80:
        return "3x"

    return "2x"


def build_badges(
    signal: dict
) -> str:

    badges = []

    status_label = signal.get(
        "status_label",
        ""
    )

    if status_label:

        badges.append(
            status_label.split(
                " "
            )[0]
        )

    if signal.get(
        "smart_money_alert"
    ):

        badges.append(
            "🐋"
        )

    if signal.get(
        "score",
        0
    ) >= 90:

        badges.append(
            "⭐"
        )

    return "".join(
        badges[:4]
    )


def build_short_reason(
    signal: dict
) -> str:

    parts = []

    structure_signal = signal.get(
        "structure_signal"
    )

    if structure_signal == "BREAKOUT_HIGH":

        parts.append(
            "شکست سقف"
        )

    elif structure_signal == "BOTTOM_REVERSAL":

        parts.append(
            "بازگشت از کف"
        )

    elif structure_signal in (
        "TREND_FLIP_LONG",
        "TREND_FLIP_SHORT"
    ):

        parts.append(
            "تغییر روند"
        )

    if signal.get(
        "smart_money_alert"
    ):

        parts.append(
            "پول هوشمند"
        )

    if signal.get(
        "volume",
        0
    ) >= 5_000_000:

        parts.append(
            "حجم سنگین"
        )

    return " + ".join(
        parts[:3]
    ) or "تأیید چندگانه بازار"


def format_dex_discovery(
    discovery: dict
) -> str:

    record = discovery[
        "record"
    ]

    symbol = clean_symbol(
        record.token
    )

    return (
        f"🚨 کشف جدید DEX\n\n"
        f"🪙 {symbol}\n"
        f"🌐 شبکه: {record.network}\n\n"
        f"💧 نقدینگی: "
        f"${record.liquidity:,.0f}\n"
        f"📊 حجم: "
        f"${record.volume:,.0f}\n\n"
        f"🛡 امنیت: "
        f"{record.security_score}/100\n"
        f"⭐ امتیاز: "
        f"{record.dex_score}/100"
    )


def format_crypto_report(
    report: dict
) -> str:

    symbol = clean_symbol(
        report.get(
            "token",
            ""
        )
    )

    return (
        f"🧠 گزارش تحلیل پروژه\n\n"
        f"🪙 {symbol}\n"
        f"🌐 بازار: "
        f"{report.get('market', 'نامشخص')}\n\n"
        f"⭐ امتیاز نهایی: "
        f"{report.get('total_score', 0)}/100\n"
        f"📌 وضعیت: "
        f"{report.get('status', 'نامشخص')}"
    )


def _format_scanner_signal(
    signal: dict,
    title: str,
    is_futures: bool = False
) -> str:

    symbol = clean_symbol(
        signal.get(
            "symbol",
            ""
        )
    )

    signal_type = (
        signal.get(
            "direction"
        )
        or
        signal.get(
            "type"
        )
        or
        ""
    ).upper()

    if signal_type == "LONG":

        direction = (
            "🟢 LONG | سناریوی صعودی"
        )

    elif signal_type == "SHORT":

        direction = (
            "🔴 SHORT | سناریوی نزولی"
        )

    else:

        direction = (
            "⚪ "
            + signal_type
        )

    levels = (
        signal.get(
            "trade_levels"
        )
        or {}
    )

    entry = (
        levels.get(
            "entry"
        )
        or
        signal.get(
            "price"
        )
        or
        "—"
    )

    score = min(
        signal.get(
            "score",
            0
        ),
        100
    )

    reasons = (
        signal.get(
            "reasons"
        )
        or []
    )

    risks = (
        signal.get(
            "risks"
        )
        or []
    )

    reason_text = "\n".join(
        f"✅ {r}"
        for r in reasons[:5]
    )

    if not reason_text:

        reason_text = (
            "✅ تأیید چندگانه تکنیکال\n"
            "✅ بررسی روند و حجم\n"
            "✅ بررسی ساختار بازار"
        )

    risk_block = ""

    if risks:

        risk_block = (
            "\n\n⚠️ ریسک‌های شناسایی‌شده\n\n"
            +
            "\n".join(
                f"⚠️ {r}"
                for r in risks[:3]
            )
        )

    term_label = classify_trade_term(
        signal,
        entry,
        signal_type
    )

    leverage_line = ""

    if is_futures:

        leverage = suggest_leverage(
            score,
            risks
        )

        leverage_line = (
            "\n\n⚡ اهرم پیشنهادی\n"
            f"{leverage}"
        )

    targets = _build_targets(
        signal,
        entry,
        signal_type
    )

    target_lines = []

    icons = [
        "🥇",
        "🥈",
        "🥉",
        "🏆",
    ]

    for index, icon in enumerate(
        icons,
        start=1
    ):

        key = f"tp{index}"

        if key not in targets:

            continue

        target = targets[key]

        profit = _pct(
            entry,
            target,
            signal_type
        )

        target_lines.append(
            f"{icon} {key.upper()}: "
            f"{_fmt_price(target)} "
            f"(+{profit}%)"
        )

    stop = levels.get(
        "stop_loss"
    )

    if not stop:

        try:

            entry_float = float(
                entry
            )

            stop = (
                entry_float * 0.94
                if signal_type == "LONG"
                else
                entry_float * 1.06
            )

        except Exception:

            stop = "—"

    return f"""
🚨 {title.upper()} SIGNAL

🪙 {symbol}

{direction}

⏳ افق معامله: {term_label}

━━━━━━━━━━━━━━

💰 نقطه ورود
{_fmt_price(entry)}

🎯 اهداف سود

{chr(10).join(target_lines)}

🛑 حد ضرر
{_fmt_price(stop)}
{leverage_line}

━━━━━━━━━━━━━━

⭐ امتیاز اطمینان
{score}/100

🧠 دلایل تأیید

{reason_text}
{risk_block}

⚠️ سیگنال بر اساس تأیید چندگانه صادر شده است.
مدیریت سرمایه الزامی است.
"""


def format_futures_top_picks(
    top_signals
):

    if not top_signals:
        return ""

    lines = [
        "🏆 برترین موقعیت‌های فیوچرز (کوتاه‌مدت)",
        "━━━━━━━━━━━━━━",
        ""
    ]

    for index, signal in enumerate(
        top_signals,
        start=1
    ):

        symbol = clean_symbol(
            signal.get("symbol", "")
        )

        direction = (
            signal.get("direction")
            or signal.get("type")
            or "LONG"
        ).upper()

        emoji = (
            "🟢" if direction == "LONG"
            else "🔴"
        )

        score = min(
            signal.get("score", 0),
            100
        )

        risks = (
            signal.get("risks") or []
        )

        leverage = suggest_leverage(
            score,
            risks
        )

        levels = (
            signal.get("trade_levels")
            or {}
        )

        entry = (
            levels.get("entry")
            or signal.get("price")
            or "—"
        )

        targets = _build_targets(
            signal,
            entry,
            direction
        )

        tp1 = targets.get("tp1")

        profit = (
            _pct(entry, tp1, direction)
            if tp1 else 0
        )

        lines.append(
            f"{index}. {emoji} {symbol} | "
            f"امتیاز {score}/100 | "
            f"اهرم {leverage} | "
            f"ورود {_fmt_price(entry)} | "
            f"TP1 (+{profit}%)"
        )

    lines.append("")
    lines.append(
        "⚠️ این دایجست صرفاً یک خلاصه سریع است؛ "
        "برای جزئیات کامل هر معامله به پیام سیگنال اصلی آن مراجعه کنید."
    )

    return "\n".join(lines)


def format_futures_signal(
    signal: dict
) -> str:

    return _format_scanner_signal(
        signal,
        "Futures",
        True
    )


def format_spot_signal(
    signal: dict
) -> str:

    return _format_scanner_signal(
        signal,
        "Spot",
        False
    )


def format_market_signal_v2(
    signal: dict
) -> str:

    return _format_scanner_signal(
        signal,
        "Market",
        False
    )


def format_catalyst_alert(
    signal: dict
) -> str:

    symbol = clean_symbol(
        signal.get(
            "symbol",
            ""
        )
    )

    c = (
        signal.get(
            "catalyst_breakout"
        )
        or {}
    )

    current_price = (
        signal.get(
            "current_price"
        )
        or
        signal.get(
            "price"
        )
        or
        "—"
    )

    reasons_text = "\n".join(
        f"✅ {r}"
        for r in c.get(
            "reasons",
            []
        )
    )

    if not reasons_text:

        reasons_text = (
            "تأیید ساختار جهش کاتالیزوری"
        )

    trade_plan = _format_trade_plan(
        signal
    )

    return f"""
🚨🚨 حرکت کاتالیزوری تأیید شد

🪙 {symbol}

🔥 یک حرکت غیرعادی در حال شکل‌گیری است

━━━━━━━━━━━━━━

💰 قیمت فعلی
{_fmt_price(current_price)}

📊 حجم
{c.get('volume_ratio', '—')}× میانگین ۲۰ روزه

📈 رشد ۳ روزه
{c.get('change_3d', '—')}٪

🧠 تأییدیه‌ها
{reasons_text}

🎯 سناریوی احتمالی حرکت
{trade_plan}

⚠️ هشدار:
این پیام فقط زمانی صادر می‌شود که الگوی حرکت
به حداقل تأییدهای لازم رسیده باشد.
"""


def format_trendline_alert(
    signal: dict
) -> str:

    symbol = clean_symbol(
        signal.get(
            "symbol",
            ""
        )
    )

    t = (
        signal.get(
            "trendline_break"
        )
        or
        {}
    )

    direction = t.get(
        "trend_direction"
    )

    if direction == "DOWN":

        title = (
            "🚀 شکست صعودی روند بلندمدت"
        )

    else:

        title = (
            "🔻 شکست نزولی روند بلندمدت"
        )

    trade_plan = _format_trade_plan(
        signal
    )

    return f"""
🚨 تأیید شکست ساختار بلندمدت

🪙 {symbol}

{title}

━━━━━━━━━━━━━━

💰 قیمت فعلی
{_fmt_price(signal.get('current_price'))}

📏 سطح تأیید ۹۰ روزه
{_fmt_price(t.get('trend_value_90d'))}

📏 سطح تأیید ۱۸۰ روزه
{_fmt_price(t.get('trend_value_180d'))}

🎯 در صورت ادامه حرکت
{trade_plan}

⚠️ این پیام فقط پس از تأیید شکست
در هر دو بازه زمانی صادر می‌شود.
"""


def format_coiling_alert(
    signal: dict
) -> str:

    symbol = clean_symbol(
        signal.get(
            "symbol",
            ""
        )
    )

    coiling = (
        signal.get(
            "coiling_setup"
        )
        or
        {}
    )

    reasons = coiling.get(
        "reasons",
        []
    )

    reasons_text = "\n".join(
        f"✅ {reason}"
        for reason in reasons
    )

    if not reasons_text:

        reasons_text = (
            "تأیید چندگانه فشردگی و آماده‌سازی حرکت"
        )

    trade_plan = _format_trade_plan(
        signal
    )

    return f"""
⚡⚡ PRE-BREAKOUT CONFIRMED

🪙 {symbol}

🔥 بازار در حال فشرده‌شدن
و به نقطه تصمیم نزدیک شده است

━━━━━━━━━━━━━━

⭐ امتیاز فشردگی
{coiling.get('score', '—')}/100

📉 فشردگی نوسان
{"✅" if coiling.get("volatility_compression") else "❌"}

🔻 Bollinger Squeeze
{"✅" if coiling.get("bollinger_squeeze") else "❌"}

📈 انباشت حجم
{"✅" if coiling.get("volume_accumulation") else "❌"}

🐋 OBV
{"✅" if coiling.get("obv_rising") else "❌"}

📏 فاصله تا مقاومت
{coiling.get('resistance_distance', '—')}٪

🧠 تأییدیه‌ها

{reasons_text}

🎯 سناریوی حرکت در صورت شکست
{trade_plan}

⚠️ این هشدار فقط برای ساختارهایی است
که تأییدیه‌های لازم را گرفته‌اند
و هنوز حرکت اصلی را کامل انجام نداده‌اند.
"""
    METAL_LABELS = {
    "GOLD": "🥇 طلا (Gold)",
    "SILVER": "🥈 نقره (Silver)",
    "COPPER": "🟤 مس (Copper)",
}


def format_metal_report(
    signal: dict
) -> str:

    metal = signal.get(
        "symbol",
        ""
    )

    label = METAL_LABELS.get(
        metal,
        metal
    )

    direction = signal.get(
        "direction",
        "LONG"
    )

    direction_text = (
        "🟢 چشم‌انداز صعودی"
        if direction == "LONG"
        else
        "🔴 چشم‌انداز نزولی"
    )

    score = signal.get(
        "score",
        0
    )

    decision = signal.get(
        "decision",
        "REJECT"
    )

    decision_text = (
        "✅ تأیید چندگانه (SIGNAL)"
        if decision == "SIGNAL"
        else
        "⚪ در حد نظارت (بدون تأیید کامل)"
    )

    reasons = (
        signal.get(
            "reasons"
        )
        or []
    )

    reasons_text = "\n".join(
        f"✅ {r}"
        for r in reasons[:6]
    )

    if not reasons_text:

        reasons_text = (
            "تحلیل بر اساس اندیکاتورها و ساختار قیمت"
        )

    trade_plan = _format_trade_plan(
        signal
    )

    return f"""
📊 تحلیل روزانه {label}

{direction_text}

━━━━━━━━━━━━━━

💰 قیمت فعلی
{_fmt_price(signal.get('current_price'))}

⭐ امتیاز اطمینان
{score}/100

📌 وضعیت
{decision_text}

🧠 دلایل تحلیل
{reasons_text}

🎯 سناریوی محتمل
{trade_plan}

⚠️ این گزارش روزانه است، نه سیگنال قطعی معامله.
مدیریت سرمایه با خودتان است.
"""
METAL_LABELS = {
    "GOLD": "🥇 طلا (Gold)",
    "SILVER": "🥈 نقره (Silver)",
    "COPPER": "🟤 مس (Copper)",
}


def format_metal_report(
    signal: dict
) -> str:

    metal = signal.get(
        "symbol",
        ""
    )

    label = METAL_LABELS.get(
        metal,
        metal
    )

    direction = signal.get(
        "direction",
        "LONG"
    )

    direction_text = (
        "🟢 چشم‌انداز صعودی"
        if direction == "LONG"
        else
        "🔴 چشم‌انداز نزولی"
    )

    score = signal.get(
        "score",
        0
    )

    decision = signal.get(
        "decision",
        "REJECT"
    )

    decision_text = (
        "✅ تأیید چندگانه (SIGNAL)"
        if decision == "SIGNAL"
        else
        "⚪ در حد نظارت (بدون تأیید کامل)"
    )

    reasons = (
        signal.get(
            "reasons"
        )
        or []
    )

    reasons_text = "\n".join(
        f"✅ {r}"
        for r in reasons[:6]
    )

    if not reasons_text:

        reasons_text = (
            "تحلیل بر اساس اندیکاتورها و ساختار قیمت"
        )

    trade_plan = _format_trade_plan(
        signal
    )

    return f"""
📊 تحلیل روزانه {label}

{direction_text}

━━━━━━━━━━━━━━

💰 قیمت فعلی
{_fmt_price(signal.get('current_price'))}

⭐ امتیاز اطمینان
{score}/100

📌 وضعیت
{decision_text}

🧠 دلایل تحلیل
{reasons_text}

🎯 سناریوی محتمل
{trade_plan}

⚠️ این گزارش روزانه است، نه سیگنال قطعی معامله.
مدیریت سرمایه با خودتان است.
"""
