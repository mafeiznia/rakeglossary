# Troubleshooting Guide

> راهنمای رفع مشکلات رایج در RakeGlossary.

**نسخه:** 0.1.0  
**آخرین به‌روزرسانی:** 2026-09-22

---

## فهرست

- [نصب و راه‌اندازی](#-نصب-و-راهاندازی)
- [Backend](#-backend)
- [Frontend](#-frontend)
- [پایپ‌لاین و پردازش](#-پایپلاین-و-پردازش)
- [LLM و ترجمه](#-llm-و-ترجمه)
- [دیتابیس و ذخیره‌سازی](#-دیتابیس-و-ذخیرهسازی)
- [CI/CD](#-cicd)
- [مشکلات خاص Windows / ARM64](#-مشکلات-خاص-windows--arm64)
- [گزارش باگ](#-گزارش-باگ)

---

## 🚀 نصب و راه‌اندازی

### ❌ `python: command not found`

**علت:** Python در PATH نیست یا نصب نشده.

**راه‌حل:**

```powershell
# چک کن Python 3.12 داری
py -3.12 --version

# اگر نداری، از microsoft.com/store یا python.org نصب کن
# حتماً "Add Python to PATH" را تیک بزن
```

### ❌ `node: command not found`

**علت:** Node.js نصب نیست یا PATH اشتباه است.

**راه‌حل:**

```powershell
node --version   # باید v20+ بدهد
npm --version
```

اگر نبود: از [nodejs.org](https://nodejs.org/) نسخه‌ی LTS را نصب کن.

### ❌ `pip install -e ".[dev]"` می‌شکند

**چند علت محتمل:**

1. **venv فعال نیست:**
   ```powershell
   # فعال کن
   ..\venv312\Scripts\activate
   # چک کن
   python -c "import sys; print(sys.executable)"
   # باید venv312\Scripts\python.exe بدهد
   ```

2. **`readme` در pyproject.toml به مسیر خارجی اشاره می‌کند:**
   ```
   DistutilsOptionError: Cannot access '../README.md'
   ```
   → در `backend/pyproject.toml`، `readme = "README.md"` باشد (نه `../README.md`).

3. **شبکه / پروکسی:**
   ```powershell
   pip install -e ".[dev]" --index-url https://pypi.org/simple/
   ```

### ❌ `python -m spacy download en_core_web_sm` fail

**علت:** گاهی روی شبکه‌های محدود یا ARM64 fail می‌شود.

**راه‌حل جایگزین:**

```powershell
# مستقیم از URL نصب کن
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

اگر باز هم fail داد → روی ARM64 از Conda استفاده کن:
```powershell
conda install -c conda-forge spacy
python -m spacy download en_core_web_sm
```

### ❌ `NLTK` نمی‌تواند دانلود کند

**علت:** firewall، پروکسی، یا محدودیت شبکه.

**راه‌حل:**

```powershell
# اجازه‌ی پروکسی
$env:NLTK_ALLOW_PROXIED_URLOPEN = "1"

# دانلود دستی
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

اگر باز fail داد → از [nltk_data GitHub](https://github.com/nltk/nltk_data) دستی دانلود کن و در `%APPDATA%\nltk_data` بگذار.

---

## 🐍 Backend

### ❌ `ModuleNotFoundError: No module named 'app'`

**علت:** از پوشه‌ی اشتباه اجرا می‌کنی یا venv فعال نیست.

**راه‌حل:**

```powershell
cd backend
python -c "from app.main import app; print('OK')"
```

اگر `OK` نداد:
- venv را فعال کن (`..\venv312\Scripts\activate`)
- `pip install -e ".[dev]"` را دوباره بزن

### ❌ `Port 8765 is already in use`

**علت:** یک backend دیگر در حال اجراست.

**راه‌حل:**

```powershell
# پیدا کن چه پروسه‌ای روی پورت است
Get-NetTCPConnection -LocalPort 8765 | Select-Object OwningProcess

# بکش
Get-Process python | Where-Object { $_.Path -like "*venv312*" } | Stop-Process -Force
```

### ❌ `pytest` command not found

**راه‌حل:**

```powershell
# به جای pytest
python -m pytest tests/ -v
```

### ❌ pytest fail روی تست‌های `test_services_runner_ai`

**علت‌های محتمل:**

1. **`retry: 1` در React Query hook:** فقط frontend را تحت تأثیر قرار می‌دهد
2. **density_target خیلی کوچک:** اگر متن تست کوتاه است، `_per_source_num_terms` فقط ۱ term می‌دهد
   - **راه‌حل:** در `_mk_project_ai`، مقدار `p.terms_per_1k_words = 500` بگذار
3. **`raise RuntimeError` در `_run_pipeline_ai` حذف شده:** بررسی کن بعد از cap، این بلوک وجود دارد:
   ```python
   if not merged_terms:
       raise RuntimeError("LLM could not extract any terms...")
   ```

### ❌ ruff / black / mypy fail

اگر بعد از `git pull` روی سیستمت fail می‌دهند ولی در CI پاس شده‌اند:

```powershell
# نسخه‌ها را همگام کن
pip install -e ".[dev]" --upgrade

# اجرای مجدد
ruff check app/
black --check app/
mypy app/
```

### ❌ `IndentationError: unindent does not match`

**علت:** Tab و Space مخلوط شده‌اند (معمولاً بعد از copy-paste).

**راه‌حل در VS Code:**
1. `Ctrl+Shift+P` → `Convert Indentation to Spaces`
2. عرض Tab را روی ۴ بگذار
3. فایل را ذخیره کن

---

## ⚛️ Frontend

### ❌ `Failed to resolve import "@/..."` در Vite

**علت:** alias `@` تعریف نشده یا config گم شده.

**چک کن:**

1. فایل `frontend/vite.config.ts` وجود دارد
2. **فقط یک فایل config** — نه `vite.config.js` و نه `vite.config.ts.txt`
   ```powershell
   Get-ChildItem vite.config.*
   ```
3. در `vite.config.ts`:
   ```ts
   resolve: {
     alias: {
       '@': path.resolve(process.cwd(), 'src'),
     },
   }
   ```
4. cache را پاک کن:
   ```powershell
   Remove-Item -Recurse -Force node_modules\.vite
   npm run dev
   ```

### ❌ `npm install` خیلی طول می‌کشد

**راه‌حل:**

```powershell
# از cache استفاده کن (اگر package-lock.json هست)
npm ci

# یا cache را پاک و دوباره نصب کن
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### ❌ `Missing key 'about.something'` در Console

**علت:** کلید i18n در `fa.ts` یا `en.ts` وجود ندارد.

**راه‌حل:**

کلید را در **هر دو** فایل اضافه کن:
```ts
// fa.ts
about: {
  myKey: 'متن فارسی',
}

// en.ts
about: {
  myKey: 'English text',
}
```

### ❌ صفحه Blank با `Uncaught SyntaxError: The requested module 'lucide-react' does not provide an export named 'Github'`

**علت:** Lucide (نسخه‌های جدید) آیکون‌های برند (Github, Twitter, Linkedin, Facebook) را حذف کرده.

**راه‌حل:** آیکون عمومی استفاده کن:
- `Github` → `Code`
- `Linkedin` → `Briefcase`
- `Twitter` → `AtSign`
- `Facebook` → `Users`

### ❌ CORS error در DevTools

**علت:** backend روی پورت اشتباه یا CORS در `main.py` تنظیم نشده.

**راه‌حل:**

1. مطمئن شو backend روی `http://127.0.0.1:8765` است
2. در `backend/app/main.py`، CORS middleware باید origins داشته باشد:
   ```python
   allow_origins=[
       "http://localhost:5173",
       "http://127.0.0.1:5173",
   ]
   ```

### ❌ Vitest تست‌ها را پیدا نمی‌کند

**علت:** `include` در `vitest.config.ts` اشتباه است.

**چک کن:**

```ts
test: {
  include: ['tests/**/*.{test,spec}.{ts,tsx}'],  // باید 'tests/' باشد
}
```

### ❌ `act(...)` warning در تست‌ها

**علت:** به‌روزرسانی state خارج از event system React.

**راه‌حل:** callback را در `act()` بپیچ:

```tsx
import { act } from '@testing-library/react'

act(() => {
  capturedCallbacks?.onEvent({ ... })
})
```

---

## ⚙️ پایپ‌لاین و پردازش

### ❌ پردازش تمام می‌شود ولی هیچ glossary entry ساخته نمی‌شود

**چند علت:**

1. **هیچ منبع معتبری وجود ندارد:**
   - چک کن همه‌ی sources `included=True` هستند
2. **`word_count` صفر است:**
   - PDF اسکن‌شده؟ → OCR لازم است (در نسخه‌ی فعلی پشتیبانی نمی‌شود)
   - فایل خالی است؟
3. **`terms_per_1k_words` خیلی کوچک:**
   - در Options Panel، مقدار density را بیشتر کن (پیش‌فرض ۱۵)
4. **`num_terms` خیلی کوچک:**
   - حداقل ۱۰۰ بگذار

### ❌ پردازش خیلی کند است

**علت‌ها:**

1. **spaCy روی ARM64 کندتر است:** طبیعی است
2. **متن خیلی طولانی:** برای کتاب‌های ۱۰۰۰+ صفحه، انتظار ۵-۱۵ دقیقه داشته باش
3. **Wikipedia lookup سری است:** هر term جداگانه فراخوانی می‌شود
4. **LLM mode کندتر از Offline است:** شبکه + provider latency

**راه‌حل:**
- از حالت `Hybrid` به جای `AI` استفاده کن (نصف هزینه و سریع‌تر)
- `num_terms` را کم کن
- منابع را split کن (چند پروژه‌ی کوچک)

### ❌ پردازش mid-way متوقف می‌شود

**راه‌حل:**

1. در UI روی دکمه‌ی **Stop** بزن
2. لاگ backend را چک کن:
   ```powershell
   Get-Content ..\data\logs\rakeglossary.log -Tail 50
   ```
3. اگر `CancelledError` دیدی → باگ در cancellation (گزارش بده)
4. اگر `MemoryError` دیدی → RAM کم است (کتاب خیلی بزرگ است)

---

## 🤖 LLM و ترجمه

### ❌ `Processing mode is 'ai' but no LLM provider is configured`

**راه‌حل:**

1. برو به **Settings → LLM**
2. **Enable** را روشن کن
3. Provider را انتخاب کن (OpenAI, OpenRouter, Gemini, GapGPT)
4. API Key را وارد کن
5. **Test** بزن تا مطمئن شو کار می‌کند
6. **Save** بزن

### ❌ LLM Test: `authentication failed`

**علت‌ها:**

1. **API Key اشتباه:** آن را از provider دوباره کپی کن
2. **Key منقضی شده:** key جدید بساز
3. **Provider اشتباه:** مطمئن شو key برای همان provider است (OpenAI key برای Gemini کار نمی‌کند)
4. **حساب بدون اعتبار:** در dashboard provider، credit را چک کن

### ❌ ترجمه خالی است

**علت:** `translate_terms=False` یا provider ترجمه تنظیم نشده.

**راه‌حل:**

1. در Options Panel، `Translate key terms to Persian` را تیک بزن
2. `Translation provider` را روی `Google` یا `LibreTranslate` بگذار
3. اگر از LibreTranslate استفاده می‌کنی، مطمئن شو server اجراست:
   ```powershell
   curl http://127.0.0.1:5000/languages
   ```

### ❌ `Argos model unavailable`

**علت:** مدل Argos برای EN→FA دانلود نشده.

**راه‌حل:**

```powershell
python -c "import argostranslate.package; argostranslate.package.update_package_index(); argostranslate.package.install_package('en', 'fa')"
```

---

## 💾 دیتابیس و ذخیره‌سازی

### ❌ دیتابیس خراب شده

**راه‌حل (با از دست دادن داده):**

```powershell
# backend را ببند
Stop-Process -Name python -Force

# دیتابیس را پاک کن
Remove-Item ..\data\rakeglossary.db

# backend را دوباره اجرا کن — دیتابیس خودکار ساخته می‌شود
scripts\dev-backend.bat
```

**⚠️ هشدار:** همه‌ی پروژه‌ها، منابع و واژه‌نامه‌ها از دست می‌روند.

### ❌ می‌خواهم schema را تغییر دهم (developer)

**راه‌حل فعلی (بدون Alembic):**

1. backend را ببند
2. دیتابیس را پاک کن
3. backend را دوباره اجرا کن
4. (اختیاری) پروژه‌ها را دوباره import کن

**راه‌حل آینده:** Alembic اضافه می‌شود (D.15+).

### ❌ فایل‌های آپلودشده کجا هستند؟

```
data/projects/{title}__{id8}/
```

مثال: `data/projects/My-Book__a1b2c3d4/`

### ❌ می‌خواهم کش ترجمه را پاک کنم

```powershell
Remove-Item -Recurse -Force data\cache\translations
```

---

## 🔄 CI/CD

### ❌ Backend CI fail با `Cannot access '../README.md'`

**علت:** در `backend/pyproject.toml`، `readme = "../README.md"` نوشته شده.

**راه‌حل:** به `readme = "README.md"` تغییر بده.

### ❌ CI fail با `spaCy model not found`

**علت:** مرحله‌ی `Download spaCy model` fail شده.

**راه‌حل:** در workflow، از URL مستقیم استفاده کن:
```yaml
- name: Download spaCy model
  run: |
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

### ❌ `Node.js 20 is deprecated` warning

**راه‌حل:** نسخه‌ی اکشن‌ها را bump کن:

- `actions/checkout@v4` → `@v5`
- `actions/setup-python@v5` → `@v6`
- `actions/setup-node@v4` → `@v6`

### ❌ می‌خواهم CI را دستی trigger کنم

در GitHub → Actions → workflow → **Run workflow** → شاخه را انتخاب کن.

---

## 🖥️ مشکلات خاص Windows / ARM64

### ❌ `spaCy` روی ARM64 نصب نمی‌شود

**علت:** wheel رسمی برای ARM64 وجود ندارد.

**راه‌حل:**

```powershell
# از Conda استفاده کن
conda install -c conda-forge spacy
python -m spacy download en_core_web_sm
```

یا از [spacy releases](https://github.com/explosion/spaCy/releases) source build کن.

### ❌ `pymupdf` روی ARM64 نصب نمی‌شود

**راه‌حل:** نسخه‌ی ۱.۲۸+ wheel برای `windows-arm64` دارد:

```powershell
pip install "pymupdf>=1.28"
```

اگر قدیمی‌تر است، ارتقا بده.

### ❌ مسیرهای طولانی در Windows

**علت:** Windows سقف 260 کاراکتر برای مسیر دارد.

**راه‌حل:**

1. پروژه را در مسیر کوتاه بگذار: `C:\dev\rakeglossary\` (نه `C:\Users\...\Projects\...\RakeGlossary\`)
2. یا Long Paths را فعال کن:
   ```powershell
   # در PowerShell as Admin
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

### ❌ فایل PDF فارسی در UI، متن خروجی mojibake است

**علت:** انکودینگ فایل اشتباه است.

**راه‌حل:** فایل را با UTF-8 ذخیره کن یا از `TxtExtractor` استفاده کن (که `charset_normalizer` دارد).

---

## 🐛 گزارش باگ

اگر راه‌حل بالا مشکلت را حل نکرد:

1. **نسخه را چک کن:** آیا روی آخرین `main` هستی؟
   ```powershell
   git log -1 --oneline
   ```
2. **لاگ را جمع کن:**
   ```powershell
   Get-Content data\logs\rakeglossary.log -Tail 100 > bug-report.log
   ```
3. **محیط را بنویس:** OS، Python، Node، نسخه‌ی مرورگر
4. **Issue باز کن:** [github.com/mafeiznia/rakeglossary/issues/new](https://github.com/mafeiznia/rakeglossary/issues/new)

از template `Bug report` استفاده کن و اطلاعات زیر را بده:

- **توضیح:** چه انتظاری داشتی؟ چه اتفاقی افتاد؟
- **مراحل بازتولید:** دقیقاً چطور می‌توانم مشکل را ببینم؟
- **محیط:** Windows 11 ARM64، Python 3.12.2، Node 24.16.0، Chrome 130
- **لاگ:** فایل `bug-report.log`
- **Screenshot:** اگر UI مشکل دارد

---

## 🔗 لینک‌های مفید

- [README](../README.md)
- [USER_GUIDE](USER_GUIDE.md)
- [DEVELOPER_GUIDE](DEVELOPER_GUIDE.md)
- [TESTING_GUIDE](TESTING_GUIDE.md)
- [GitHub Issues](https://github.com/mafeiznia/rakeglossary/issues)