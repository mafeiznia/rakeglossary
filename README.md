# RakeGlossary

> **تولیدکننده‌ی خودکار واژه‌نامه‌ی دو زبانه (انگلیسی → فارسی) از کتاب و متن**

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Node](https://img.shields.io/badge/node-24.x-green)
![License](https://img.shields.io/badge/license-MIT-green)

[![Backend CI](https://github.com/mafeiznia/rakeglossary/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/mafeiznia/rakeglossary/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/mafeiznia/rakeglossary/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/mafeiznia/rakeglossary/actions/workflows/frontend-ci.yml)

RakeGlossary یک اپلیکیشن دسکتاپ محلی است که فایل‌های PDF، DOCX، EPUB یا TXT را دریافت می‌کند، واژه‌های کلیدی متن را با ترکیبی از روش‌های NLP کلاسیک و هوش مصنوعی استخراج می‌کند، برای هر واژه تعریف می‌سازد و آن‌ها را به فارسی ترجمه می‌کند.

نتیجه یک واژه‌نامه‌ی ساختارمند است که می‌توانی در قالب‌های CSV، Excel یا TBX ذخیره کنی.

---

## فهرست

- [ویژگی‌ها](#-ویژگیها)
- [پشته فناوری](#-پشته-فناوری)
- [شروع سریع](#-شروع-سریع)
- [راهنمای استفاده](#-راهنمای-استفاده)
- [حالت‌های پردازش](#-حالتهای-پردازش)
- [تنظیمات](#-تنظیمات)
- [خروجی‌ها](#-خروجیها)
- [محل ذخیره‌سازی](#-محل-ذخیرهسازی)
- [ساختار پروژه](#-ساختار-پروژه)
- [مستندات بیشتر](#-مستندات-بیشتر)
- [نقشه راه](#-نقشه-راه)
- [مجوز](#-مجوز)

---

## ✨ ویژگی‌ها

### ورودی

- **آپلود فایل:** PDF، DOCX، EPUB، TXT
- **چند فایل در یک پروژه:** می‌توانی چند فصل را در یک پروژه بیاوری
- **ورود مستقیم متن:** برای متن‌های کوتاه یا محتوای کپی‌شده
- **اطلاعات کتاب‌شناختی:** عنوان، نویسنده، ژانر، تم‌ها، مخاطب هدف
  - ورود دستی از فرم
  - یا آپلود فایل JSON ساخته‌شده توسط سیستم دیگر

### استخراج واژه

- **حالت Offline:** spaCy (Noun Chunks + NER) + RAKE + YAKE
- **حالت AI:** استخراج مستقیم با LLM بر اساس پرامپت تخصصی ویراستار
- **Blacklist سراسری:** کلماتی که نمی‌خواهی در هیچ پروژه‌ای استخراج شوند
- **کنترل چگالی:** تعیین تعداد واژه بر اساس تعداد کلمات متن

### تعریف‌یابی

- **In-Text:** اگر کتاب خودش تعریف کرده باشد
- **Wikipedia:** برای اسامی خاص و مفاهیم عمومی
- **WordNet:** برای کلمات رایج (آفلاین)
- **LLM:** برای بهترین کیفیت (در حالت AI)

### ترجمه

- **Google Translate:** آنلاین، سرعت بالا
- **LibreTranslate:** خودمیزبان، آفلاین
- **Argos Translate:** کاملاً آفلاین روی سیستم
- **LLM:** با درک زمینه‌ی کتاب

### خروجی

- **CSV:** دو ستونه (term + translation) برای import سریع
- **XLSX:** کامل با ۱۳ ستون، آماده‌ی ویرایش در Excel
- **TBX:** استاندارد ISO برای ابزارهای CAT مثل memoQ و SDL Trados

### رابط کاربری

- **۵ تم رنگی:** Indigo Light, Emerald Light, Rose Light, Slate Dark, Midnight Dark
- **دو زبانه:** فارسی (RTL) و انگلیسی (LTR)
- **ویرایش درون‌خطی:** تغییر مستقیم سلول‌های جدول
- **لاگ زنده:** مشاهده‌ی لحظه‌به‌لحظه‌ی جریان پردازش
- **کنترل کامل:** توقف پردازش، حذف منبع، حذف واژه

### تاریخچه و ذخیره

- **ذخیره‌سازی محلی:** SQLite + فایل‌های پروژه در `data/`
- **لیست پروژه‌ها:** مرور، ادامه، حذف
- **خروجی‌های قبلی:** ذخیره‌ی خودکار فایل‌های export

---

## 🧰 پشته فناوری

### Backend

| بخش | فناوری |
|---|---|
| فریم‌ورک | FastAPI + Uvicorn |
| دیتابیس | SQLite + SQLAlchemy 2.0 |
| پردازش PDF | PyMuPDF |
| پردازش DOCX | python-docx |
| پردازش EPUB | ebooklib + BeautifulSoup |
| NLP | spaCy + NLTK + RAKE + YAKE |
| ترجمه | deep-translator + Argos Translate |
| LLM | OpenAI SDK (سازگار با OpenAI, OpenRouter, Gemini, GapGPT, DeepSeek, Groq) |
| لاگ | loguru |

### Frontend

| بخش | فناوری |
|---|---|
| فریم‌ورک | React 18 + TypeScript |
| Build | Vite |
| استایل | Tailwind CSS v4 + CSS variables |
| UI Primitives | Radix UI + shadcn/ui |
| State | Zustand + TanStack Query |
| جدول | TanStack Table (custom) |
| آیکون | Lucide React |
| Toast | Sonner |
| i18n | i18next + react-i18next |

### Desktop (آینده)

- **pywebview** برای پنجره‌ی بومی
- **PyInstaller** برای بسته‌بندی به `.exe`
- **Inno Setup** برای نصب‌کننده

---

## 🚀 شروع سریع

### پیش‌نیازها

- **Windows 10/11** (یا ARM64)
- **Python 3.12** — [دانلود](https://www.python.org/downloads/)
- **Node.js 20+** — [دانلود](https://nodejs.org/)
- **Git** (اختیاری)

### نصب

**۱. کلون یا دانلود پروژه:**

```cmd
git clone <repository-url> RakeGlossary
cd RakeGlossary
```

**۲. اجرای اسکریپت setup (یک‌بار):**

```cmd
scripts\setup.bat
```

این اسکریپت:
- venv مشترک در `..\venv312` می‌سازد
- وابستگی‌های backend را نصب می‌کند
- مدل spaCy (`en_core_web_sm`) را دانلود می‌کند
- داده‌های NLTK را دانلود می‌کند
- وابستگی‌های frontend را نصب می‌کند

**۳. اجرا:**

```cmd
scripts\dev.bat
```

دو پنجره باز می‌شود:
- **Backend:** `http://127.0.0.1:8765`
- **Frontend:** `http://localhost:5173`

برای پایان: هر دو پنجره را ببند.

### گزینه‌های جایگزین

```cmd
scripts\dev-backend.bat    # فقط backend
scripts\dev-frontend.bat   # فقط frontend
scripts\cmd.bat            # cmd تعاملی با venv فعال
```

---

## 📖 راهنمای استفاده

### جریان کامل در ۶ گام

**گام ۱: ساخت پروژه**

1. صفحه‌ی **خانه** (`/`) را باز کن
2. عنوان پروژه را وارد کن (مثلاً «کتاب فیزیک هالیدی»)
3. فایل‌ها را آپلود کن یا متن را پیست کن
4. (اختیاری) **اطلاعات کتاب** را باز کن و فیلدها را پر کن
5. روی **ایجاد و شروع پردازش** کلیک کن

**گام ۲: تنظیمات پردازش**

در صفحه‌ی پروژه:
1. **Process** را بزن تا OptionsPanel باز شود
2. حالت پردازش را انتخاب کن (Offline / AI / Hybrid)
3. چگالی واژگان و سقف کل را تنظیم کن
4. ترجمه را روشن/خاموش کن
5. **Start processing** را بزن

**گام ۳: مشاهده‌ی پیشرفت**

ProgressLog به‌صورت زنده نشان می‌دهد:
- استخراج از هر منبع
- ادغام و حذف تکراری‌ها
- تعریف‌یابی هر واژه
- ترجمه
- ذخیره

اگر خواستی متوقف کنی: روی **Stop** بزن.

**گام ۴: ویرایش واژه‌نامه**

در جدول نتایج:
- روی هر سلول کلیک کن → ویرایش کن → Enter
- Esc = لغو ویرایش
- 🚫 = افزودن به Blacklist (حذف + عدم استخراج در آینده)
- 🗑️ = حذف واژه از این پروژه

**گام ۵: خروجی گرفتن**

روی **CSV / Excel / TBX** کلیک کن → فایل دانلود می‌شود.

**گام ۶: بازگشت در جلسه‌ی بعد**

از `/projects` هر پروژه را می‌توانی باز کنی.

---

## 🎯 حالت‌های پردازش

| حالت | تعریف | ترجمه | هزینه |
|---|---|---|---|
| **Offline** | In-Text → Wikipedia → WordNet | Argos (آفلاین) | صفر |
| **Hybrid** | In-Text → Wikipedia → WordNet | LLM (با زمینه‌ی کتاب) | ~نصف AI |
| **AI** | LLM (استخراج + تعریف + ترجمه) | LLM (یکپارچه) | ~$0.01 per 100 terms |

### کدام را انتخاب کنم؟

- **Offline:** می‌خواهی سریع و رایگان باشد، کیفیت ترجمه‌ی Argos برایت کافی است.
- **Hybrid:** کیفیت ترجمه‌ی بهتر می‌خواهی ولی هزینه‌ی AI برایت زیاد است.
- **AI:** بهترین کیفیت ممکن (انتخاب واژه + تعریف + ترجمه) و هزینه‌اش هم اشکالی ندارد.

### نکته درباره‌ی AI

در حالت AI:
- LLM ابتدا **واژه‌ها + تعریف‌ها + context** را استخراج می‌کند (چانک به چانک)
- سپس **ترجمه** با پرامپت غنی‌شده با اطلاعات کتاب انجام می‌شود
- اگر **اطلاعات کتاب** پر شده باشد، کیفیت به‌طور محسوسی بالاتر می‌رود

---

## ⚙️ تنظیمات

### `/settings` → ظاهر

- **۵ تم رنگی:** انتخاب و ذخیره‌ی خودکار
- **دو زبان:** فارسی (RTL) / انگلیسی (LTR)

### `/settings` → هوش مصنوعی (LLM)

پشتیبانی از این Providerها (همه از SDK سازگار OpenAI استفاده می‌کنند):

| Provider | نوع کلید | لینک دریافت |
|---|---|---|
| OpenAI | `sk-...` | platform.openai.com/api-keys |
| OpenRouter | `sk-or-v1-...` | openrouter.ai/keys |
| Google Gemini | `AIza...` | aistudio.google.com/app/apikey |
| GapGPT | `sk-...` | gapgpt.app |
| DeepSeek | `sk-...` | platform.deepseek.com/api_keys |
| Groq | `gsk_...` | console.groq.com/keys |
| Custom | دلخواه | (OpenAI-compatible) |

دکمه‌ی **تست اتصال** صحت کلید و مدل را بررسی می‌کند.

### `/settings` → کلمات سیاهه

کلماتی که هرگز نباید استخراج شوند (فقط حروف انگلیسی).

مثال‌ها: `the`, `however`, `chapter`, `page`

---

## 📦 خروجی‌ها

### CSV (دوستونه)

```csv
English Term,Persian Term
Yumiko,یومیکو
Kagoshima,کاگوشیما
```

مناسب برای import در ابزارهایی که فقط جفت term+translation می‌خواهند.

### XLSX (۱۳ ستون)

```
# | English Term | Persian Term | Persian Alternatives |
Persian Transliteration | POS | Category | Context |
Translator Note | English Definition | Persian Definition |
Source | Score | Frequency
```

مناسب برای ویرایش دستی در Excel.

### TBX (ISO 30042)

فایل XML استاندارد که در ابزارهای CAT مثل memoQ و SDL Trados قابل import است.

---

## 💾 محل ذخیره‌سازی

```
RakeGlossary/
└─ data/
   ├─ rakeglossary.db          ← دیتابیس SQLite
   ├─ projects/                ← فایل‌های آپلودشده (به تفکیک پروژه)
   │  ├─ Book Title__abc12345/
   │  │  ├─ chapter1.pdf
   │  │  ├─ chapter2.docx
   │  │  └─ metadata.json
   │  └─ ...
   ├─ exports/                 ← فایل‌های خروجی موقت
   ├─ cache/                   ← کش ترجمه و LLM
   │  └─ translations/
   └─ logs/                    ← لاگ‌های چرخشی
      └─ rakeglossary.log
```

**نکته:** همه‌ی داده‌ها محلی هستند. هیچ چیزی به سرور خارجی نمی‌رود (به‌جز LLM/Translation providerهایی که خودت انتخاب می‌کنی).

---

## 📁 ساختار پروژه

```
RakeGlossary/
├─ backend/                    ← Python + FastAPI
│  ├─ app/
│  │  ├─ api/                  ← endpoints
│  │  ├─ core/                 ← config, logging, db
│  │  ├─ models/               ← SQLAlchemy models
│  │  ├─ schemas/              ← Pydantic schemas
│  │  ├─ services/             ← business logic
│  │  └─ pipeline/             ← پردازش اصلی
│  │     ├─ extractors/        ← PDF, DOCX, EPUB, TXT
│  │     ├─ nlp/               ← spaCy, RAKE, YAKE
│  │     ├─ definitions/       ← Wikipedia, WordNet, LLM
│  │     ├─ translation/       ← Google, LibreTranslate, Argos
│  │     └─ glossary.py        ← orchestrator
│  ├─ tests/                   ← pytest
│  └─ pyproject.toml
│
├─ frontend/                   ← React + TypeScript
│  ├─ src/
│  │  ├─ api/                  ← HTTP client
│  │  ├─ components/           ← UI components
│  │  ├─ features/             ← feature-specific
│  │  ├─ pages/                ← route pages
│  │  ├─ i18n/                 ← translations
│  │  ├─ types/                ← TypeScript types
│  │  └─ lib/                  ← helpers
│  ├─ index.html
│  └─ package.json
│
├─ scripts/                    ← batch files برای Windows
│  ├─ setup.bat
│  ├─ dev.bat
│  ├─ dev-backend.bat
│  ├─ dev-frontend.bat
│  └─ cmd.bat
│
├─ docs/                       ← مستندات
│  ├─ USER_GUIDE.md
│  ├─ ARCHITECTURE.md
│  ├─ DEVELOPER_GUIDE.md
│  └─ CHANGELOG.md
│
├─ data/                       ← داده‌های runtime (git-ignored)
├─ README.md                   ← این فایل
└─ LICENSE                     ← MIT
```

---

## 📚 مستندات بیشتر

| فایل | برای چه کسی |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | کاربران نهایی — راهنمای کامل فارسی |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | توسعه‌دهندگان — معماری و تصمیمات فنی |
| [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | توسعه‌دهندگان — setup، تست، build |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | تاریخچه‌ی تغییرات نسخه‌ها |

---

## 🗺 نقشه راه

### ✅ انجام‌شده (v0.1.0)

- [x] ورودی چند‌فایلی و متن مستقیم
- [x] استخراج NLP کلاسیک (spaCy + RAKE + YAKE + NER)
- [x] حالت AI (LLM برای استخراج + تعریف + ترجمه)
- [x] حالت Hybrid
- [x] اطلاعات کتاب + validation
- [x] Blacklist سراسری
- [x] سه Provider ترجمه
- [x] هفت Provider LLM
- [x] خروجی CSV / XLSX / TBX
- [x] ۵ تم رنگی + RTL/LTR
- [x] ProgressLog زنده (SSE)
- [x] ویرایش درون‌خطی
- [x] Stop/Cancel پردازش
- [x] Blacklist per-term

### 🚧 در برنامه

- [ ] بسته‌بندی ویندوز (`.exe`)
- [ ] LLM برای پالایش واژه‌نامه (Reflection)
- [ ] Translation Memory برای consistency بین پروژه‌ها
- [ ] Folder linking (خواندن مستقیم از پوشه)
- [ ] پشتیبانی از زبان‌های مقصد بیشتر

---

## 📜 مجوز

این پروژه تحت مجوز **MIT** منتشر می‌شود. برای جزئیات، فایل [LICENSE](LICENSE) را ببین.

---

## 🙏 تقدیر

- **spaCy** — برای NLP و NER
- **RAKE-NLTK** — برای استخراج واژه‌ی کلیدی
- **YAKE** — برای extraction آماری
- **Argos Translate** — برای ترجمه‌ی آفلاین
- **FastAPI** — برای API
- **React + Vite** — برای UI
- **shadcn/ui + Radix** — برای کامپوننت‌های پایه

---

<p align="center">
  ساخته‌شده با ❤️ برای مترجمان و ویراستاران فارسی
</p>