def send_message(text: str, chat_id: str = None, reply_to_message_id: int = None):
    """ارسال پیام تلگرام و برگشت message_id برای Reply خودکار."""

    if not settings.telegram_enabled:
        print("[Telegram] تنظیمات کامل نیست:")
        print(text)
        return None

    url = API_URL.format(
        token=settings.telegram_bot_token,
        method="sendMessage"
    )

    payload = {
        "chat_id": chat_id or settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("ok"):
            message_id = data["result"]["message_id"]
            print("[Telegram] Message ID:", message_id)
            return message_id

        print("[Telegram] پاسخ نامعتبر:", data)
        return None

    except requests.RequestException as e:
        print(f"[Telegram] خطا در ارسال پیام: {e}")
        return None
