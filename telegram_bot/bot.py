"""
telegram_bot/bot.py

ربات تلگرام شامل:
    - تابع ارسال پیام ساده (استفاده در اسکریپت‌های GitHub Actions / زمان‌بند)
    - دستورات تعاملی: /scan /top /watchlist /report /stats
      (این دستورات برای زمانی است که ربات به‌صورت مداوم اجرا می‌شود -
       در حالت GitHub Actions فقط از send_message برای گزارش‌های خودکار استفاده می‌شود)
"""

import requests
from config.settings import settings
from database.db import db

API_URL = "https://api.telegram.org/bot{token}/{method}"


def send_message(text: str, chat_id: str = None):
    """ارسال یک پیام متنی ساده به کانال/چت تلگرام (روش سبک، بدون نیاز به کتابخانه اضافه)."""
    if not settings.telegram_enabled:
        print("[Telegram] توکن یا chat_id تنظیم نشده - پیام فقط در کنسول چاپ می‌شود:")
        print(text)
        return

    url = API_URL.format(token=settings.telegram_bot_token, method="sendMessage")
    payload = {
        "chat_id": chat_id or settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Telegram] خطا در ارسال پیام: {e}")


# ------------------------------------------------------------------
# دستورات تعاملی ربات (نیازمند اجرای مداوم ربات - نه در GitHub Actions)
# برای اجرای این بخش، پروژه را روی یک سرویس رایگان دائمی مثل Railway/Render
# اجرا کنید (توضیحات در README).
# ------------------------------------------------------------------

def build_application():
    """
    ساخت اپلیکیشن python-telegram-bot با دستورات تعریف‌شده.
    این تابع فقط زمانی استفاده می‌شود که بخواهید ربات را به‌صورت polling اجرا کنید
    (مثلاً روی یک سرویس رایگان که امکان اجرای دائمی دارد).
    """
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

    async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ در حال اجرای اسکن... این ممکن است کمی طول بکشد.")
        from dex.gem_scanner import run_full_scan
        from telegram_bot.formatters import format_dex_discovery

        discoveries = run_full_scan()
        if not discoveries:
            await update.message.reply_text("موردی برای گزارش یافت نشد.")
            return
        for d in discoveries:
            await update.message.reply_text(format_dex_discovery(d))

    async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
        rows = db.fetch_all("crypto_reports", limit=5)
        rows = sorted(rows, key=lambda r: r.get("total_score", 0), reverse=True)
        if not rows:
            await update.message.reply_text("هنوز گزارشی ثبت نشده است.")
            return
        text = "\n\n".join([f"{r['token']} — امتیاز: {r['total_score']} — وضعیت: {r['status']}" for r in rows])
        await update.message.reply_text(f"🏆 برترین پروژه‌ها:\n\n{text}")

    async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
        rows = db.fetch_all("crypto_reports", limit=50)
        watch_rows = [r for r in rows if r.get("status") == "WATCHLIST"]
        if not watch_rows:
            await update.message.reply_text("واچ‌لیست خالی است.")
            return
        text = "\n".join([f"- {r['token']} ({r['total_score']})" for r in watch_rows])
        await update.message.reply_text(f"👀 واچ‌لیست:\n{text}")

    async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("استفاده صحیح: /report SYMBOL   مثال: /report ETH")
            return
        token = context.args[0].upper()
        rows = db.fetch_by_token("crypto_reports", token)
        if not rows:
            await update.message.reply_text(f"گزارشی برای {token} یافت نشد.")
            return
        r = rows[0]
        await update.message.reply_text(
            f"📄 گزارش {token}\nامتیاز کل: {r['total_score']}\nوضعیت: {r['status']}"
        )

    async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        dex_rows = db.fetch_all("dex_discoveries", limit=1000)
        report_rows = db.fetch_all("crypto_reports", limit=1000)
        await update.message.reply_text(
            f"📊 آمار کلی ربات\n\nتوکن‌های کشف‌شده (DEX): {len(dex_rows)}\nگزارش‌های تحلیلی: {len(report_rows)}"
        )

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("stats", cmd_stats))
    return app


def run_polling_bot():
    """اجرای ربات در حالت polling (برای اجرای دائمی روی یک سرویس رایگان)."""
    app = build_application()
    print("[Telegram] ربات در حال اجراست (polling)...")
    app.run_polling()
