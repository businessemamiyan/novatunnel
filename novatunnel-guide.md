# 🚀 راهنمای کامل نصب و راه‌اندازی NovaTunnel Bot
### ربات تلگرام فروش VPN — نسخه ۱.۰
---

> **قبل از هر چیز:** توکن ربات قدیمی را باطل کن. به @BotFather برو، دستور `/revoke` بزن و توکن جدید بگیر. توکن قدیمی‌ای که در مستندات قبلی نوشتی لو رفته.

---

## فهرست مطالب
1. پیش‌نیازها
2. آماده‌سازی سرور
3. نصب n8n روی Docker
4. تنظیم Supabase (دیتابیس)
5. تنظیم ربات تلگرام
6. تنظیم X-ui Sanaei
7. تنظیم درگاه‌های پرداخت
8. import کردن Workflow در n8n
9. تنظیم متغیرهای محیطی
10. تنظیم Credentials در n8n
11. فعال‌سازی Webhook‌ها
12. تست و راه‌اندازی
13. اسکیما SQL دیتابیس
14. نقشه کامل Workflow (شرح هر نود)
15. سوالات متداول

---

## ۱. پیش‌نیازها

قبل از شروع باید این‌ها رو آماده داشته باشی:

| چی | کجا بگیری |
|---|---|
| سرور Ubuntu 22.04 (حداقل 2GB RAM) | هر هاستینگ ایرانی یا خارجی |
| دامنه یا ساب‌دامین برای n8n | مثلاً `n8n.yourdomain.com` |
| توکن ربات تلگرام (جدید) | @BotFather |
| حساب Supabase رایگان | supabase.com |
| Merchant ID زرین‌پال | zarinpal.com |
| API Key ناوپیمنتس | nowpayments.io |
| IP پنل X-ui: 94.75.223.106 | داری |

---

## ۲. آماده‌سازی سرور

**قدم ۱ — وصل شو به سرور:**
```bash
ssh root@YOUR_SERVER_IP
```

**قدم ۲ — سیستم رو آپدیت کن:**
```bash
apt update && apt upgrade -y
```

**قدم ۳ — Docker رو نصب کن:**
```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

**قدم ۴ — بررسی نصب Docker:**
```bash
docker --version
# باید چیزی شبیه: Docker version 24.x.x نشون بده
```

**قدم ۵ — Nginx و Certbot رو نصب کن (برای HTTPS):**
```bash
apt install nginx certbot python3-certbot-nginx -y
```

---

## ۳. نصب n8n روی Docker

**قدم ۱ — یک پوشه برای n8n بساز:**
```bash
mkdir -p /opt/novatunnel/n8n-data
cd /opt/novatunnel
```

**قدم ۲ — فایل docker-compose.yml رو بساز:**
```bash
nano docker-compose.yml
```

این محتوا رو داخلش بنویس:
```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.yourdomain.com          # ← دامنه خودت رو بذار
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.yourdomain.com  # ← همینجا هم
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=STRONG_PASSWORD_HERE   # ← عوضش کن
      - GENERIC_TIMEZONE=Asia/Tehran
      # متغیرهای NovaTunnel (بعداً پر می‌کنیم):
      - TELEGRAM_BOT_TOKEN=
      - SUPABASE_URL=
      - SUPABASE_SERVICE_KEY=
      - XUI_ADMIN_USER=
      - XUI_ADMIN_PASS=
      - XUI_INBOUND_ID=
      - XUI_PANEL_DOMAIN=94.75.223.106
      - XUI_VLESS_PORT=443
      - ADMIN_TELEGRAM_ID=
      - ZARINPAL_MERCHANT_ID=
      - NOWPAYMENTS_API_KEY=
      - NOWPAYMENTS_IPN_SECRET=
      - N8N_BASE_URL=https://n8n.yourdomain.com
    volumes:
      - /opt/novatunnel/n8n-data:/home/node/.n8n
