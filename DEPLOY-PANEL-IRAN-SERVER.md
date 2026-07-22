# راهنمای دیپلوی پنل مدیریت (panel-api + admin-panel) روی سرور ایران

این راهنما رو خودت (یا از سیستمت با SSH، یا از کنسول وب هاست) روی سرور رلهٔ ایران
(`109.122.246.148`) اجرا می‌کنی — من (Claude) از محیط ابری فعلی‌ام اصلاً نمی‌تونم به این
سرور SSH بزنم (پورت ۲۲ از این محیط بسته‌ست)، برای همین این مراحل باید دستی طی بشن.

هیچ‌کدوم از این مراحل به `bot`/`admin_api`/`automation` روی سرور هلند دست نمی‌زنه — کاملاً
مجزاست.

---

## ⚠️ قبل از شروع — یک محدودیت مهم تلگرام

صفحهٔ ورود از **Telegram Login Widget** استفاده می‌کنه. تلگرام این ویجت رو فقط روی یک
**دامنهٔ ثبت‌شده با HTTPS** قبول می‌کنه، نه روی آی‌پی خام. یعنی قبل از اینکه صفحهٔ لاگین
واقعاً کار کنه، باید:
1. یک ساب‌دامنه (مثلاً `panel.novaprd.ir`) با DNS نوع `A` به `109.122.246.148` اشاره کنه
   (دقیقاً مثل کاری که قبلاً برای `vip.novaprd.ir` انجام شده بود).
2. روی همون دامنه گواهی SSL واقعی نصب بشه (مرحلهٔ ۸).
3. با دستور `/setdomain` در **@BotFather** برای بات، همون دامنه (بدون https:// و بدون
   مسیر، فقط مثلاً `panel.novaprd.ir`) ثبت بشه.

بدون این سه تا، ویجت لاگین خطای «Bot domain invalid» می‌ده. تا وقتی دامنه/SSL آماده نشده،
می‌تونی فقط `curl` به `/health` بزنی تا مطمئن بشی سرویس بالاست، ولی لاگین واقعی کار نمی‌کنه.

---

## مرحله ۰ — اجرای migration دیتابیس (نیازی به سرور نداره)

این کار رو از داخل **Supabase Dashboard → SQL Editor** (پروژهٔ همون Supabase فعلی) انجام
بده، مستقل از سرور:

```sql
create table admin_refresh_tokens (
  id uuid primary key default gen_random_uuid(),
  telegram_id bigint not null references bot_admins(telegram_id) on delete cascade,
  token_hash text not null unique,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz
);

comment on table admin_refresh_tokens is 'Refresh tokenهای صادرشده برای پنل مدیریت دسکتاپ (panel-api) — فقط hash ذخیره می‌شود، نه خود توکن.';

create index idx_admin_refresh_tokens_telegram_id on admin_refresh_tokens(telegram_id);
create index idx_admin_refresh_tokens_expires_at on admin_refresh_tokens(expires_at);

alter table admin_refresh_tokens enable row level security;
```

(همون فایل `supabase/migrations/20260721000001_admin_panel_refresh_tokens.sql` توی ریپو.)

---

## مرحله ۱ — SSH به سرور ایران

```bash
ssh <username>@109.122.246.148
```

## مرحله ۲ — نصب پیش‌نیازها (اگر از قبل نصب نیستن)

```bash
sudo dnf install -y git python3.11 python3.11-pip nodejs npm
python3.11 -m venv --help >/dev/null || sudo dnf install -y python3.11-venv
```

## مرحله ۳ — گرفتن کد

```bash
cd /opt   # یا هر مسیری که ترجیح می‌دی
sudo git clone https://github.com/businessemamiyan/novatunnel.git
cd novatunnel
sudo git checkout claude/ai-sales-platform-novatunnel-er4qsw
```

