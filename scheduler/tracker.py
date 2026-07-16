from database.db import db
from futures.toobit import get_current_price
from telegram_bot.bot import send_message


def check_active_signals():

    print("[Tracker] شروع بررسی معاملات فعال")


    try:
        signals = db.fetch_all(
            "active_signals",
            limit=200
        )

    except Exception as e:

        print(
            "[Tracker DB ERROR]",
            e
        )

        return



    for signal in signals:


        if signal.get("status") != "active":
            continue



        symbol = signal.get("token")


        current_price = get_current_price(symbol)


        if not current_price:
            continue



        entry = float(
            signal.get("entry_price", 0)
        )

        tp1 = float(
            signal.get("tp1", 0)
        )

        tp2 = float(
            signal.get("tp2", 0)
        )

        tp3 = float(
            signal.get("tp3", 0)
        )

        stop = float(
            signal.get("stop_loss", 0)
        )


        signal_type = signal.get(
            "signal_type",
            "LONG"
        )



        hit = None



        if signal_type == "LONG":

            if tp1 and current_price >= tp1:
                hit = "TP1"

            if tp2 and current_price >= tp2:
                hit = "TP2"

            if tp3 and current_price >= tp3:
                hit = "TP3"

            if stop and current_price <= stop:
                hit = "STOP LOSS"



        else:

            if tp1 and current_price <= tp1:
                hit = "TP1"

            if tp2 and current_price <= tp2:
                hit = "TP2"

            if tp3 and current_price <= tp3:
                hit = "TP3"

            if stop and current_price >= stop:
                hit = "STOP LOSS"



        if hit:


            message = (
                f"🚨 {hit}\n\n"
                f"ارز: {symbol}\n"
                f"قیمت فعلی: {current_price}\n"
            )


            send_message(message)



            print(
                f"[Tracker] {symbol} {hit}"
            )
