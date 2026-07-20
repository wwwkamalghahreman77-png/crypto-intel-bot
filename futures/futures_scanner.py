"""
futures/futures_scanner.py

اسکنر فیوچرز.

SIGNAL / REJECT از کانفلوئنس.

Coiling مستقل از SIGNAL / REJECT است.
"""

from futures.toobit import (
    get_futures_opportunities,
    get_klines,
)

from futures.derivatives import (
    analyze_derivatives,
)

from analysis.confluence import (
    run_confluence_analysis,
)


STATUS_LABELS = {

    "BOS_BULLISH":
        "📈 BOS - ادامه روند صعودی",

    "BOS_BEARISH":
        "📉 BOS - ادامه روند نزولی",

    "CHOCH_BULLISH":
        "🔄 CHOCH - برگشت احتمالی به صعودی",

    "CHOCH_BEARISH":
        "🔄 CHOCH - برگشت احتمالی به نزولی",

    None:
        "🔥 سیگنال کانفلوئنس",
}


def _prefilter(
    signals,
    min_change=3,
    min_volume=200_000
):

    shortlist = []

    for signal in signals:

        change = abs(
            signal.get(
                "change",
                0
            )
        )

        volume = signal.get(
            "volume",
            0
        )

        if (
            change < min_change
            or volume < min_volume
        ):
            continue

        shortlist.append(
            signal
        )

    shortlist.sort(
        key=lambda s:
        abs(
            s.get(
                "change",
                0
            )
        )
        *
        (
            s.get(
                "volume",
                0
            )
            ** 0.1
        ),

        reverse=True
    )

    return shortlist[:40]


def scan_futures(
    max_results=15
):

    signals = (
        get_futures_opportunities()
    )

    shortlist = _prefilter(
        signals
    )

    print(
        f"[FuturesScanner] "
        f"{len(shortlist)} کاندید اولیه پس از پیش‌فیلتر"
    )

    results = []

    all_scores = []

    for signal in shortlist:

        symbol = signal[
            "symbol"
        ]

        direction = signal.get(
            "type",
            "LONG"
        )

        analysis = (
            run_confluence_analysis(
                symbol,
                get_klines,
                signal_meta=signal,
                direction=direction,
                extra_analyzer=analyze_derivatives,
                min_signal_score=55,
            )
        )

        if analysis is None:
            continue

        all_scores.append(
            analysis[
                "score"
            ]
        )

        coiling_hit = (
            analysis
            .get(
                "coiling_setup",
                {}
            )
            .get(
                "match",
                False
            )
        )

        catalyst_hit = (
            analysis
            .get(
                "catalyst_breakout",
                {}
            )
            .get(
                "match",
                False
            )
        )

        trendline_hit = (
            analysis
            .get(
                "trendline_break",
                {}
            )
            .get(
                "break_confirmed",
                False
            )
        )

        if (
            analysis["decision"]
            == "REJECT"
            and not coiling_hit
            and not catalyst_hit
            and not trendline_hit
        ):
            continue

        signal.update(
            analysis
        )

        signal[
            "status_label"
        ] = STATUS_LABELS.get(
            analysis.get(
                "structure_signal"
            ),
            STATUS_LABELS[None]
        )

        results.append(
            signal
        )

    results.sort(
        key=lambda s:
        s.get(
            "score",
            0
        ),
        reverse=True
    )

    if all_scores:

        print(
            f"[FuturesScanner] امتیازها: "
            f"max={max(all_scores)} "
            f"avg={round(sum(all_scores) / len(all_scores), 1)} "
            f"(n={len(all_scores)})"
        )

    signal_count = sum(
        1
        for r in results
        if r.get(
            "decision"
        )
        == "SIGNAL"
    )

    coiling_count = sum(
        1
        for r in results
        if r.get(
            "coiling_setup",
            {}
        ).get(
            "match",
            False
        )
    )

    print(
        f"[FuturesScanner] "
        f"{signal_count} سیگنال نهایی / "
        f"{coiling_count} Pre-Breakout"
    )

    return results[
        :max_results
    ]