اگر بعداً این برنچ merge شد به `main`، دفعات بعد کافیه:
```bash
cd /opt/novatunnel && sudo git checkout main && sudo git pull
```

## مرحله ۴ — تنظیم panel-api

```bash
cd /opt/novatunnel/panel-api
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # یا vi، مقادیر واقعی رو پر کن:
```

مقادیر لازم در `.env`:
- `BOT_TOKEN` — همون توکن بات تلگرام (از `bot/.env` روی سرور هلند یا از BotFather)
- `DATABASE_URL` — دقیقاً همون رشتهٔ اتصال Supabase که `bot/.env`/`admin_api/.env` دارن
- `MARZBAN_ADMIN_USER` / `MARZBAN_ADMIN_PASSWORD` — panel-api خودش ازش استفاده نمی‌کنه ولی
  پکیج `shared/config.py` وجودشون رو الزامی می‌خواد؛ همون مقادیر واقعی رو بذار (یا هر
  رشتهٔ غیرخالی اگر نمی‌خوای مقدار واقعی همین‌جا هم باشه)
- `JWT_SECRET` — یک رشتهٔ تصادفی و قوی **جدید** (مثلاً با `openssl rand -hex 32` بسازش)،
  هرگز برابر با bot token یا رمز دیگه‌ای نباشه
- `CORS_ORIGINS` — اگه فرانت رو با همین سرویس سرو می‌کنی (مرحلهٔ ۶) خالی بذار؛ اگه جدا
  سرو می‌کنی، آدرس دقیق فرانت رو بذار (مثلاً `https://panel.novaprd.ir`)
- `TELEGRAM_BOT_USERNAME` — یوزرنیم بات بدون @ (همون که در لینک‌های نمایندگی هم استفاده
  می‌شه)

### تست دستی قبل از سرویس دائمی

```bash
cd /opt/novatunnel/panel-api
source venv/bin/activate
PYTHONPATH=.. uvicorn main:app --host 0.0.0.0 --port 8001
```

از یک ترمینال دیگه (یا مرورگر):
```bash
curl http://109.122.246.148:8001/health
# باید {"ok":true} برگردونه
```

اگه این خطا داد که به Supabase وصل نمی‌شه (`ConnectTimeout` یا مشابه)، یعنی همون ریسکی
که قبلاً هشدار داده بودم واقعیه — سرور ایران به `aws-0-eu-west-1.pooler.supabase.com`
دسترسی نداره و باید مثل زرین‌پال یه راه‌حل شبکه (تونل/DNS دیگه) پیدا بشه. `Ctrl+C` بزن و
بهم بگو تا با هم حلش کنیم.

اگه سالم بود، `Ctrl+C` بزن و برو مرحلهٔ بعد.

## مرحله ۵ — systemd service برای panel-api (اجرای دائمی + ری‌استارت خودکار)

```bash
sudo tee /etc/systemd/system/novatunnel-panel-api.service > /dev/null <<'EOF'
[Unit]
Description=NovaTunnel Panel API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/novatunnel/panel-api
Environment=PYTHONPATH=/opt/novatunnel
ExecStart=/opt/novatunnel/panel-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now novatunnel-panel-api
sudo systemctl status novatunnel-panel-api --no-pager
```

## مرحله ۶ — ساخت فرانت (admin-panel) و سرو از همون panel-api

خبر خوب: panel-api طوری نوشته شده که اگه `admin-panel/dist` کنارش وجود داشته باشه،
خودش همون رو هم سرو می‌کنه — نیازی به nginx جدا نیست (اختیاریه، اگه ترجیح می‌دی جدا
باشه هم می‌تونی).

```bash
cd /opt/novatunnel/admin-panel
cp .env.example .env
nano .env
```

مقادیر `.env` فرانت:
- `VITE_PANEL_API_BASE_URL` — چون قراره از همون سرویس سرو بشه، بذار خالی نمونه بلکه
  آدرس خودش رو بده: `https://panel.novaprd.ir` (بعد از آماده شدن دامنه/SSL در مرحلهٔ ۸) —
  یا موقتاً برای تست `http://109.122.246.148:8001`
