<div dir="rtl" markdown="1">
* markdown
# راهنمای جامع انتقال RakeGlossary به درایو External

> **هدف:** انتقال کامل و امن پروژه‌ی RakeGlossary از یک مسیر به درایو External (یا هر درایو دیگر) بدون از دست دادن داده، بدون شکستن محیط توسعه، و بدون خطاهای سخت‌قابل‌دیباگ.
>
> **نسخه:** 1.0.0  
> **تاریخ:** 2026-10-02  
> **مخاطب:** کاربر تک‌نفره‌ی RakeGlossary (dev + production)  
> **سازگاری:** Windows 10/11، درایوهای NTFS و exFAT، USB/Thunderbolt/SSD External

---

## 📑 فهرست

- [قانون طلایی](#قانون-طلایی)
- [چرا انتقال ساده کار نمی‌کند؟](#چرا-انتقال-ساده-کار-نمیکند)
- [فاز ۰: پیش‌نیازها](#فاز-۰-پیشنیازها)
- [فاز ۱: آماده‌سازی سیستم مبدأ](#فاز-۱-آمادهسازی-سیستم-مبدأ)
- [فاز ۲: بکاپ کامل](#فاز-۲-بکاپ-کامل)
- [فاز ۳: پاکسازی مبدأ](#فاز-۳-پاکسازی-مبدأ)
- [فاز ۴: انتقال](#فاز-۴-انتقال)
- [فاز ۵: تنظیم Git روی درایو جدید](#فاز-۵-تنظیم-git-روی-درایو-جدید)
- [فاز ۶: ساخت محیط Python](#فاز-۶-ساخت-محیط-python)
- [فاز ۷: ساخت محیط Node](#فاز-۷-ساخت-محیط-node)
- [فاز ۸: دانلود مدل‌های زبانی](#فاز-۸-دانلود-مدلهای-زبانی)
- [فاز ۹: تست backend و frontend](#فاز-۹-تست-backend-و-frontend)
- [فاز ۱۰: اجرای برنامه](#فاز-۱۰-اجرای-برنامه)
- [فاز ۱۱ (اختیاری): ساخت .exe](#فاز-۱۱-اختیاری-ساخت-exe)
- [فاز ۱۲: تأیید نهایی](#فاز-۱۲-تأیید-نهایی)
- [نکات مخصوص درایو External](#نکات-مخصوص-درایو-external)
- [مشکلات رایج و راه‌حل](#مشکلات-رایج-و-راهحل)
- [دستورالعمل سریع](#دستورالعمل-سریع)
- [پیوست: مسیر داده‌ها](#پیوست-مسیر-دادهها)

---

## قانون طلایی

> **هرگز این پوشه‌ها را کپی نکن:**
>
> - `.venv/`
> - `backend/.venv/`
> - `frontend/node_modules/`
> - `build/`، `dist/`، `backend/build/`، `backend/dist/`
> - هر پوشه‌ی `__pycache__/`، `.pytest_cache/`، `.mypy_cache/`، `.ruff_cache/`
> - `frontend/.vite/`
>
> **همه‌ی این‌ها باید از صفر روی درایو جدید ساخته شوند.**

اگر این قانون را رعایت کنی، ۹۰٪ دردسرهای انتقال حل می‌شود.

---

## چرا انتقال ساده کار نمی‌کند؟

پروژه‌ی RakeGlossary دو بخش دارد که هر دو **مسیرهای مطلق را ذخیره می‌کنند**:

### Backend (Python)

| مورد | چرا مشکل می‌شود | نشانه‌ی خرابی |
|---|---|---|
| `.venv/Scripts/python.exe` | مسیر Python اصلی در metadata داخلی | `python` کار می‌کند ولی importها resolve نمی‌شوند |
| `.venv/Scripts/pip.exe` | مسیر `site-packages` مبدأ hardcode | `pip install` می‌گوید موفق، ولی `pip list` خالی است |
| `.venv/Scripts/activate*` | مسیرهای مطلق در متغیرهای محیطی | `(.venv)` در prompt ظاهر می‌شود ولی `sys.prefix` غلط است |
| `.venv/pyvenv.cfg` | `home = C:\...\Python312` | مسیر مبدأ را نشان می‌دهد |
| `.venv/Lib/site-packages/*.pth` | مسیر `site-packages` مبدأ | importها resolve نمی‌شوند |
| `__pycache__/*.pyc` | مسیر مطلق فایل مبدأ | Python کد قدیمی را import می‌کند |
| `.pytest_cache/`, `.mypy_cache/` | cache با مسیر مطلق | lint/type/test نتایج نادرست |

### Frontend (Node.js)

| مورد | چرا مشکل می‌شود | نشانه‌ی خرابی |
|---|---|---|
| `node_modules/.bin/*` | symlink یا shim با مسیر مطلق | `npm run dev` خطای module not found |
| `node_modules/.vite/` | cache با hash و مسیر مطلق | Vite با خطای cache می‌افتد |
| `node_modules/.cache/` | cache پراکنده | build ناسازگار |
| `frontend/dist/` | خروجی Vite با مسیر مطلق | build قدیمی |

### Git

| مورد | چرا مشکل می‌شود | نشانه‌ی خرابی |
|---|---|---|
| `.git/index` | مسیرهای مطلق در بعضی entries | `git status` ممکن است فایل‌ها را "modified" ببیند |
| `.git/config` | remote origin (شبکه) | معمولاً مشکلی ندارد |
| روی درایو exFAT | ownership ذخیره نمی‌شود | `fatal: detected dubious ownership` |

### PyInstaller (اگر `.exe` داری)

| مورد | چرا مشکل می‌شود | نشانه‌ی خرابی |
|---|---|---|
| `build/` و `dist/` | مسیر مطلق bundle در `.exe` | `.exe` روی ماشین دیگر یا بعد از transfer crash می‌کند |

**نتیجه‌ی قطعی:** کپی ساده با Windows Explorer یا `Copy-Item` **کار نمی‌کند**. حتی `robocopy` هم اگر `venv` و `node_modules` را کپی کند، خراب می‌شود.

---

## فاز ۰: پیش‌نیازها

### روی سیستم مبدأ

* powershell
# نسخه‌ی Python
py -0p
* 

**انتظار:** باید `Python 3.12` در لیست باشد. این پروژه روی 3.12 تست شده — **نه 3.13، نه 3.14**.

* powershell
# نسخه‌ی Node.js
node --version    # انتظار: v20.x یا بالاتر
npm --version     # انتظار: 10.x یا بالاتر

# Git
git --version     # انتظار: 2.36 یا بالاتر

# نسخه‌ی پروژه
cd <مسیر پروژه>
git log -1 --oneline
git status --short   # باید خالی باشد (یا فقط تغییرات آگاهانه)
* 

### روی سیستم مقصد (اگر کامپیوتر دیگری است)

- **Python 3.12** نصب باشد
- **Node.js 20+** نصب باشد
- **Git** نصب باشد
- **درایو External** با فضای کافی (حداقل ۵ گیگابایت برای سورس + venv + node_modules)
- دسترسی به اینترنت برای دانلود dependencyها

### فضای مورد نیاز (تخمینی)

| بخش | فضا |
|---|---|
| سورس کد + git history | ~۱۰ مگابایت |
| `.venv` بعد از نصب | ~۴۰۰ مگابایت |
| `frontend/node_modules` | ~۳۰۰ مگابایت |
| spaCy model (`en_core_web_sm`) | ~۵۰ مگابایت |
| NLTK data | ~۳۰ مگابایت |
| `data/` (با پروژه‌های واقعی) | متغیر (۵-۱۰۰ مگابایت) |
| **مجموع پایه** | **~۸۰۰ مگابایت** |

اگر `.exe` هم بسازی، +۲۰۰-۵۰۰ مگابایت.

---

## فاز ۱: آماده‌سازی سیستم مبدأ

### ۱.۱. بستن همه‌ی پروسه‌ها

* powershell
# backend
Get-Process python, uvicorn, RakeGlossary -ErrorAction SilentlyContinue | Stop-Process -Force

# frontend
Get-Process node, npm -ErrorAction SilentlyContinue | Stop-Process -Force

# ترمینال‌های باز (اگر backend/frontend در حال اجراست)
Get-Process pwsh, powershell, cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*RakeGlossary*" } | Stop-Process -Force
* 

### ۱.۲. تأیید وضعیت git

* powershell
cd <مسیر پروژه>
git status
* 

**باید یکی از این‌ها باشد:**

- `nothing to commit, working tree clean` → می‌توانی ادامه بدهی
- چند تغییر commit نشده → **اول commit کن یا stash کن**

اگر می‌خواهی تغییرات نیمه‌کاره را نگه داری:

* powershell
git stash push -u -m "قبل از انتقال به درایو External"
* 

### ۱.۳. تأیید push آخرین کامیت‌ها

* powershell
git log origin/main..HEAD --oneline
* 

**اگر خطی برگشت** → کامیت‌های محلی‌ات push نشده‌اند:

* powershell
git push
* 

---

## فاز ۲: بکاپ کامل

**این مرحله را جدی بگیر.** انتقال همیشه ریسک دارد.

### ۲.۱. بکاپ داده‌ها (مهم‌ترین)

* powershell
# بکاپ DB
Copy-Item data\rakeglossary.db "<مسیر بکاپ>\rakeglossary.db.backup" -Force

# بکاپ پوشه‌ی projects (شامل فایل‌های PDF/DOCX/EPUB/TXT آپلودشده)
Copy-Item -Recurse data\projects "<مسیر بکاپ>\projects_backup" -Force

# بکاپ فایل‌های export (اگر مهم است)
Copy-Item -Recurse data\exports "<مسیر بکاپ>\exports_backup" -Force
* 

**مسیر بکاپ پیشنهادی:** `D:\Backups\RakeGlossary_<تاریخ>` یا یک درایو دیگر.

### ۲.۲. بکاپ تنظیمات

* powershell
# فایل .env (اگر داری)
Copy-Item .env "<مسیر بکاپ>\env.backup" -Force -ErrorAction SilentlyContinue

# تنظیمات VS Code (اگر داری)
Copy-Item -Recurse .vscode "<مسیر بکاپ>\vscode_backup" -Force -ErrorAction SilentlyContinue

# CLAUDE.md یا مستندات محلی
Copy-Item docs\*.md "<مسیر بکاپ>\docs_backup\" -Force -ErrorAction SilentlyContinue
* 

### ۲.۳. تأیید بکاپ

* powershell
Get-ChildItem "<مسیر بکاپ>" -Recurse | Measure-Object -Property Length -Sum
* 

باید حجم معقولی ببینی (چند ده مگابایت اگر پروژه‌های واقعی داری).

### ۲.۴. بکاپ از git (اختیاری ولی توصیه‌شده)

* powershell
# کل ریپو به‌صورت bare (کامل با history)
git clone --mirror . "<مسیر بکاپ>\rakeglossary.git"

# یا فقط چک کن remote به‌روز است
git fetch --all
git log origin/main -1 --oneline
* 

---

## فاز ۳: پاکسازی مبدأ

### ۳.۱. پاک کردن venv (اگر در ریشه است)

* powershell
cd <مسیر پروژه>
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
* 

### ۳.۲. پاک کردن node_modules

* powershell
Remove-Item -Recurse -Force frontend\node_modules -ErrorAction SilentlyContinue
* 

### ۳.۳. پاک کردن build artifacts

* powershell
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force frontend\dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force frontend\.vite -ErrorAction SilentlyContinue
* 

### ۳.۴. پاک کردن Python caches

* powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter ".mypy_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter ".ruff_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
* 

### ۳.۵. پاک کردن لاگ‌ها و فایل‌های موقت

* powershell
Remove-Item backend\install-log.txt -ErrorAction SilentlyContinue
Remove-Item backend\nohup.out -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include "*.log" -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "data\\logs" } | Remove-Item -Force
* 

**⚠️ نکته:** `data/logs/` را پاک نکن — لاگ‌های تاریخی ممکن است ارزشمند باشند.

### ۳.۶. تأیید پاکسازی

* powershell
# هیچ کدام نباید وجود داشته باشند
Test-Path .venv               # False
Test-Path frontend\node_modules  # False
Test-Path build               # False
Test-Path dist                # False

# این‌ها باید باشند
Test-Path data\rakeglossary.db   # True (اگر DB داری)
Test-Path .git                   # True
Test-Path backend\pyproject.toml # True
* 

### ۳.۷. Git status بعد از پاکسازی

* powershell
git status
* 

**انتظار:** `nothing to commit, working tree clean` یا فقط تغییرات کوچک (مثل `.gitignore`).

اگر چیزی unexpected دیدی (مثل فایل‌های tracked که حذف شده‌اند)، با `git checkout -- <file>` بازگردان:

* powershell
git restore .
git status
* 

---

## فاز ۴: انتقال

### ۴.۱. انتخاب روش

| روش | مزیت | عیب | توصیه برای |
|---|---|---|---|
| `robocopy` | سریع، resistent، فلگ‌های زیاد | سینتکس قدیمی | **توصیه‌شده** |
| `Copy-Item` | ساده | کند، بدون resume | پروژه‌های کوچک |
| Windows Explorer | گرافیکی | کند، بدون کنترل | پروژه‌های خیلی کوچک |
| 7-Zip | فشرده، قابل حمل | نیاز به extract دو بار | انتقال بین کامپیوتر |

### ۴.۲. انتقال با robocopy (توصیه‌شده)

* powershell
# مثال: از C: به G:
robocopy "C:\projects\Translation\RAKE\RakeGlossary" "G:\Projects\Translation\RakeGlossary" /E /COPYALL /DCOPY:T /R:3 /W:2 /MT:8 /XF "*.log" "install-log.txt" /XD "node_modules" ".venv" "build" "dist" "__pycache__" ".pytest_cache" ".mypy_cache" ".ruff_cache" ".vite"
* 

**توضیح فلگ‌ها:**

| فلگ | کار |
|---|---|
| `/E` | همه‌ی زیرپوشه‌ها (حتی خالی‌ها) |
| `/COPYALL` | همه‌ی attributeها (timestamps, ACL, owner) |
| `/DCOPY:T` | timestamp پوشه‌ها را هم کپی کن |
| `/R:3` | سه بار retry در خطا |
| `/W:2` | دو ثانیه بین retryها |
| `/MT:8` | ۸ ترد موازی (سریع‌تر) |
| `/XF` | exclude files (فایل‌های log) |
| `/XD` | exclude directories (venv, node_modules, build, cache) |

### ۴.۳. تأیید انتقال

* powershell
# مقایسه تعداد فایل‌ها
(Get-ChildItem "C:\projects\Translation\RAKE\RakeGlossary" -Recurse -File | Measure-Object).Count
(Get-ChildItem "G:\Projects\Translation\RakeGlossary" -Recurse -File | Measure-Object).Count
* 

**باید نزدیک به هم باشند** (تفاوت فقط به خاطر فایل‌های exclude شده).

* powershell
# چک فایل‌های کلیدی
Test-Path "G:\Projects\Translation\RakeGlossary\.git"                     # True
Test-Path "G:\Projects\Translation\RakeGlossary\backend\pyproject.toml"    # True
Test-Path "G:\Projects\Translation\RakeGlossary\frontend\package.json"     # True
Test-Path "G:\Projects\Translation\RakeGlossary\data\rakeglossary.db"      # True (اگر DB داری)
* 

### ۴.۴. (اختیاری) نگه‌داشتن مبدأ

اگر می‌خواهی مبدأ را هم داشته باشی، **الان پاکش نکن**. فقط یادت باشد:

- **دو نسخه را همزمان اجرا نکن** (data و DB diverge می‌شوند)
- اگر یکی را dev می‌کنی، دیگری را فقط برای خواندن/بکاپ نگه دار

---

## فاز ۵: تنظیم Git روی درایو جدید

### ۵.۱. رفع خطای safe.directory

**اولین چیزی که می‌بینی:**

* 
fatal: detected dubious ownership in repository at 'G:/...'
'G:/...' is on a file system that does not record ownership
* 

**علت:** درایوهای External روی exFAT یا NTFS بدون ACL فرمت شده‌اند. Git از این می‌ترسد که فایل‌ها توسط کاربر دیگری تغییر کرده باشند.

**راه‌حل — گزینه ۱ (امن‌تر، مسیر خاص):**

* powershell
git config --global --add safe.directory G:/Projects/Translation/RakeGlossary
* 

**راه‌حل — گزینه ۲ (راحت‌تر، wildcard):**

* powershell
git config --global --add safe.directory "*"
* 

**توصیه:** wildcard. چون:

- اگر حرف درایو عوض شود (`G:` → `H:`)، دوباره درگیر نمی‌شوی
- اگر مسیر را جابجا کنی، دوباره درگیر نمی‌شوی
- برای پروژه‌ی شخصی، ریسک امنیتی معنی‌داری ندارد

### ۵.۲. تأیید

* powershell
cd G:\Projects\Translation\RakeGlossary
git status --short
git log -1 --oneline
git remote -v
git config --global --get-all safe.directory
* 

**انتظار:**

- `git status` بدون خطا کار کند
- آخرین commit را نشان دهد
- remote درست باشد (`https://github.com/mafeiznia/rakeglossary.git`)
- `safe.directory` شامل مسیر جدید یا `*` باشد

### ۵.۳. اگر خطای دیگری دیدی

**`fatal: not a git repository`:**

* powershell
# چک کن .git وجود دارد
Test-Path .git
* 

اگر `False`، یعنی `robocopy` آن را کپی نکرده. از بکاپ بازیابی کن:

* powershell
Copy-Item -Recurse "<مسیر بکاپ>\rakeglossary.git" .git
git status
* 

---

## فاز ۶: ساخت محیط Python

### ۶.۱. ساخت venv از صفر

* powershell
cd G:\Projects\Translation\RakeGlossary

# ساخت با Python 3.12 (صریح — پیش‌فرض سیستم ممکن است 3.14 باشد)
py -3.12 -m venv .venv
* 

**اگر `py -3.12` پیدا نشد:**

* powershell
# مسیر Python 3.12 را پیدا کن
py -0p

# یا مستقیم از مسیر
& "C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
* 

**زمان تخمینی:** ۱۰-۳۰ ثانیه (بسته به سرعت درایو).

### ۶.۲. فعال‌سازی

* powershell
.venv\Scripts\Activate.ps1
* 

**اگر execution policy خطا داد:**

* powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# بعد دوباره فعال‌سازی کن
* 

**انتظار:** پرامپت `(.venv)` را نشان بدهد.

### ۶.۳. تأیید ساخت درست

* powershell
python -c "import sys; print(sys.executable); print(sys.prefix)"
* 

**انتظار:**

* 
G:\Projects\Translation\RakeGlossary\.venv\Scripts\python.exe
G:\Projects\Translation\RakeGlossary\.venv
* 

**⚠️ اگر مسیر `C:` یا `AppData` را نشان داد** → venv خراب است. حذف و دوباره بساز:

* powershell
deactivate
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
* 

### ۶.۴. آپدیت pip

* powershell
# همیشه با python -m pip، نه pip خالی
python -m pip install --upgrade pip
* 

**💡 چرا `python -m pip`؟** — اگر venv کپی‌شده باشد، `pip.exe` مسیر مبدأ را hardcode دارد. ولی `python -m pip` از `sys.executable` استفاده می‌کند که همیشه درست است.

### ۶.۵. نصب dependencies backend

* powershell
cd backend

# نصب editable با dev extras
python -m pip install -e ".[dev]"
* 

**زمان تخمینی:** ۵-۱۵ دقیقه (همه چیز از صفر دانلود می‌شود).

**انتظار در انتها:**

* 
Successfully installed fastapi-X.X.X uvicorn-X.X.X alembic-X.X.X black-X.X.X ... (~85 package)
* 

### ۶.۶. تأیید نصب

* powershell
python -m pip list | Select-String "fastapi|uvicorn|sqlalchemy|pydantic|pytest|spacy|nltk"
* 

باید این‌ها را ببینی:

* 
fastapi
uvicorn
sqlalchemy
pydantic
pytest
spacy
nltk
...
* 

**⚠️ اگر `pip list` فقط `pip` را نشان داد** → venv کپی‌شده است. برو به بخش [Troubleshooting: pip list خالی](#-pip-میگوید-نصب-شد-ولی-pip-list-خالی-است).

### ۶.۷. (اختیاری) ذخیره‌ی لاگ نصب

اگر خواستی خروجی نصب را ذخیره کنی:

* powershell
python -m pip install -e ".[dev]" 2>&1 | Tee-Object -FilePath install-log.txt
* 

**نکته:** ممکن است PowerShell خطای زیر بدهد:

* 
pip : At line:1 char:1
+ CategoryInfo : NotSpecified: (:String) [], RemoteException
+ FullyQualifiedErrorId : NativeCommandError
* 

**این خطا بی‌ضرر است** — pip روی stderr چیزی نوشته (مثل notice آپدیت)، PowerShell آن را به عنوان خطا تفسیر کرده. نصب انجام شده.

**⚠️ فایل `install-log.txt` را در `.gitignore` بگذار یا پاکش کن تا در `git status` ظاهر نشود.**

---

## فاز ۷: ساخت محیط Node

### ۷.۱. رفتن به frontend

* powershell
cd ..\frontend
* 

### ۷.۲. نصب node_modules

* powershell
npm install
* 

**زمان تخمینی:** ۲-۵ دقیقه (بسته به سرعت درایو و اینترنت).

**انتظار در انتها:**

* 
added 300+ packages, and audited ...
found 0 vulnerabilities
* 

**⚠️ اگر خطاهای deprecated یا warning دیدی، معمولاً بی‌ضرر هستند.**

### ۷.۳. تأیید نصب

* powershell
Test-Path node_modules
Test-Path node_modules\.bin\vite
Test-Path node_modules\react
* 

**همه باید `True` باشند.**

### ۷.۴. (اختیاری) تأیید Vite

* powershell
npx vite --version
* 

باید نسخه‌ی Vite را نشان بدهد.

---

## فاز ۸: دانلود مدل‌های زبانی

### ۸.۱. spaCy English model

* powershell
cd ..\backend
python -m spacy download en_core_web_sm
* 

**انتظار:**

* 
✔ Download and installation successful
You can now load the package via spacy.load('en_core_web_sm')
* 

**تأیید:**

* powershell
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('OK')"
* 

باید `OK` چاپ کند.

### ۸.۲. NLTK data

* powershell
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
* 

**انتظار:**

* 
[nltk_data] Downloading package stopwords to C:\Users\<user>\AppData\Roaming\nltk_data...
[nltk_data]   Unzipping corpora/stopwords.zip.
[nltk_data] Downloading package punkt to ...
...
* 

**تأیید:**

* powershell
python -c "import nltk; nltk.data.find('corpora/stopwords'); nltk.data.find('tokenizers/punkt'); print('OK')"
* 

باید `OK` چاپ کند.

### ۸.۳. اگر پشت proxy یا محدودیت شبکه هستی

**spaCy:**

از [github.com/explosion/spacy-models/releases](https://github.com/explosion/spacy-models/releases) فایل `.whl` مربوط به `en_core_web_sm` را دانلود کن و:

* powershell
python -m pip install <file>.whl
* 

**NLTK:**

از [nltk.org/nltk_data](https://www.nltk.org/nltk_data/) دستی دانلود کن و در مسیر زیر بگذار:

* 
%APPDATA%\nltk_data\
├── corpora\
│   └── stopwords\
└── tokenizers\
    ├── punkt\
    └── punkt_tab\
* 

---

## فاز ۹: تست backend و frontend

### ۹.۱. تست backend

* powershell
# مطمئن شو در backend هستی
pwd   # انتظار: G:\Projects\Translation\RakeGlossary\backend

python -m pytest tests/ -q
* 

**انتظار:**

* 
225 passed in 41.34s
* 

**اگر تعداد pass کمتر بود یا fail داشت:**

| خطا | علت | راه‌حل |
|---|---|---|
| `ImportError: No module named spacy` | spaCy نصب نیست | `python -m pip install -e ".[dev]"` |
| `OSError: [E050] Can't find model 'en_core_web_sm'` | مدل spaCy دانلود نشده | مرحله ۸.۱ |
| `LookupError: punkt not found` | NLTK data دانلود نشده | مرحله ۸.۲ |
| `sqlite3.OperationalError: no such table` | DB کپی نشده یا خراب | `data/` را از بکاپ بازیابی کن |
| `FileNotFoundError` برای fixture | data/ ناقص | بکاپ را بررسی کن |

### ۹.۲. تست frontend

* powershell
cd ..\frontend
npm test
* 

**انتظار:** همه‌ی تست‌ها pass.

**⚠️ اگر `npm test` خطا داد که "script not found":**

* powershell
# چک کن package.json اسکریپت test دارد
Get-Content package.json | Select-String '"test"'
* 

اگر ندارد، فقط `npm run build` را اجرا کن برای تأیید.

### ۹.۳. (اختیاری) Lint و Type check

* powershell
cd ..\backend

# ruff
ruff check app/

# black
black --check app/

# mypy
mypy app/
* 

**انتظار:** همه بدون خطا.

---

## فاز ۱۰: اجرای برنامه

### ۱۰.۱. Backend (ترمینال ۱)

* powershell
cd G:\Projects\Translation\RakeGlossary\backend
.venv\Scripts\Activate.ps1   # اگر فعال نیست
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
* 

**انتظار:**

* 
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
* 

**تست سریع:**

مرورگر: http://127.0.0.1:8765/api/health

**انتظار:** یک JSON مثل `{"status": "ok", "version": "0.1.0"}`.

### ۱۰.۲. Frontend (ترمینال ۲)

* powershell
cd G:\Projects\Translation\RakeGlossary\frontend
npm run dev
* 

**انتظار:**

* 
  VITE vX.X.X  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
* 

### ۱۰.۳. تست در مرورگر

مرورگر: http://localhost:5173/

**انتظار:**

- صفحه‌ی خانه‌ی RakeGlossary بالا بیاید
- پروژه‌های قبلی (اگر DB کپی شده) نمایش داده شوند
- منوی Settings کار کند
- حداقل یک پروژه‌ی جدید بساز و process کن

**اگر همه‌چیز کار کرد → انتقال موفق.** ✅

### ۱۰.۴. (اختیاری) اجرای خودکار

اگر می‌خواهی هر دو سرویس را یکجا اجرا کنی:

* powershell
cd G:\Projects\Translation\RakeGlossary
scripts\dev.bat
* 

**انتظار:** دو پنجره‌ی جدید باز شود — یکی backend، یکی frontend.

---

## فاز ۱۱ (اختیاری): ساخت .exe

اگر نسخه‌ی `.exe` هم می‌خواهی، **همیشه از صفر build کن**. `dist/` قبلی مسیرهای مطلق مبدأ را در bundle PyInstaller دارد.

### ۱۱.۱. Build frontend

* powershell
cd G:\Projects\Translation\RakeGlossary
cd frontend
npm run build
cd ..
* 

**انتظار:** پوشه‌ی `frontend/dist/` ساخته شود.

### ۱۱.۲. پاک کردن build قبلی (اگر مانده)

* powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
* 

### ۱۱.۳. Build PyInstaller

* powershell
pyinstaller desktop\build.spec --clean --noconfirm
* 

**زمان تخمینی:** ۳-۱۰ دقیقه.

**انتظار:**

* 
INFO: Building COLLECT ...
INFO: Building EXE from EXE-00.toc ...
INFO: Copying DLLs ...
Building EXE from EXE-00.toc completed successfully.
* 

### ۱۱.۴. تست .exe

* powershell
cd dist\RakeGlossary
.\RakeGlossary.exe
* 

**انتظار:** پنجره‌ی desktop باز شود، UI کار کند.

**⚠️ نکته:** در حالت `.exe`، داده‌ها در `%APPDATA%\RakeGlossary\data\` ذخیره می‌شوند، **نه** در پروژه. این یعنی:

- DB و data جدا از پروژه‌اند
- انتقال پروژه به درایو دیگر، این‌ها را دست نمی‌زند
- اگر می‌خواهی data جابجا شود، `%APPDATA%\RakeGlossary\` را کپی کن

### ۱۱.۵. (اختیاری) ساخت installer با Inno Setup

اگر Inno Setup نصب است:

* powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
* 

**خروجی:** `dist\installer\RakeGlossary-Setup-0.1.0.exe`

---

## فاز ۱۲: تأیید نهایی

### چک‌لیست کامل

* 
✅ انتقال
  □ فایل‌های پروژه در مسیر جدید کپی شده
  □ .git کپی شده و git status کار می‌کند
  □ data/rakeglossary.db سالم است
  □ data/projects/ (اگر داری) کامل است

✅ Git
  □ git status بدون خطا کار می‌کند
  □ git log -1 آخرین commit را نشان می‌دهد
  □ git remote -v درست است
  □ safe.directory تنظیم شده

✅ Python
  □ .venv در مسیر جدید ساخته شده (نه کپی)
  □ python -c "import sys; print(sys.executable)" مسیر جدید را نشان می‌دهد
  □ python -m pip list پکیج‌ها را نشان می‌دهد
  □ python -m spacy validate → OK
  □ python -c "import nltk; nltk.data.find('corpora/stopwords')" → OK

✅ تست backend
  □ python -m pytest tests/ -q → 225 passed
  □ ruff check app/ → All checks passed
  □ black --check app/ → All done
  □ mypy app/ → Success

✅ Node
  □ node_modules نصب شده
  □ npm test همه pass
  □ (اختیاری) npm run build موفق

✅ اجرا
  □ backend روی 8765 بالا می‌آید
  □ frontend روی 5173 بالا می‌آید
  □ UI در مرورگر کار می‌کند
  □ می‌توان یک پروژه‌ی جدید ساخت و process کرد

✅ (اختیاری) .exe
  □ dist/RakeGlossary/RakeGlossary.exe ساخته شده
  □ .exe اجرا می‌شود و UI کار می‌کند
  □ (اختیاری) installer ساخته شده
* 

---

## نکات مخصوص درایو External

### سرعت

| اتصال | تجربه |
|---|---|
| **USB 3.0+ / USB-C** | سرعت خوب، تجربه‌ی عادی |
| **USB 2.0** | `npm install` و `pip install` ۳-۵ برابر کندتر |
| **Thunderbolt 3/4** | تقریباً معادل SSD داخلی |
| **HDD External (نه SSD)** | `pytest` و `npm run build` کند می‌شوند |

**توصیه:** اگر درایو HDD است و پروژه بزرگ می‌شود، SSD External را در نظر بگیر.

### قطع ناگهانی

**قبل از قطع درایو:**

* powershell
# بستن همه‌ی پروسه‌های Python/Node
Get-Process python, node, uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force

# خروج از venv
deactivate
* 

بعد از بستن، از **"Safely Remove Hardware"** استفاده کن (آیکون در system tray).

**اگر درایو وسط کار قطع شود:**

| خرابی | راه‌حل |
|---|---|
| venv خراب | حذف و بازسازی (فاز ۶) |
| node_modules خراب | `Remove-Item node_modules -Recurse -Force; npm install` |
| DB خراب | از بکاپ بازیابی |
| git index خراب | `git reset --mixed HEAD` |

### مسیر طولانی (Windows MAX_PATH)

Windows سقف **260 کاراکتر** برای مسیر دارد.

**مثال مسیر مشکل‌دار:**

* 
G:\Projects\Translation\RakeGlossary\frontend\node_modules\@some-org\some-package\node_modules\another-package\lib\components\...
* 

**راه‌حل ۱ — فعال‌سازی Long Paths (توصیه‌شده):**

PowerShell با Admin:

* powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
* 
* 
بعد **ریستارت کن**.

**راه‌حل ۲ — مسیر کوتاه‌تر:**

پروژه را در مسیر کوتاه بگذار:

* 
G:\RG\
* 

یا از `subst` استفاده کن:

* powershell
subst X: "G:\Projects\Translation\RakeGlossary"
cd X:\backend
* 

**راه‌حل ۳ — npm با تنظیمات کوتاه‌تر:**

* powershell
npm config set cache "G:\npm-cache" --global
npm config set prefix "G:\npm-global" --global
* 

### همزمان dev روی دو درایو

**توصیه نمی‌شود.** چرا؟

- Database و data در دو جا diverge می‌شوند
- اگر در یکی پروژه بسازی، در دیگری نمی‌بینی
- git status در دو جا متفاوت می‌شود
- اگر یک کامیت کنی، در دیگری نیست

**اگر مجبوری:**

- یکی را read-only نگه‌دار
- یا از یک DB مشترک (مثل Postgres remote) استفاده کن
- یا sync دستی بین دو نسخه

### Sync با Cloud (OneDrive, Dropbox, Google Drive)

**نکن.** دلایل:

1. Cloud sync در وسط کار، `.venv` و `node_modules` را همزمان sync می‌کند → خرابی
2. فایل‌های قفل‌شده (مثل DB SQLite) sync نمی‌شوند درست
3. `.git` با sync، conflict می‌سازد

**اگر واقعاً می‌خواهی sync کنی:**

- فقط سورس کد را sync کن (با `.gitignore` برای `venv`/`node_modules`)
- هرگز `.venv`, `node_modules`, `.git`, `data/` را sync نکن
- بعد از sync روی ماشین دیگر، مراحل فاز ۶ و ۷ را تکرار کن

### BitLocker / رمزنگاری

اگر درایو BitLocker دارد:

- سرعت کمی کندتر
- بعد از قفل شدن، دسترسی قطع می‌شود → پروسه‌ها crash می‌کنند

**توصیه:** اگر BitLocker فعال است، از قفل خودکار در حین کار جلوگیری کن (تنظیمات BitLocker).

### NTFS vs exFAT

| ویژگی | NTFS | exFAT |
|---|---|---|
| **سرعت** | کمی سریع‌تر | کمی کندتر |
| **سازگاری Windows** | کامل | کامل |
| **سازگاری macOS** | فقط read | read/write |
| **سازگاری Linux** | بله | بله |
| **Permission (ACL)** | پشتیبانی | ندارد |
| **Git safe.directory** | معمولاً نیاز است | همیشه نیاز است |

**توصیه:** اگر فقط با Windows کار می‌کنی، NTFS. اگر با macOS هم کار می‌کنی، exFAT.

---

## مشکلات رایج و راه‌حل

### ❌ `fatal: detected dubious ownership in repository`

**علت:** درایو External بدون ownership.

**راه‌حل:**

* powershell
git config --global --add safe.directory "*"
* 

### ❌ `pip` می‌گوید نصب شد ولی `pip list` خالی است

**نشانه‌ها:**

- `pip install` پیام `Successfully installed rakeglossary` می‌دهد
- ولی `python -m pip list` فقط `pip` را نشان می‌دهد
- یا pip notice هنوز مسیر `C:\...` را نشان می‌دهد

**علت:** `.venv` کپی‌شده (نه ساخته‌شده).

**تشخیص قطعی:**

* powershell
# چک کن site-packages در G: خالی است یا پر
Get-ChildItem "G:\Projects\Translation\RakeGlossary\.venv\Lib\site-packages" -Directory | Select-Object -First 20 Name

# چک کن site-packages در C: پر است (نشانه‌ی کپی)
Test-Path "C:\projects\Translation\RAKE\RakeGlossary\.venv\Lib\site-packages"
* 

اگر G: خالی و C: پر بود → قطعاً کپی‌شده.

**راه‌حل:**

* powershell
deactivate
Remove-Item -Recurse -Force "G:\Projects\Translation\RakeGlossary\.venv"
cd G:\Projects\Translation\RakeGlossary
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
cd backend
python -m pip install -e ".[dev]"
* 

### ❌ `No module named uvicorn` بعد از انتقال

**علت:** `.venv` کپی‌شده یا نصب ناقص.

**راه‌حل:** بازسازی venv از صفر (بالا).

### ❌ `npm` خطای module resolution می‌دهد

**علت:** `node_modules` کپی‌شده با symlinks شکسته.

**راه‌حل:**

* powershell
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
* 

### ❌ `.exe` بعد از انتقال crash می‌کند

**علت:** `dist/` کپی‌شده و PyInstaller مسیر مطلق مبدأ را در bundle دارد.

**راه‌حل:**

* powershell
Remove-Item -Recurse -Force build, dist, backend\build, backend\dist -ErrorAction SilentlyContinue
pyinstaller desktop\build.spec --clean --noconfirm
*

### ❌ `data/` خالی است یا پروژه‌های قبلی نمایش داده نمی‌شوند

**در حالت dev:**

- Data در `<root>/data/` است — مطمئن شو کپی شده
- اگر در `.gitignore` است، با `robocopy` بدون `/XD` کپی شده

**در حالت `.exe`:**

- Data در `%APPDATA%\RakeGlossary\data\` است (نه در پروژه)
- این مستقل از جابجایی پروژه است و دست‌نخورده می‌ماند
- اگر می‌خواهی data جدید جابجا شود:

* powershell
# از ماشین قدیم
Copy-Item -Recurse "$env:APPDATA\RakeGlossary" "<درایو>\RakeGlossary-AppData"

# روی ماشین جدید
Copy-Item -Recurse "<درایو>\RakeGlossary-AppData" "$env:APPDATA\RakeGlossary"


### ❌ `activate.ps1` خطای execution policy می‌دهد

* powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned


### ❌ `install-log.txt` در `git status` ظاهر می‌شود

**راه‌حل:**

* powershell
Remove-Item backend\install-log.txt
Add-Content -Path .gitignore -Value "`n# Local install logs`ninstall-log.txt`n*-log.txt"
git status --short


باید فقط `.gitignore` را `modified` نشان بدهد.

### ❌ درایو حرفش عوض شد (`G:` → `H:`)

**۱) Git:**

* powershell
# با wildcard، خودکار کار می‌کند
git config --global --add safe.directory "*"

# یا اگر مسیر خاص داری، حذف و اضافه کن
git config --global --unset safe.directory G:/Projects/Translation/RakeGlossary
git config --global --add safe.directory H:/Projects/Translation/RakeGlossary


**۲) venv:** مسیرهای داخلی venv به حرف درایو وابسته‌اند. **باید حذف و از صفر ساخته شود:**

* powershell
deactivate
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
cd backend
python -m pip install -e ".[dev]"


**۳) node_modules:**

* powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
*

**۴) IDE:**

- **VS Code:** `.vscode/settings.json` — کلید `python.defaultInterpreterPath` را آپدیت کن
- **PyCharm:** `File → Settings → Project → Python Interpreter` → مسیر جدید

**۵) `pyvenv.cfg`:** مسیر `home = C:\Users\...\Python312` (مسیر Python اصلی، نه درایو پروژه) — این **عوض نمی‌شود** چون Python اصلی همیشه در `C:` است.

### ❌ خطای `Permission denied` هنگام کپی

**علت:** فایل‌های قفل‌شده (مثلاً DB در حال استفاده) یا readonly.

**راه‌حل:**

* powershell
# بستن پروسه‌ها
Get-Process python, node, RakeGlossary -ErrorAction SilentlyContinue | Stop-Process -Force

# پاک کردن readonly attribute
Get-ChildItem -Recurse -File | ForEach-Object { $_.IsReadOnly = $false }

# دوباره کپی کن
robocopy ...
*

### ❌ `UnicodeDecodeError` در هنگام اجرا

**علت:** فایل با encoding اشتباه کپی شده (به‌خصوص روی exFAT).

**راه‌حل:** مطمئن شو فایل‌های `.py` و `.ts` با UTF-8 هستند:

* powershell
# چک encoding یک فایل نمونه
Get-Content backend\app\main.py -Encoding Byte | Select-Object -First 3
*

اگر BOM دارد (`EF BB BF`), ممکن است مشکلی نباشد. اگر دارد و مشکل ایجاد می‌کند:

* powershell
# حذف BOM
$content = Get-Content -Path file.py -Raw
[System.IO.File]::WriteAllText((Resolve-Path file.py), $content, [System.Text.UTF8Encoding]::new($false))
*

### ❌ درایو پر شد وسط نصب

**راه‌حل:**

* powershell
# چک فضای درایو
Get-PSDrive G

# چک حجم پوشه‌ها
Get-ChildItem G:\Projects\Translation\RakeGlossary -Recurse -Directory | ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    [PSCustomObject]@{ Path = $_.FullName; SizeMB = [math]::Round($size, 2) }
} | Sort-Object SizeMB -Descending | Select-Object -First 10
*

**راه‌حل:** فضای اضافه کن، یا پوشه‌های cache را پاک کن.

---

## دستورالعمل سریع

برای انتقال بعدی، فقط این چند خط کافی است:

* powershell
# ============================================================
# فاز ۱: پاکسازی مبدأ
# ============================================================
cd <مسیر مبدأ>

# بستن پروسه‌ها
Get-Process python, node, uvicorn, RakeGlossary -ErrorAction SilentlyContinue | Stop-Process -Force

# بکاپ DB و data
Copy-Item data\rakeglossary.db "<مسیر بکاپ>\rakeglossary.db.backup" -Force
Copy-Item -Recurse data\projects "<مسیر بکاپ>\projects_backup" -Force

# پاک کردن artifacts
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force frontend\node_modules -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force build, dist, backend\build, backend\dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force frontend\dist, frontend\.vite -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter ".mypy_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter ".ruff_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# چک git
git status

# ============================================================
# فاز ۲: انتقال
# ============================================================
robocopy "<مسیر مبدأ>" "<مسیر مقصد>" /E /COPYALL /DCOPY:T /R:3 /W:2 /MT:8 /XD "node_modules" ".venv" "build" "dist" "__pycache__" ".pytest_cache" ".mypy_cache" ".ruff_cache" ".vite"

# ============================================================
# فاز ۳: تنظیم Git روی درایو جدید
# ============================================================
cd "<مسیر مقصد>"
git config --global --add safe.directory "*"
git status --short
git log -1 --oneline

# ============================================================
# فاز ۴: ساخت محیط Python
# ============================================================
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
cd backend
python -m pip install -e ".[dev]"
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

# ============================================================
# فاز ۵: تست backend
# ============================================================
python -m pytest tests/ -q

# ============================================================
# فاز ۶: ساخت محیط Node
# ============================================================
cd ..\frontend
npm install
npm test

# ============================================================
# فاز ۷: تست اجرا
# ============================================================
# ترمینال ۱:
cd ..\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8765

# ترمینال ۲:
cd frontend
npm run dev
*
---

## پیوست: مسیر داده‌ها

| حالت | مسیر داده‌ها |
|---|---|
| **dev mode** | `<root>/data/rakeglossary.db` |
| **dev mode** | `<root>/data/projects/<title>__<id8>/` |
| **dev mode** | `<root>/data/exports/` |
| **dev mode** | `<root>/data/cache/translations/` |
| **dev mode** | `<root>/data/logs/rakeglossary.log` |
| **`.exe` mode** | `%APPDATA%\RakeGlossary\data\rakeglossary.db` |
| **`.exe` mode** | `%APPDATA%\RakeGlossary\data\projects\` |
| **`.exe` mode** | `%APPDATA%\RakeGlossary\data\exports\` |
| **`.exe` mode** | `%APPDATA%\RakeGlossary\data\cache\translations\` |
| **`.exe` mode** | `%APPDATA%\RakeGlossary\data\logs\rakeglossary.log` |

**نکته‌ی مهم:** در حالت `.exe`، داده‌ها **در پوشه‌ی پروژه نیستند** — در `%APPDATA%` هستند. پس انتقال پروژه به درایو دیگر، به data کاری ندارد. اگر می‌خواهی data هم منتقل شود:

* powershell
Copy-Item -Recurse "$env:APPDATA\RakeGlossary" "<درایو>\RakeGlossary-AppData"
# روی سیستم جدید:
Copy-Item -Recurse "<درایو>\RakeGlossary-AppData" "$env:APPDATA\RakeGlossary"
*

---

## تاریخچه‌ی نسخه

| نسخه | تاریخ | تغییرات |
|---|---|---|
| 1.0.0 | 2026-10-02 | نسخه‌ی اول جامع: ۱۲ فاز، چک‌لیست کامل، troubleshooting دقیق، نکات مخصوص External، دستورالعمل سریع |

---

**پایان سند**

این سند بر اساس تجربه‌ی واقعی انتقال `RakeGlossary` از `C:\` به `G:\` (درایو External) تهیه شده است.

اگر با مشکل جدیدی مواجه شدی، این سند را آپدیت کن و نسخه را افزایش بده.


---

## چند نکته درباره‌ی این سند

1. **ساختار ۱۲ فازی** — از آماده‌سازی تا تأیید نهایی، هیچ مرحله‌ای جا نیفتاده.

2. **دستورات آماده‌ی copy-paste** — همه با PowerShell، سازگار با Windows 10/11.

3. **بخش‌های مخصوص External** — سرعت، قطع ناگهانی، مسیر طولانی، BitLocker، NTFS vs exFAT.

4. **Troubleshooting جامع** — ۹ مشکل رایج با تشخیص قطعی و راه‌حل.

5. **دستورالعمل سریع در انتها** — برای انتقال‌های بعدی، فقط همین یک بلوک کافی است.

6. **پیوست مسیر داده‌ها** — تفاوت مهم بین dev mode و `.exe` mode.

**این سند را می‌توانی در `docs/Migration_Guide_v2.md` یا مشابه آن ذخیره کنی.**

</div>