import json
import os
from datetime import datetime


FILE_PATH = "database/signal_history.json"


def load_history():
    if not os.path.exists(FILE_PATH):
        return {}

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return {}



def save_history(history):

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )



def already_sent(symbol):

    history = load_history()

    return symbol in history



def mark_sent(symbol):

    history = load_history()

    history[symbol] = {
        "sent_at": datetime.utcnow().isoformat()
    }

    save_history(history)