- `VITE_TELEGRAM_BOT_USERNAME` — یوزرنیم بات، همون مقدار مرحلهٔ ۴

```bash
npm install
npm run build
sudo systemctl restart novatunnel-panel-api
```

حالا با باز کردن `http://109.122.246.148:8001` باید فرانت لود بشه (لاگین واقعی هنوز کار
نمی‌کنه تا دامنه/SSL/BotFather آماده بشه — مرحلهٔ بعد).

## مرحله ۷ — باز کردن پورت در فایروال

```bash
sudo ufw allow 8001/tcp
# اگه بعداً nginx با پورت ۴۴۳ جلوش گذاشتی، این مرحله لازم نیست، به‌جاش:
# sudo ufw allow 443/tcp
```

## مرحله ۸ — دامنه + HTTPS (اجباری برای کارکردن واقعی لاگین تلگرام)

ساده‌ترین راه: nginx به‌عنوان reverse proxy جلوی panel-api + Let's Encrypt.

```bash
sudo dnf install -y nginx certbot python3-certbot-nginx

sudo tee /etc/nginx/conf.d/novatunnel-panel.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name panel.novaprd.ir;
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo systemctl enable --now nginx
sudo nginx -t && sudo systemctl reload nginx

# اول DNS رکورد A برای panel.novaprd.ir → 109.122.246.148 رو بساز و صبر کن propagate بشه، بعد:
sudo certbot --nginx -d panel.novaprd.ir
```

بعد از موفقیت certbot، `.env` فرانت (`VITE_PANEL_API_BASE_URL`) و ری‌بیلد (`npm run build`)
رو با آدرس نهایی `https://panel.novaprd.ir` آپدیت کن و `systemctl restart novatunnel-panel-api`
بزن.

## مرحله ۹ — ثبت دامنه در BotFather

توی چت **@BotFather**:
```
/setdomain
```
بات مربوطه رو انتخاب کن، بعد فقط `panel.novaprd.ir` (بدون https و بدون /) رو بفرست.

## مرحله ۱۰ — تست نهایی

مرورگر: `https://panel.novaprd.ir` → دکمهٔ ورود تلگرام باید ظاهر بشه → بعد از کلیک و تایید،
باید وارد داشبورد بشی (فقط اگه همون telegram_id توی جدول `bot_admins` باشه).

---

## عیب‌یابی سریع

| علامت | علت محتمل |
|---|---|
| `/health` جواب نمی‌ده | سرویس بالا نیومده؛ `journalctl -u novatunnel-panel-api -n 50` رو چک کن |
| خطای اتصال دیتابیس در لاگ | سرور ایران به Supabase دسترسی نداره — نیاز به راه‌حل شبکه (مثل تونل زرین‌پال) |
| «Bot domain invalid» موقع کلیک لاگین | دامنه هنوز در BotFather ثبت نشده یا HTTPS نداره |
| صفحه لود می‌شه ولی بعد از لاگین چیزی نمیاد (CORS error در کنسول مرورگر) | اگه فرانت رو جدا از panel-api سرو می‌کنی، `CORS_ORIGINS` توی `.env` سرور رو دقیقاً برابر آدرس فرانت بذار |
| ادمین شناخته نمی‌شه بعد از لاگین موفق تلگرام | telegram_id در جدول `bot_admins` نیست/`is_active=false` است |

## Rollback

```bash
sudo systemctl stop novatunnel-panel-api
sudo systemctl disable novatunnel-panel-api
```
هیچ چیزی روی سرور هلند یا دیتابیس اصلی (جز جدول جدید `admin_refresh_tokens`) تغییر نکرده،
پس این کاملاً بی‌خطر و قابل قطع/برگشت است.
