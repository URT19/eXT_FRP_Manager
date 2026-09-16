<div align="center">

# 🚀 eXtreme FRP Manager v3.1

**مدیر پیشرفته تونل FRP چندپروتکلی با تجمیع HAProxy**

<img width="674" height="648" alt="image" src="https://github.com/user-attachments/assets/b246232a-4156-4c80-96ca-f8c1139d7913" />


[![Version](https://img.shields.io/badge/version-3.0.0-blue?style=for-the-badge)](https://github.com/ExtremeDot/frp_manager)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Ubuntu](https://img.shields.io/badge/ubuntu-22.04%20%7C%2024.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

مدیر تونل FRP چندپروتکلی پیشرفته با **تجمیع HAProxy**  
و معماری **مسیر/کانال (Route/Channel)** — طراحی‌شده برای مسیریابی ترافیک ایران ← خارج.

[📥 دانلود](#-دانلود) · [ویژگی‌ها](#-ویژگی‌ها) · [نصب](#-نصب) · [استفاده](#-استفاده) · [تصاویر](#-تصاویر)

</div>



---

## 📥 دانلود

### آخرین نسخه: v3.0.0

<div align="center">

[Download V3.1 ](https://github.com/ExtremeDot/eXT-FRP-Manager/releases/download/v3.1/frp-manager_v3.1.zip)

**حجم فایل:** حدود ۵۰ کیلوبایت · **فرمت:** ZIP

</div>

### نصب سریع


### دانلود

```
wget https://github.com/ExtremeDot/eXT-FRP-Manager/releases/download/v3.1/frp-manager_v3.1.zip
unzip frp-manager_v3.1.zip
cd frp-manager
```

### نصب

```
sudo bash install.sh
```

### اجرا

```
sudo frp-cli
```

### یا کلون از گیت

```bash
git clone https://github.com/ExtremeDot/eXT-FRP-Manager.git
cd frp_manager
sudo bash install.sh
sudo frp-cli
```

---

## ✨ ویژگی‌ها

<table>
<tr>
<td width="50%">

### 🌐 پشتیبانی چندپروتکلی
- **TCP** — سریع‌ترین و رایج‌ترین
- **KCP** — بهترین برای شبکه‌های پرپکت‌لاس (UDP)
- **QUIC** — مدرن و پهنای‌باند بالا (UDP)
- **WebSocket** — دور زدن فایروال / CDN

### ⚖️ تجمیع HAProxy
- توزیع ترافیک روی چند تونل موازی
- تجمیع پهنای‌باند از چند سرور
- Failover خودکار در صورت قطع کانال
- بالانسینگ Round-robin / leastconn / source

### 🎯 ویزارد ترکیبی
- ساخت Node + Route در یک جریان
- حالت سریع: فقط ۳ سؤال
- حالت سفارشی: کنترل کامل

</td>
<td width="50%">

### ⌨️ میانبرهای کلید F

| کلید | عملکرد                          |
|------|---------------------------------|
| F1   | راهنما                          |
| F2   | روشن/خاموش کردن حالت راهنما     |
| F3   | زبان (فینگلیش / انگلیسی)        |
| F5   | تعویض مکان (ایران ↔ خارج)       |
| F7   | حالت پیشرفته / ساده             |
| F10  | خروج                            |

### 🎨 رابط کاربری مدرن
- باکس‌ها و پنل‌های رنگی
- مشاور هوشمند متنی
- وضعیت زنده کانال‌ها
- دو زبانه (فینگلیش / انگلیسی)

### 🚀 راه‌اندازی آسان
- نصب یک‌کلیکی: `sudo bash install.sh`
- خروجی تمیز پروژه: `sudo frp-export`
- حذف کامل: `sudo frp-uninstall`

</td>
</tr>
</table>

---

## 🎯 موارد استفاده

### ۱. تجمیع پهنای‌باند
یک اتصال کلاینت را روی چند سرور خارج توزیع کنید:

```text
Client → Iran:443 → HAProxy → 6 کانال → Hetzner:443
                                     ├─→ Walter:443
                                     └─→ Azure:443
```

### ۲. مسیریابی چندمنطقه‌ای
پورت‌های عمومی مختلف را به سرورهای مختلف هدایت کنید:

```text
:443  ──► HAProxy ──► 6 کانال ──► Hetzner:443   (Xray)
:8443 ──► HAProxy ──► 4 کانال ──► Walter:8443   (Xray)
:2083 ──► 1 کانال   ──────────────► DigitalOcean:2083
:2087 ──► HAProxy ──► 3 کانال ──► Azure:2087
```

### ۳. دور زدن فایروال
از WebSocket یا QUIC برای دور زدن بازرسی عمیق بسته‌ها (DPI) استفاده کنید.

---

## 📖 فهرست مطالب

- [دانلود](#-دانلود)
- [ویژگی‌ها](#-ویژگی‌ها)
- [مفاهیم اصلی](#-مفاهیم-اصلی)
- [شروع سریع](#-شروع-سریع)
- [چیدمان منو](#-چیدمان-منو)
- [نصب](#-نصب)
- [استفاده](#-استفاده)
- [انواع پورت](#-انواع-پورت)
- [پروتکل‌ها](#-پروتکل‌ها)
- [ویزارد](#-ویزارد-ترکیبی)
- [خروجی و استقرار](#-خروجی--استقرار)
- [عیب‌یابی](#-عیب‌یابی)
- [ساختار فایل‌ها](#-ساختار-فایل‌ها)
- [نقشه راه](#-نقشه-راه)

---

## 🧠 مفاهیم اصلی

| اصطلاح     | معنی                                                      |
|------------|-----------------------------------------------------------|
| **Hub**    | سرور ایران (frps اینجا گوش می‌دهد)                        |
| **Node**   | سرور خارج (فرآیند frpc اینجا متصل می‌شود)                 |
| **Route**  | یک پورت عمومی روی Hub که به یک یا چند کانال نگاشت می‌شود  |
| **Channel**| یک تونل FRP تکی بین Hub و یک Node                         |

### حالت‌های Route

| حالت      | تعداد کانال | HAProxy | کاربرد                              |
|-----------|-------------|---------|-------------------------------------|
| Simple    | ۱           | ✗       | ترافیک سبک، راه‌اندازی سریع         |
| Balanced  | N (۲–۸)     | ✓       | پهنای‌باند بالا، HA، چند نود        |

---

## 🚀 شروع سریع

```bash
# ۱. نصب
sudo bash install.sh

# ۲. اجرا
sudo frp-cli

# ۳. استفاده از ویزارد (پیشنهادی)
# منوی [2] → حالت سریع → پاسخ به ۳ سؤال
```

یا از منوهای جداگانه استفاده کنید:

```text
[1] نصب FRP
[3] افزودن Node
[4] Route ساده  یا  [5] Route متوازن
[7] خروجی برای Node
[8] ورودی روی Node
[9] مدیریت کانال‌ها
```

---

## 📋 چیدمان منو

```text
  [ 1]  نصب FRP v0.71.0
  [ 2]  ویزارد (سریع)                  ← پیشنهادی
  [ 3]  مدیریت Node-ها
  [ 4]  ساخت Simple Route
  [ 5]  ساخت Balanced Route
  [ 6]  مدیریت Route-ها
  [ 7]  خروجی برای Node
  [ 8]  ورودی روی Node
  [ 9]  مدیریت Channel-ها
  [10]  تست سرعت
  [11]  بهینه‌سازی
  [12]  پشتیبان‌گیری
  [13]  ریست
  [14]  زبان (فینگلیش / انگلیسی)
  [15]  راهنما (Help)
  [16]  حالت راهنما [ON/OFF]
  [17]  نمایش IP [ON/OFF]
  [18]  حذف نصب
  [ 0]  خروج
```

### میانبرهای صفحه‌کلید

| کلید | عملکرد                              |
|------|-------------------------------------|
| F1   | راهنمای کامل                        |
| F2   | روشن/خاموش کردن حالت راهنما (نکات درون‌خطی) |
| F3   | تغییر زبان                          |
| F5   | تعویض مکان (ایران ↔ خارج)           |
| F7   | تغییر حالت پیشرفته/ساده منو         |
| F10  | خروج                                |
| h    | راهنمای منوی فعلی                   |
| 0    | بازگشت / خروج                       |

---

## 📦 نصب

### پیش‌نیازها
- اوبونتو ۲۲.۰۴ / ۲۴.۰۴ (همچنین دبیان ۱۲+)
- دسترسی root
- پایتون ۳.۱۰+
- حداقل ۱ گیگابایت رم و ۱ هسته CPU

### نصب خودکار

```bash
sudo bash install.sh
```

این دستور موارد زیر را انجام می‌دهد:
- ✅ نصب وابستگی‌های سیستم (curl، iperf3، ufw، haproxy و غیره)
- ✅ دانلود باینری‌های FRP v0.71.0 در `/usr/local/bin/`
- ✅ ساخت محیط مجازی پایتون در `/opt/frp-manager/venv`
- ✅ نصب پکیج پایتون
- ✅ ساخت entrypointها: `frp-manager`، `frp-cli`، `frp-tui`، `frp-export`، `frp-wizard`، `frp-uninstall`

### گزینه‌ها

```bash
sudo bash install.sh                # نصب کامل
sudo bash install.sh --cli          # فقط CLI
sudo bash install.sh --no-haproxy   # بدون HAProxy
sudo bash install.sh --upgrade      # ارتقا
sudo bash install.sh --uninstall    # حذف
```

---

## 🎮 استفاده

```bash
sudo frp-cli           # منوی کلاسیک CLI
sudo frp-manager       # لانچر هوشمند (سؤال CLI یا TUI)
sudo frp-wizard        # ویزارد مستقیم
sudo frp-uninstall     # منوی حذف نصب
sudo frp-export        # خروجی ZIP تمیز پروژه
sudo frp-tui           # TUI متنی (آزمایشی)
```

---

## 🔌 انواع پورت

| پورت    | مکان | تولیدکننده         | کاربرد                              |
|---------|------|--------------------|-------------------------------------|
| Entry   | Hub  | کاربر              | پورت عمومی (کاربر اینجا وصل می‌شود) |
| Bind    | Hub  | خودکار (۴۰۰۰۰–۶۵۰۰۰)| frps اینجا گوش می‌دهد               |
| Remote  | Node | خودکار (۲۰۰۰۰–۲۹۹۹۹)| frps اینجا expose می‌کند            |
| Target  | Node | کاربر              | سرویس Xray اینجا گوش می‌دهد         |
| iPerf   | هر دو| خودکار (۵۵۰۰۰–۵۹۹۹۹)| تست سرعت                            |

---

## 🌐 پروتکل‌ها

| پروتکل     | انتقال | بهترین برای                     |
|------------|--------|---------------------------------|
| TCP        | TCP    | سریع‌ترین و رایج‌ترین           |
| KCP        | UDP    | شبکه‌های پرپکت‌لاس              |
| QUIC       | UDP    | مدرن و پهنای‌باند بالا          |
| WebSocket  | TCP    | دور زدن فایروال / CDN           |

**پیشنهاد برای Routeهای متوازن:** ترکیب `۲× TCP + ۱× WS` برای هر نود.

---

## 🧙 ویزارد ترکیبی

ویزارد (منوی **[2]**) یک راه‌اندازی کامل را در یک جریان می‌سازد.

### حالت سریع

```text
گام ۱ ویزارد: 1 (سریع)
گام ۲ ویزارد:
  نام Node: Frankfurt-A
  آدرس Node: 1.2.3.4
گام ۳ ویزارد:
  پورت Entry: 443
  پورت Target: 443
  پروتکل: 1 (TCP)
  حالت: 2 (Balanced)
گام ۴ ویزارد: ایجاد؟ بله

→ Node + Route + ۳ کانال ساخته شد
→ فرانت‌اند HAProxy روی :443
→ همه سرویس‌های systemd راه‌اندازی شدند
→ فایل compact آماده برای import روی Node
```

### حالت سفارشی

کنترل کامل روی:
- نام، آدرس، مکان و یادداشت Node
- پورت Entry و Target
- حالت Route (Simple / Balanced)
- ترکیب پروتکل (مثلاً `tcp,tcp,ws`)

---

## 📤 خروجی و استقرار

### از Hub به Node

```bash
# روی Hub (ایران):
sudo frp-cli
# منوی [7] → انتخاب نود → کپی خروجی compact

# روی Node (خارج):
sudo frp-cli
# منوی [8] → چسباندن compact → خط خالی برای پایان
```

### خروجی کل پروژه

```bash
sudo frp-export
# → /root/frp-manager-clean-YYYYMMDD_HHMMSS.zip
```

فایل ZIP فقط شامل کد منبع است:

- ✅ `frp_manager/`، `pyproject.toml`، `install.sh`، `README.md`، `tests/`
- ❌ بدون `data/`، بدون `state.json`، بدون توکن، بدون IP، بدون لاگ، بدون venv

انتقال به سرور جدید:

```bash
# روی سرور قدیمی
sudo frp-export

# کپی به سرور جدید
scp /root/frp-manager-clean-*.zip root@NEW_SERVER:/root/

# روی سرور جدید
ssh root@NEW_SERVER
unzip frp-manager-clean-*.zip
cd frp-manager
sudo bash install.sh
sudo frp-cli
```

---

## 📸 تصاویر

### منوی اصلی

```text
╭─ ● IRAN — Inbound Server (frps) ─────────────────────────────╮
│   ✓  6 channel — 6 online                                     │
│   ✓  2 route tarif shode                                      │
│   ✓  HAProxy service ONLINE                                   │
╰───────────────────────────────────────────────────────────────╯

  [ 1]  Nasb FRP v0.71.0             [11]  Optimize
  [ 2]  Wizard (quick)               [12]  Backup
  [ 3]  Modiriyat Node-ha (2)        [13]  Reset (!)
  [ 4]  Sakht Simple Route (1 ch)    [14]  Zaban (fin)
  [ 5]  Sakht Balanced Route (N)     [15]  Rahnama
  [ 6]  Modiriyat Route-ha (2)       [16]  Help Mode [OFF]
  [ 7]  Export baraye Node           [17]  Show IP [ON]
  [ 8]  Import rooye Node →KHAREJ    [18]  Uninstall
  [ 9]  Modiriyat Channel-ha (6)     [19]  Switch →KHAREJ
  [10]  Speedtest                    [ 0]  Khoroj
```

### ویزارد

```text
╭─ ● IRAN — Wizard ─────────────────────────────────────────────╮
│                                                               │
│  eXtreme FRP  ·  Wizard                                       │
│  Multi-Protocol Tunnel Manager                                │
│                                                               │
│  ━━━ Step 3/4 ━━━  Tanzim-e Route                             │
│                                                               │
│  💡 Entry port chie?                                          │
│                                                               │
│  Port-e voroodi be server-e IRAN.                             │
│  Hamin porti ke user behesh vasl mishe.                       │
╰───────────────────────────────────────────────────────────────╯
```

---

## 🐛 عیب‌یابی

### CLI اجرا نمی‌شود

```bash
/opt/frp-manager/venv/bin/python -c "import frp_manager; print(frp_manager.__file__)"
# باید این را چاپ کند: /opt/frp-manager/frp_manager/__init__.py
```

اگر `/root/frp_manager/...` چاپ شد:

```bash
sudo rm -rf /root/frp_manager
cd /
sudo frp-cli
```

### باینری FRP موجود نیست

```bash
sudo frp-cli   # منوی [1] → نصب
# یا دستی
ls -la /usr/local/bin/frps /usr/local/bin/frpc
```

### سرویس‌ها راه‌اندازی نمی‌شوند

```bash
journalctl -u 'frps@ch-443-hetzner-01.service' -f
journalctl -u 'frpc@ch-443-hetzner-01.service' -f
journalctl -u haproxy-frp-agg.service -f
```

### کانفیگ HAProxy نامعتبر است

```bash
sudo frp-cli   # منوی [6] → بازسازی
# یا
haproxy -c -f /opt/frp-manager/data/haproxy/haproxy-agg.cfg
```

### ریست کامل همه چیز

```bash
sudo frp-cli   # منوی [13] → ریست کامل
# یا استفاده از منوی حذف نصب
sudo frp-uninstall
```

---

## 📁 ساختار فایل‌ها

### نصب‌شده روی سرور

```text
/opt/frp-manager/
├── frp_manager/              # پکیج پایتون
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                # منوی CLI
│   ├── config.py             # مقادیر پیش‌فرض
│   ├── constants.py
│   ├── models.py             # Node / Route / Channel
│   ├── state.py              # بارگذاری/ذخیره state.json
│   ├── frp/                  # سرور/کلاینت/compact FRP
│   ├── haproxy/              # کانفیگ و سرویس HAProxy
│   ├── system/               # شبکه، systemd، بهینه‌سازی
│   ├── i18n/                 # فینگلیش + انگلیسی
│   └── ui/                   # پرامپت‌ها، جداول، راهنما، ویزارد، حذف
├── data/                     # تمام داده‌های زمان اجرا
│   ├── state.json
│   ├── configs/
│   ├── haproxy/
│   ├── exports/
│   ├── backups/
│   └── logs/
├── venv/
├── install.sh
├── pyproject.toml
└── README.md
```

### یونیت‌های Systemd

```text
/etc/systemd/system/
├── frps@.service                # سرور FRP (Hub)
├── frpc@.service                # کلاینت FRP (Node)
└── haproxy-frp-agg.service      # تجمیع HAProxy
```

### Entrypointها

```text
/usr/local/bin/
├── frp-manager                  # لانچر هوشمند
├── frp-cli                      # میانبر CLI
├── frp-tui                      # میانبر TUI
├── frp-wizard                   # ویزارد مستقیم
├── frp-uninstall                # منوی حذف نصب
└── frp-export                   # خروجی تمیز پروژه
```

---

## 🧪 تست‌ها

```bash
cd /opt/frp-manager
venv/bin/pip install pytest
venv/bin/pytest tests/
```

---

## 🔐 نکات امنیتی

- تمام کانفیگ‌ها و توکن‌ها در `/opt/frp-manager/data/` قرار دارند
- دسترسی‌ها: پوشه `data/` فقط برای root قابل خواندن است
- **هرگز** فایل `data/state.json` را به اشتراک نگذارید — شامل تمام IP سرورها، توکن‌ها و مسیریابی است
- از `sudo frp-export` برای انتقال پروژه بدون داده‌ها استفاده کنید
- تمام دستورات پنل از توکن استفاده می‌کنند؛ پوشه `data/` را خصوصی نگه دارید

---

## 🗺 نقشه راه

- [x] CLI با معماری Route/Channel
- [x] تجمیع چندنودی HAProxy
- [x] رابط دو زبانه (فینگلیش / انگلیسی)
- [x] سیستم راهنما با نکات درون‌خطی
- [x] ویزارد ترکیبی
- [x] خروجی تمیز پروژه
- [x] منوی حذف نصب
- [x] میانبرهای کلید F (F1–F10)
- [x] حالت منوی پیشرفته / ساده
- [ ] TUI متنی (بازنویسی نسخه ۳)
- [ ] استقرار خودکار SSH روی نودها
- [ ] داشبورد وب
- [ ] به‌روزرسانی خودکار از GitHub

---

## 📄 مجوز

مجوز MIT — فایل [LICENSE](LICENSE) را ببینید.

---

## 💬 پشتیبانی

- 📖 راهنمای داخلی: `sudo frp-cli` → منوی **[15]**
- 🐛 گزارش باگ: [GitHub Issues](https://github.com/ExtremeDot/frp_manager/issues)
- 💡 درخواست ویژگی: [GitHub Issues](https://github.com/ExtremeDot/frp_manager/issues)
- 📝 لاگ‌ها: `/var/log/frp-manager-install.log`
- 🔧 سرویس‌ها: `systemctl status 'frps@*' 'frpc@*' haproxy-frp-agg.service`

---

## 🙏 قدردانی

- [FRP](https://github.com/fatedier/frp) — نرم‌افزار تونل پایه
- [HAProxy](https://www.haproxy.org/) — لودبالانسر
- [Rich](https://github.com/Textualize/rich) — فریم‌ورک رابط ترمینال
- [Textual](https://github.com/Textualize/textual) — فریم‌ورک TUI

<div align="center">

**ساخته‌شده با ❤️ برای استقرارهای FRP چندنودی با پهنای‌باند بالا**

[⬆ بازگشت به بالا](#-extreme-frp-manager-v30)

</div>
