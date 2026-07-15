import sys
from scheduler.jobs import job_market_scan


def main():

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"


    if mode == "all":
        job_market_scan()

    elif mode == "scan":
        job_market_scan()

    else:
        print(
            f"حالت ناشناخته: {mode}"
        )
        sys.exit(1)



if __name__ == "__main__":
    main()
