import sys

from scheduler.jobs import (
    job_market_scan,
    job_futures_scan,
    job_spot_scan,
    job_monitor_active_signals,
    job_send_performance_report,
)


def run_scans():
    job_market_scan()
    job_futures_scan()
    job_spot_scan()


def main():

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "all":

        job_monitor_active_signals()
        run_scans()

    elif mode == "market":

        job_market_scan()

    elif mode == "futures":

        job_futures_scan()

    elif mode == "spot":

        job_spot_scan()

    elif mode == "monitor":

        job_monitor_active_signals()

    elif mode == "performance":

        job_send_performance_report()

    else:

        print(
            "حالت ناشناخته"
        )


if __name__ == "__main__":

    main()
