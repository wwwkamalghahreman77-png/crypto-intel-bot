import requests

from config.settings import settings


TELEGRAM_API = (
    f"https://api.telegram.org/bot"
    f"{settings.telegram_bot_token}"
)


def get_primary_chat_id():
    channel_id = getattr(settings, "telegram_channel_id", None)
    if channel_id:
        return str(channel_id)

    private_chat_id = getattr(settings, "telegram_chat_id", None)
    if private_chat_id:
        return str(private_chat_id)

    return None


def send_message(text, chat_id=None, reply_to_message_id=None):
    targets = []

    if chat_id:
        targets.append(str(chat_id))
    else:
        private_chat_id = getattr(settings, "telegram_chat_id", None)
        if private_chat_id:
            targets.append(str(private_chat_id))

        channel_id = getattr(settings, "telegram_channel_id", None)
        if channel_id:
            channel_id = str(channel_id)
            if channel_id not in targets:
                targets.append(channel_id)

    if not targets:
        print("[Telegram] هیچ مقصدی برای ارسال پیام تنظیم نشده است")
        return None

    results = {}

    for target in targets:
        payload = {
            "chat_id": target,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        if chat_id and reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            response = requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json=payload,
                timeout=20
            )
            data = response.json()

            if not data.get("ok"):
                print("[Telegram Error]", target, data)
                continue

            message_id = data.get("result", {}).get("message_id")
            if message_id:
                results[target] = message_id

            print(f"[Telegram] پیام ارسال شد به {target}")

        except Exception as e:
            print("[Telegram Exception]", target, e)

    if not results:
        return None

    if chat_id:
        return results.get(str(chat_id))

    primary = get_primary_chat_id()
    if primary and primary in results:
        return results[primary]

    return list(results.values())[-1]
