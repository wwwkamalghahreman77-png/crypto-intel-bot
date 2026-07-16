import sys
import time

from scheduler.jobs import (
    job_market_scan,
    job_futures_scan,
    job_spot_scan,
    job_monitor_active_signals,
)

SCAN_INTERVAL_SECONDS = 900      # هر ۱۵ دقیقه اسکن کامل بازار
MONITOR_INTERVAL_SECONDS = 20    # هر ۲۰ ثانیه چک کردن TP/SL


def run_scans():
    job_market_scan()
    job_futures_scan()
    job_spot_scan()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"

    if mode == "loop":

        print("[Main] اجرای دائمی شروع شد")

        last_scan_time = 0

        while True:

            now = time.time()

            try:
                job_monitor_active_signals()
            except Exception as e:
                print("[Main] خطا در مانیتورینگ:", e)

            if now - last_scan_time >= SCAN_INTERVAL_SECONDS:

                try:
                    run_scans()
                except Exception as e:
                    print("[Main] خطا در اسکن:", e)

                last_scan_time = now

            time.sleep(MONITOR_INTERVAL_SECONDS)

    elif mode == "all":
        run_scans()

    elif mode == "market":
        job_market_scan()

    elif mode == "futures":
        job_futures_scan()

    elif mode == "spot":
        job_spot_scan()

    elif mode == "monitor":
        job_monitor_active_signals()

    else:
        print("حالت ناشناخته")


if __name__ == "__main__":
    main()
