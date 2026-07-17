# تغییرات این آپدیت (Confluence + SMC + واچ‌لیست + دیتابیس + پرفورمنس)

هیچ فایل قدیمی حذف نشد؛ همه چیز جایگزین (Additive) اضافه یا بهبود داده شده.

## ۱) فایل‌های جدید

- **analysis/indicators.py** — محاسبه RSI, MACD, EMA20/50/100/200, Bollinger, ATR, ADX,
  Ichimoku, SuperTrend (پیاده‌سازی دستی), OBV, MFI, CCI, CMF, VWAP روی کندل‌های واقعی
  (نه فقط قیمت کوینگکو - چون ATR/ADX/Ichimoku/SuperTrend نیاز به High/Low واقعی دارند).
- **analysis/smc.py** — تشخیص الگوریتمیک Smart Money Concepts:
  BOS (Break Of Structure) / CHOCH (Change of Character)، Order Block، Fair Value Gap،
  Liquidity Sweep. همه بر پایه سوئینگ‌های فرکتالی و رفتار کندل محاسبه می‌شوند.
- **analysis/confluence.py** — موتور امتیازدهی نهایی (۰ تا ۱۰۰):
  اندیکاتورها (۴۵) + SMC (۲۰) + هم‌راستایی چند‌تایم‌فریمه (۲۰) + مشتقات/حجم (۱۵).
  تصمیم نهایی: `score >= 80` → SIGNAL, `60-79` → WATCHLIST, `<60` → REJECT (نادیده گرفته می‌شود).
- **futures/derivatives.py** — دیتای واقعی از توبیت: Funding Rate، Open Interest، Long/Short Ratio
  (اندپوینت‌های رسمی `api-docs.toobit.com`). چون ربات هر ۵ دقیقه از صفر روی GitHub Actions اجرا می‌شود،
  OI قبلی در جدول جدید `derivatives_snapshot` ذخیره می‌شود تا تغییرات OI بین دو اجرا قابل مقایسه باشد.
- **scheduler/performance.py** — محاسبه Win Rate، میانگین RR، میانگین مدت معامله، سود کل،
  بهترین/بدترین معامله از روی `closed_trades`.
- **.github/workflows/performance.yml** — ارسال گزارش عملکرد هر دوشنبه ساعت ۸ صبح UTC.

## ۲) فایل‌های بازنویسی‌شده (منطق قدیمی حفظ نشد چون ساده و ناکافی بود)

- **futures/futures_scanner.py** و **spot/spot_scanner.py** — امتیازدهی دستی قدیمی حذف و
  با `analysis.confluence.run_confluence_analysis` جایگزین شد. خروجی هر سیگنال حالا شامل
  `decision` (SIGNAL/WATCHLIST/REJECT) است.
- **market_scanner/signal_detector.py** — قبلاً از تابعی در spot_scanner ایمپورت می‌کرد که
  در بازنویسی حذف شده بود؛ حالا مستقیماً از موتور کانفلوئنس استفاده می‌کند (باگ رفع شد).

## ۳) فایل‌های ویرایش‌شده (افزوده، نه جایگزین کامل)

- **database/db.py** — ۴ جدول جدید اضافه شد: `watchlist`, `closed_trades`,
  `telegram_messages`, `derivatives_snapshot`. متد عمومی `fetch_by_field` هم اضافه شد.
- **database/models.py** — دیتاکلاس‌های `WatchlistItem`, `ClosedTrade`, `TelegramMessageLog`.
- **scheduler/jobs.py**:
  - تابع `process_confluence_signal` اضافه شد: مسیریابی خودکار SIGNAL → پیام معاملاتی +
    ثبت `active_signals`، یا WATCHLIST → پیام واچ‌لیست + ثبت `watchlist` (بدون تکرار،
    و با بستن خودکار واچ‌لیست وقتی سیگنال واقعی تایید شد).
  - هر پیام ارسالی (سیگنال، واچ‌لیست، TP hit، SL hit، گزارش عملکرد) در `telegram_messages` ثبت می‌شود.
  - وقتی معامله با TP نهایی یا SL بسته می‌شود، رکورد کامل آن (درصد سود، RR، مدت‌زمان) در
    `closed_trades` ذخیره می‌شود — این دقیقاً همان چیزی است که `performance.py` می‌خواند.
- **telegram_bot/formatters.py** — پیام سیگنال معاملاتی حالا شامل «روند» و بخش «ریسک» است؛
  تابع جدید `format_watchlist_signal` دقیقاً طبق فرمت درخواستی‌ات (قیمت فعلی/مقاومت/شرط/ورود پیشنهادی/ابطال).
- **main.py** — حالت جدید `performance` (`python main.py performance`).

## ۴) نکات مهم برای اجرا

1. هیچ Secret جدیدی لازم نیست — از همان `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` /
   `TOOBIT_ACCESS_KEY` / `TOOBIT_SECRET_KEY` موجود استفاده می‌شود.
2. کتابخانه `ta==0.11.0` که در `requirements.txt` بود، همه‌ی اندیکاتورهای جدید را پشتیبانی می‌کند؛
   نیازی به نصب پکیج اضافه نیست.
3. اسکن فیوچرز حالا هم امتیاز اندیکاتور/SMC/MTF و هم فاندینگ/OI/Long-Short واقعی را چک می‌کند؛
   بنابراین ممکن است در ابتدا سیگنال‌های کمتری نسبت به قبل ارسال شود — این عمدی است
   (چون قبلاً امتیاز خیلی راحت به ۸۰+ می‌رسید).
4. جدول `derivatives_snapshot` و `watchlist` و `closed_trades` در اولین اجرا خودکار ساخته می‌شوند
   (`CREATE TABLE IF NOT EXISTS`) — نیازی به مایگریشن دستی نیست.
5. اگر از Supabase استفاده می‌کنی، باید این ۴ جدول جدید را در Supabase هم دستی بسازی
   (فایل `supabase_schema.sql` را با ساختار جدول‌های `CREATE_TABLES_SQL` در `database/db.py` هماهنگ کن).

## ۵) چیزهایی که هنوز اضافه نشده (برای فاز بعدی)

- تشخیص Whale واقعی از دیتای ترید فردی (الان فقط جهش حجم + L/S Ratio افراطی به‌عنوان پروکسی استفاده شده).
- گسترش بخش کشف پروژه جدید (dex/gem_scanner) با چک‌های عمیق‌تر امنیتی/تیم/سرمایه‌گذار.
- گسترش news_fetcher برای منابع بیشتر (فعلاً منبع‌های موجود دست‌نخورده مانده).