```

ذخیره کن: `Ctrl+X` → `Y` → `Enter`

**قدم ۳ — n8n رو راه‌اندازی کن:**
```bash
docker compose up -d
```

**قدم ۴ — بررسی کن که اجرا شده:**
```bash
docker compose logs -f n8n
# باید "Editor is now accessible" ببینی
```

---

## ۴. تنظیم HTTPS با Nginx

**قدم ۱ — DNS دامنه‌ات رو تنظیم کن:**
در پنل DNS دامنه‌ات، یک رکورد A بساز:
```
n8n.yourdomain.com  →  YOUR_SERVER_IP
```
صبر کن تا DNS پروپاگیت بشه (معمولاً ۵ تا ۳۰ دقیقه).

**قدم ۲ — فایل Nginx بساز:**
```bash
nano /etc/nginx/sites-available/n8n
```

این محتوا رو بنویس:
```nginx
server {
    listen 80;
    server_name n8n.yourdomain.com;

    location / {
        proxy_pass http://localhost:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

**قدم ۳ — Nginx رو فعال کن:**
```bash
ln -s /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

**قدم ۴ — SSL بگیر:**
```bash
certbot --nginx -d n8n.yourdomain.com
# ایمیلت رو بنویس، Y بزن برای Terms
```

---

## ۵. تنظیم Supabase

**قدم ۱ — برو روی supabase.com و یک حساب رایگان بساز**

**قدم ۲ — یک پروجکت جدید بساز:**
- Name: `novatunnel`
- Database Password: یک رمز قوی انتخاب کن (ذخیره کن!)
- Region: نزدیک‌ترین به سرورت

**قدم ۳ — بعد از ساخت پروجکت، به SQL Editor برو و این اسکیما رو اجرا کن:**

```sql
-- ===== جدول کاربران =====
CREATE TABLE users (
    telegram_id   BIGINT PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    language      TEXT DEFAULT 'fa',
    referrer_id   BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    wallet_credit INTEGER DEFAULT 0,
    joined_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ===== جدول اشتراک‌ها =====
CREATE TABLE subscriptions (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_id   BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    plan_key      TEXT NOT NULL,
    client_uuid   TEXT NOT NULL,
    expiry_at     TIMESTAMPTZ NOT NULL,
    traffic_gb    INTEGER NOT NULL,
    price_paid    INTEGER NOT NULL,
    status        TEXT DEFAULT 'active',  -- active, expired, pending, cancelled
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ===== جدول دفترچه امتیاز Nova Points =====
CREATE TABLE point_ledger (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id       BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    amount        INTEGER NOT NULL,
    tier          INTEGER CHECK (tier IN (1,2,3)),
    status        TEXT DEFAULT 'hold',   -- hold, released, cancelled
    release_at    TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ===== جدول لینک‌های نمایندگی (رفرال ۳ سطحی) =====
CREATE TABLE agency_links (
    id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id       BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE UNIQUE,
    upline_id     BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, upline_id)
);

-- ===== تابع آمار داشبورد =====
CREATE OR REPLACE FUNCTION get_dashboard_stats()
RETURNS JSON AS $$
DECLARE result JSON;
BEGIN
    SELECT json_build_object(
        'total_users', (SELECT COUNT(*) FROM users),
        'active_subs', (SELECT COUNT(*) FROM subscriptions WHERE status = 'active' AND expiry_at > NOW()),
        'monthly_revenue', (SELECT COALESCE(SUM(price_paid),0) FROM subscriptions WHERE created_at > date_trunc('month', NOW()))
    ) INTO result;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ===== ایندکس‌ها برای سرعت =====
CREATE INDEX idx_subs_telegram ON subscriptions(telegram_id);
CREATE INDEX idx_subs_expiry ON subscriptions(expiry_at);
CREATE INDEX idx_subs_status ON subscriptions(status);
CREATE INDEX idx_points_user ON point_ledger(user_id);
CREATE INDEX idx_points_release ON point_ledger(release_at);
```

**قدم ۴ — اطلاعات اتصال رو بگیر:**
در پنل Supabase → Settings → API:
- `Project URL` → این رو ذخیره کن (مثلاً `https://xxxxx.supabase.co`)
- `service_role` secret → این رو ذخیره کن (توکن ادمین کامل)

---

## ۶. تنظیم ربات تلگرام

**قدم ۱ — به @BotFather برو:**
1. `/newbot` بزن (اگه ربات نداری)
2. یا `/mybot` → ربات → API Token → Revoke (توکن قدیمی رو باطل کن)
3. توکن جدید رو ذخیره کن

**قدم ۲ — ربات رو ادمین کانال کن:**
1. به کانال @novatunnelch برو
2. Settings → Administrators → Add Administrator
3. ربات رو اضافه کن (فقط نیاز به دسترسی Read Messages داره)

**قدم ۳ — Telegram ID ادمین (خودت) رو پیدا کن:**
به @userinfobot پیام بده — عدد ID رو ذخیره کن.

---

## ۷. تنظیم X-ui Sanaei

**قدم ۱ — به پنل X-ui وارد شو:**
```
https://94.75.223.106:2053
```

**قدم ۲ — Inbound ID رو پیدا کن:**
- به بخش Inbounds برو
- جلوی Inbound مورد نظر، عدد ID رو ببین (مثلاً ۱)
- این عدد رو ذخیره کن → `XUI_INBOUND_ID`

**قدم ۳ — دامنه یا IP پنل:**
اگه دامنه داری (مثلاً `vpn.yourdomain.com`):
- این رو به عنوان `XUI_PANEL_DOMAIN` ذخیره کن
- اگه ندری، همون IP یعنی `94.75.223.106` باقی می‌مونه

**قدم ۴ — پورت VLESS رو پیدا کن:**
در بخش Inbounds، پورت Inbound مورد نظر (مثلاً ۴۴۳) → `XUI_VLESS_PORT`

**نکته مهم:** ربات از طریق session cookie با X-ui کار می‌کنه. اگه پنل IP یا پورتش رو تغییر داد، باید متغیرها رو آپدیت کنی.

---

## ۸. تنظیم درگاه‌های پرداخت

### زرین‌پال:
1. به zarrinpal.com برو و حساب بساز
2. Dashboard → Business → Merchant ID رو کپی کن → `ZARINPAL_MERCHANT_ID`
3. در تنظیمات، آدرس callback رو ثبت کن: `https://n8n.yourdomain.com/webhook/zarinpal-callback`

### ناوپیمنتس (کریپتو):
1. به nowpayments.io برو
2. Dashboard → API Keys → بساز → `NOWPAYMENTS_API_KEY`
3. Dashboard → IPN Settings:
   - IPN Callback URL: `https://n8n.yourdomain.com/webhook/nowpayments-ipn`
   - IPN Secret Key رو ذخیره کن → `NOWPAYMENTS_IPN_SECRET`

### کارت به کارت:
شماره کارت خودت رو در node **"Ask For Receipt Photo"** جایگزین `6219-8619-XXXX-XXXX` و `به نام: ...` کن.

---

## ۹. Import کردن Workflow در n8n

**قدم ۱ — وارد n8n شو:**
```
https://n8n.yourdomain.com
```
با یوزر/پسوردی که در docker-compose تنظیم کردی وارد شو.

**قدم ۲ — Workflow رو import کن:**
1. از منوی بالا سمت چپ → **Workflows** → **Import from file**
2. فایل `novatunnel-workflow.json` رو آپلود کن
3. روی **Import** کلیک کن

---

## ۱۰. تنظیم Credentials در n8n

بعد از import، باید دو Credential بسازی:

### Credential اول — Telegram Bot:
1. در n8n: **Settings** → **Credentials** → **Add Credential**
2. نوع: **Telegram API**
3. Access Token: توکن ربات جدیدت رو بنویس
4. Name: `NovaTunnel Bot Token`
5. **Save**

### Credential دوم — Supabase (HTTP Header Auth):
1. **Add Credential** → نوع: **Header Auth**
2. Name: `Supabase Service Key`
3. Name (header): `apikey`
4. Value: Service Role Key از Supabase
5. **Save**

---

## ۱۱. تنظیم متغیرهای محیطی

فایل docker-compose رو ویرایش کن:
```bash
nano /opt/novatunnel/docker-compose.yml
```

همه مقادیر خالی بعد از `=` رو پر کن:

```yaml
- TELEGRAM_BOT_TOKEN=123456789:AAXXXXXX...      # توکن جدید
- SUPABASE_URL=https://xxxxx.supabase.co         # از Supabase Dashboard
- SUPABASE_SERVICE_KEY=eyJhbGc...               # Service Role Key
- XUI_ADMIN_USER=admin                           # یوزر پنل X-ui
- XUI_ADMIN_PASS=your_xui_password              # پسورد پنل X-ui
- XUI_INBOUND_ID=1                              # عدد ID Inbound
- XUI_PANEL_DOMAIN=94.75.223.106                # دامنه یا IP پنل
- XUI_VLESS_PORT=443                            # پورت VLESS
- ADMIN_TELEGRAM_ID=123456789                   # ID تلگرام خودت
- ZARINPAL_MERCHANT_ID=xxxxxxxx-xxxx-...        # از زرین‌پال
- NOWPAYMENTS_API_KEY=XXXXX                     # از ناوپیمنتس
- NOWPAYMENTS_IPN_SECRET=XXXXX                  # از ناوپیمنتس
- N8N_BASE_URL=https://n8n.yourdomain.com       # آدرس n8n
```

بعد ری‌استارت کن:
```bash
docker compose down && docker compose up -d
```

---

## ۱۲. فعال‌سازی Webhook تلگرام

بعد از ری‌استارت، باید Webhook رو ثبت کنی تا تلگرام آپدیت‌ها رو به n8n بفرسته.

**روش ۱ — از داخل n8n (راحت‌تر):**
1. Workflow رو باز کن
2. روی نود **"Telegram Trigger"** کلیک کن
3. بالای نود روی **"Execute Node"** کلیک کن — این Webhook رو خودکار ثبت می‌کنه

**روش ۲ — دستی (مطمئن‌تر):**
در مرورگر این URL رو باز کن (TOKEN رو عوض کن):
```
https://api.telegram.org/botTOKEN/setWebhook?url=https://n8n.yourdomain.com/webhook/telegram-trigger
```
باید پاسخ بگیری: `{"ok":true,"result":true}`

---

## ۱۳. تنظیمات نهایی و تست

**قدم ۱ — Workflow رو فعال کن:**
در n8n، در بالای Workflow گوشه راست، کلید **Active** رو روشن کن.

**قدم ۲ — تست کن:**
1. ربات رو در تلگرام پیدا کن
2. `/start` بزن
3. باید پیام عضویت در کانال بیاد
4. بعد از عضویت، منوی اصلی باید نشون داده بشه

**قدم ۳ — قیمت‌ها رو تنظیم کن:**
در نود **"Calculate Plan Price+Traffic"** و **"Show Plan Tiers"**، قیمت‌ها و حجم‌ها رو با مقادیر واقعی جایگزین کن.

**قدم ۴ — شماره کارت رو تنظیم کن:**
در نود **"Ask For Receipt Photo"**، شماره کارت و نام صاحب کارت رو بنویس.

---

## ۱۴. نقشه کامل Workflow

### بخش A — ورود و مسیریابی
| نود | کارش |
|---|---|
| Telegram Trigger | دروازه ورود. هر پیام و کلیک دکمه از اینجا وارد میشه |
| Parse Update | پیام معمولی، callback_query (کلیک دکمه) و عکس رو به یک فرمت یکسان تبدیل می‌کنه. نوع ورودی رو هم تشخیص میده (start/callback/admin...) |
| Route Update Type | بر اساس نوع ورودی، مسیر رو انتخاب می‌کنه |

### بخش B — /start و دروازه عضویت
| نود | کارش |
|---|---|
| Check Channel Membership | از API تلگرام می‌پرسه: آیا این کاربر عضو @novatunnelch هست؟ |
| Is Member? | جواب رو بررسی می‌کنه |
| Send Join Required Message | اگه عضو نیست، پیام عضویت اجباری با لینک کانال و اینستاگرام میفرسته |
| Upsert User | اگه عضو هست، کاربر رو در Supabase ثبت یا آپدیت می‌کنه |
| Send Language Selection | انتخاب زبان فارسی / انگلیسی |

### بخش C — مسیریابی کلیک‌ها و منوی اصلی
| نود | کارش |
|---|---|
| Get User Record | اطلاعات کاربر از Supabase می‌خونه (زبان و...) |
| Callback Router | بر اساس داده‌ی دکمه‌ی کلیک‌شده، مسیر مناسب رو انتخاب می‌کنه |
| Save Language Choice | زبان انتخابی رو در Supabase ذخیره می‌کنه |
| Build Main Menu Text+Buttons | متن و دکمه‌های منوی اصلی رو بر اساس زبان می‌سازه |
| Send Main Menu | منوی اصلی رو نشون میده |

### بخش D — خرید پلن
| نود | کارش |
|---|---|
| Show Plan Tiers | ۴ پلن با قیمت و حجم نشون میده |
| Calculate Plan Price+Traffic | بر اساس پلن انتخابی، اطلاعات کامل قیمت/ترافیک/مدت رو آماده می‌کنه |
| Show Payment Methods | ۳ روش پرداخت نشون میده |
| Parse Dynamic Callback | کلیک‌های پویا (pay_zarinpal_plan_1m و...) رو تجزیه می‌کنه |
| Dynamic Action Router | بر اساس action، به شاخه پرداخت مناسب هدایت می‌کنه |

### بخش E — زرین‌پال
| نود | کارش |
|---|---|
| Zarinpal Request Payment | درخواست پرداخت به API زرین‌پال می‌فرسته و Authority می‌گیره |
| Send Zarinpal Pay Link | لینک پرداخت رو به کاربر میفرسته |
| Zarinpal Callback Webhook | بعد از پرداخت، زرین‌پال کاربر رو اینجا ری‌دایرکت می‌کنه |
| Zarinpal Verify Payment | پرداخت رو تایید می‌کنه |
| Zarinpal Verified? | کد ۱۰۰ = موفق |
| Parse Zarinpal Success Params | ID کاربر و پلن رو از URL استخراج می‌کنه |

### بخش F — کریپتو (Nowpayments)
| نود | کارش |
|---|---|
| Create Nowpayments Invoice | Invoice در Nowpayments می‌سازه |
| Send Crypto Pay Link | لینک پرداخت کریپتو به کاربر |
| Nowpayments IPN Webhook | اعلان خودکار بعد از پرداخت |
| Verify IPN HMAC Signature | امضای دیجیتال رو چک می‌کنه (امنیت) |
| Nowpayments Status Finished? | وضعیت `finished` = موفق |
| Parse Nowpayments Success Params | ID کاربر و پلن رو از order_id استخراج می‌کنه |

### بخش G — کارت به کارت
| نود | کارش |
|---|---|
| Ask For Receipt Photo | شماره کارت و درخواست عکس رسید |
| Forward Receipt To Admin | عکس رسید رو با دکمه‌های تایید/رد به ادمین فوروارد می‌کنه |
| Parse Card Approve Params | بعد از تایید ادمین، ID کاربر و پلن رو می‌خونه |
| Send Rejection Notice | در صورت رد، به کاربر اطلاع میده |

### بخش H — فعال‌سازی روی پنل X-ui (مشترک)
| نود | کارش |
|---|---|
| Lookup Plan By Key | اطلاعات پلن رو از کلید پلن دوباره بازسازی می‌کنه |
| X-UI Login | با یوزر/پسورد ادمین وارد پنل X-ui میشه و session cookie می‌گیره |
| Generate Client UUID+Email | UUID و ایمیل یکتا برای کاربر جدید می‌سازه |
| X-UI Add Client | کاربر جدید رو با مشخصات ترافیک و تاریخ انقضا روی پنل می‌سازه |
| Build Config Links | لینک VLESS رو بر اساس UUID و دامنه پنل می‌سازه |
| Generate QR Code | QR Code از لینک می‌سازه (api.qrserver.com) |
| Send Config + QR to User | عکس QR + لینک + توضیحات رو به کاربر میفرسته |
| Insert Subscription Record | خرید رو در جدول subscriptions ذخیره می‌کنه |
| Calculate 3-Tier Referral Bonus | درصد پاداش ۳ سطح رفرال رو حساب می‌کنه (۱۰٪/۵٪/۲٪) |
| Get Referrer Chain | معرف کاربر رو از Supabase می‌خونه |
| Insert Point Ledger (24h hold) | امتیاز رو با ۲۴ ساعت تاخیر در point_ledger ثبت می‌کنه |
| Notify Admin New Purchase | پیام خرید جدید به ادمین |

### بخش I — حساب کاربری
| نود | کارش |
|---|---|
| Get User Subscriptions | اشتراک‌های فعال کاربر از Supabase |
| Format Account Summary | لیست رو به متن قابل خواندن تبدیل می‌کنه |
| Send Account Summary | نتیجه رو به کاربر نشون میده |

### بخش J — خدمات جانبی
| نود | کارش |
|---|---|
| Get Wallet + Points | امتیازهای point_ledger رو می‌خونه |
| Send Wallet Info | موجودی رو نشون میده |
| Build Referral Link | لینک اختصاصی دعوت با ref_ID می‌سازه |
| Send Referral Info | لینک رو به کاربر میفرسته |
| Send Support Message | اطلاعات پشتیبانی |
| Send About Message | لینک کانال و اینستاگرام |

### بخش K — پنل ادمین
| نود | کارش |
|---|---|
| Is Admin? | چک می‌کنه آیا فرستنده همون ADMIN_TELEGRAM_ID هست |
| Send Admin Menu | منوی ادمین |
| Get Stats Aggregate | آمار کلی از Supabase function |
| Get Pending Receipts | رسیدهای در انتظار تایید |
| Split In Batches | برای ارسال پیام همگانی، لیست رو دسته‌بندی می‌کنه |
| Broadcast Message | پیام رو به همه کاربران میفرسته |

### بخش L — یادآوری خودکار
| نود | کارش |
|---|---|
| Daily Schedule (09:00) | هر روز ساعت ۹ صبح اجرا میشه |
| Get Expiring Subscriptions | اشتراک‌هایی که تا ۳ روز دیگه تموم میشن |
| Split 3-Day vs Today Reminders | تفکیک: امروز تموم میشه vs ۳ روز دیگه |
| Send Expiry-Day Reminder | پیام فوری + دکمه تمدید |
| Send 3-Day Reminder | یادآوری ۳ روز قبل |
| X-UI Disable Expired Client | کاربر منقضی‌شده رو از پنل حذف می‌کنه |

---

## ۱۵. تنظیمات مهم بعد از Import

### Retry On Fail — روی همه HTTP Request نودها:
1. روی هر نود HTTP Request کلیک کن
2. تب **Settings** رو باز کن
3. **On Error** → **Retry On Fail** انتخاب کن
4. Max Tries: `3`
5. Wait Between Tries: `1000ms`

### پیکربندی Admin Notify:
نود **"Notify Admin New Purchase"** الان `chatId` رو از کاربر می‌خونه. باید تغییرش بدی:
1. روی نود کلیک کن
2. مقدار `chatId` رو به `={{$env.ADMIN_TELEGRAM_ID}}` تغییر بده

### Inbound ID در X-UI Add Client:
در نود **"X-UI Add Client"**، مطمئن شو `id: $env.XUI_INBOUND_ID` برابر ID واقعی Inbound در پنلته.

---

## ۱۶. سوالات متداول

**ربات پیامی نمیده — چیکار کنم؟**
```bash
docker compose logs n8n | tail -50
```
دنبال خطا بگرد. احتمالاً Webhook ثبت نشده یا توکن اشتباهه.

**X-UI Authentication Error میگیرم؟**
یوزر/پسورد رو چک کن. اگه پنل ۲FA داره باید خاموشش کنی برای API.

**Zarinpal callback نمیرسه؟**
مطمئن شو callback_url در موقع ساخت لینک، دقیقاً همون آدرسی هست که در پنل زرین‌پال ثبت کردی.

**چطور قیمت‌ها رو عوض کنم؟**
نود **"Calculate Plan Price+Traffic"** رو باز کن و مقادیر `price` رو ویرایش کن. نود **"Show Plan Tiers"** رو هم برای متن نمایشی آپدیت کن.

**چطور پروتکل‌های دیگه (VMess، Trojan) هم اضافه کنم؟**
در نود **"Build Config Links"** کد رو گسترش بده تا چند لینک بسازه، سپس در **"Send Config + QR to User"** همه رو ارسال کنی.

---

## چک‌لیست نهایی

قبل از لایو کردن مطمئن شو:

- [ ] توکن ربات قدیمی باطل شده و توکن جدید استفاده میشه
- [ ] دامنه n8n با HTTPS کار می‌کنه
- [ ] همه متغیرهای محیطی در docker-compose پر شدن
- [ ] اسکیما SQL در Supabase اجرا شده
- [ ] Credential تلگرام در n8n ست شده
- [ ] Credential Supabase در n8n ست شده
- [ ] Webhook تلگرام ثبت شده
- [ ] Workflow فعال (Active) شده
- [ ] ربات پیام /start رو جواب میده
- [ ] قیمت‌های پلن درست تنظیم شدن
- [ ] شماره کارت صحیح وارد شده
- [ ] ADMIN_TELEGRAM_ID درست تنظیم شده
- [ ] یک تست خرید کامل انجام شده


---

## ۱۷. اضافه کردن Error Handler (Workflow جداگانه)

این workflow جدا، هر خطایی رو که در workflow اصلی بیفته می‌گیره و به ادمین پیام میده.

**مراحل:**
1. در n8n روی **+ New Workflow** کلیک کن
2. یک نود **Error Trigger** اضافه کن
3. بعدش یک نود **Telegram** اضافه کن:
   - Operation: `Send Message`
   - Chat ID: `={{$env.ADMIN_TELEGRAM_ID}}`
   - Text:
```
⚠️ خطا در NovaTunnel Bot
نود: {{$json.execution.lastNodeExecuted}}
خطا: {{$json.execution.error.message}}
زمان: {{$now.toFormat('yyyy-MM-dd HH:mm:ss')}}
```
4. Workflow رو ذخیره کن با نام `NovaTunnel Error Handler`
5. در workflow اصلی → Settings → Error Workflow → این workflow رو انتخاب کن

---

## ۱۸. Cron Job برای آزادسازی Nova Points

امتیازهای `hold` بعد از ۲۴ ساعت باید آزاد بشن. این رو یا با یک scheduled workflow در n8n انجام بده:

**در n8n یک Workflow جدید بساز:**

نود ۱ — Schedule Trigger:
```
Cron: 0 * * * *  (هر ساعت)
```

نود ۲ — HTTP Request (Supabase):
```
Method: PATCH
URL: {{$env.SUPABASE_URL}}/rest/v1/point_ledger
Headers:
  apikey: {{$env.SUPABASE_SERVICE_KEY}}
  Authorization: Bearer {{$env.SUPABASE_SERVICE_KEY}}
Query params:
  status=eq.hold
  release_at=lte.{{$now.toISO()}}
Body (JSON):
  {"status": "released"}
```

---

## ۱۹. نکات مهم امنیتی

1. **توکن ربات** را هرگز در کد، گیت یا چت ننویس — فقط در متغیر محیطی
2. **Service Key سوپاپیس** دسترسی کامل به دیتابیس داره — مثل رمز بانک مراقبش باش
3. **پنل X-ui** را با فایروال محدود کن:
```bash
ufw allow 22      # SSH
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw allow 5678    # n8n (اگه لازمه)
ufw enable
```
4. **IPN Nowpayments** را حتماً با بررسی HMAC تایید کن — نود "Verify IPN HMAC Signature" این کار رو می‌کنه
5. **ادمین تنها یک نفر** باشه — از `ADMIN_TELEGRAM_ID` برای کنترل استفاده کن

---

## ۲۰. نحوه آپدیت و نگهداری

**آپدیت n8n:**
```bash
cd /opt/novatunnel
docker compose pull
docker compose up -d
```

**بکاپ گرفتن از workflow‌ها:**
در n8n → Workflows → روی workflow کلیک کن → سه نقطه → Download

**بکاپ Supabase:**
در Supabase Dashboard → Settings → Backups → Manual Backup

**بررسی لاگ‌ها:**
```bash
docker compose logs n8n --tail=100 -f
```

---

## ۲۱. متن‌های کامل پیام‌ها (قالب‌ها)

### پیام خوش‌آمدگویی (فارسی):
```
👋 به NovaTunnel خوش اومدی!

ما سریع‌ترین و پایدارترین سرویس VPN رو برات آماده کردیم.
کانال ما رو دنبال کن: @novatunnelch

از منوی زیر شروع کن 👇
```

### پیام تحویل کانفیگ (فارسی):
```
🎉 اشتراک VPN تو فعال شد!

━━━━━━━━━━━━━━━━
📋 مشخصات اشتراک:
📅 مدت: [X ماهه]
📊 ترافیک: [X] گیگابایت
⏰ تاریخ انقضا: [تاریخ]
━━━━━━━━━━━━━━━━

🔗 لینک اتصال:
[لینک VLESS]

📱 نحوه استفاده:
1. اپ v2rayNG (اندروید) یا Shadowrocket (iOS) رو نصب کن
2. QR بالا رو اسکن کن یا لینک رو کپی کن
3. سرور رو فعال کن و enjoy کن! 🚀

📞 مشکل داری؟ @novatunnel_support
```

### پیام انقضا (فارسی):
```
⏰ اشتراک VPN تو تموم شد!

برای تمدید و ادامه استفاده از دکمه زیر اقدام کن.
اگه سوالی داری: @novatunnel_support
```

### پیام معرفی دوست (فارسی):
```
🎁 با دعوت دوستات درآمد کسب کن!

لینک اختصاصی تو:
[لینک]

💰 پورسانت:
• معرفی مستقیم: ۱۰٪ از هر خرید
• سطح دوم: ۵٪
• سطح سوم: ۲٪

امتیازها بعد از ۲۴ ساعت از خرید آزاد میشن.
```

---

## ۲۲. خلاصه متغیرهای محیطی

| متغیر | توضیح | مثال |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | توکن ربات از BotFather | `123456:AAXXXX` |
| `SUPABASE_URL` | آدرس پروجکت Supabase | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | کلید Service Role | `eyJhbGc...` |
| `XUI_ADMIN_USER` | یوزرنیم ادمین X-ui | `admin` |
| `XUI_ADMIN_PASS` | پسورد ادمین X-ui | `strongpass` |
| `XUI_INBOUND_ID` | شماره Inbound | `1` |
| `XUI_PANEL_DOMAIN` | دامنه یا IP پنل | `94.75.223.106` |
| `XUI_VLESS_PORT` | پورت VLESS | `443` |
| `ADMIN_TELEGRAM_ID` | ID تلگرام ادمین | `98765432` |
| `ZARINPAL_MERCHANT_ID` | Merchant ID زرین‌پال | `xxxxxxxx-xxxx-...` |
| `NOWPAYMENTS_API_KEY` | API Key ناوپیمنتس | `XXXXX` |
| `NOWPAYMENTS_IPN_SECRET` | IPN Secret ناوپیمنتس | `XXXXX` |
| `N8N_BASE_URL` | آدرس کامل n8n | `https://n8n.yourdomain.com` |

---

*راهنمای NovaTunnel Bot v1.0 — تمام*
