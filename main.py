import sys
from scheduler.jobs import job_dex_scan, job_intelligence_analysis, job_market_scan

DEFAULT_WATCHLIST = [
    {"coin_id": "ethereum", "symbol": "ETH", "market": "Toobit/Global"},
    {"coin_id": "solana", "symbol": "SOL", "market": "Toobit/Global"},
    {"coin_id": "arbitrum", "symbol": "ARB", "market": "Toobit/Global"},
]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "scan":
        job_dex_scan()
    elif mode == "analyze":
        job_intelligence_analysis(DEFAULT_WATCHLIST)
    elif mode == "all":
        job_dex_scan()
job_intelligence_analysis(DEFAULT_WATCHLIST)
job_market_scan()
    else:
        print(f"حالت ناشناخته: {mode}. از scan / analyze / all استفاده کنید.")
        sys.exit(1)


if __name__ == "__main__":
    main()
