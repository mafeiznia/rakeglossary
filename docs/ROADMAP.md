# RakeGlossary — دفترچه توسعه

> نقشه‌ی راه و ایده‌های توسعه برای مراحل بعدی پروژه.

**نسخه فعلی:** 0.1.0  
**آخرین به‌روزرسانی:** 2026-09-21

---

## 📌 وضعیت فعلی پروژه

| بخش | وضعیت |
|---|---|
| Backend tests | ✅ 204 پاس |
| Frontend tests | ✅ 14 پاس |
| زیرساخت Vitest | ✅ |
| D.6 backend README | ✅ |
| D.7 frontend README | ✅ |
| D.8 About + version badge | ✅ |
| D.9 Vitest setup | ✅ |
| dev server | ✅ |

**اجرای تست‌ها:**

- Backend: `cd backend && python -m pytest tests/ -v`
- Frontend: `cd frontend && npm test`

---

## 🗺️ نقشه‌ی راه — تسک‌های برنامه‌ریزی‌شده

### D.10 — تست‌های بیشتر frontend

**هدف:** افزایش coverage و catch رگرسیون در اجزای کلیدی UI.

**گام‌ها:**

1. تست `SettingsPage` (integration)
2. تست `ProjectsPage` (لیست، خالی، لودینگ)
3. تست `ProjectDetailPage` (نقشه‌ها، حالت‌ها)
4. تست کامپوننت‌های `features/settings/`:
   - `StopwordsManager`
   - `LlmSettings`
   - `LlmQuickSetupDialog`
5. تست کامپوننت‌های `features/sources/`
6. تست کامپوننت‌های `features/glossary/`
7. تست hookهای دیگر: `useSettings`, `useConfirm`, `useProgressStream`
8. افزایش coverage به بالای 60%

**خروجی:** پوشه‌ی `src/**/*.test.tsx` گسترده + گزارش coverage.

---

### D.11 — CI/CD با GitHub Actions

**هدف:** اجرای خودکار تست‌ها و linting روی هر push/PR.

**گام‌ها:**

1. ساخت `.github/workflows/backend-ci.yml`:
   - اجرا روی `windows-latest` و `ubuntu-latest`
   - `setup-python` 3.12
   - `pip install -e ".[dev]"`
   - دانلود `en_core_web_sm`, `nltk` data
   - `ruff check app/`
   - `mypy app/`
   - `pytest tests/ -v`
2. ساخت `.github/workflows/frontend-ci.yml`:
   - `setup-node` 24
   - `npm ci`
   - `tsc --noEmit`
   - `oxlint`
   - `npm test`
3. Badge در `README.md` بالای فایل
4. (اختیاری) Pre-commit hooks:
   - `.pre-commit-config.yaml`
   - `ruff`, `black`, `mypy` روی backend
   - `oxlint`, `tsc` روی frontend

**خروجی:** تست خودکار روی هر commit + badge در README.

**پیش‌نیاز:** مخزن پروژه به GitHub push شده باشد.

---

### D.12 — تکمیل مستندات

**هدف:** آماده‌سازی برای انتشار و مشارکت دیگران.

**گام‌ها:**

1. `docs/ARCHITECTURE.md` — معماری سیستم:
   - نمودار کلی (backend, frontend, DB, pipeline)
   - توضیح لایه‌ها
   - جریان داده از upload تا خروجی
   - تصمیمات معماری (ADR)
2. `docs/DEVELOPER_GUIDE.md` — راهنمای توسعه‌دهنده:
   - راه‌اندازی محیط dev
   - ساختار کد
   - نحوه‌ی افزودن extractor/translator جدید
   - نحوه‌ی افزودن provider LLM
   - قواعد کد (lint، تست، naming)
   - روند commit/PR
3. `docs/USER_GUIDE.md` (فارسی) — راهنمای کاربر نهایی:
   - نصب و راه‌اندازی
   - ساخت پروژه جدید
   - آپلود فایل یا ورود متن
   - انتخاب حالت پردازش (Offline / Hybrid / AI)
   - مدیریت منابع
   - ویرایش واژه‌نامه
   - خروجی گرفتن
4. `docs/TROUBLESHOOTING.md` — مشکلات رایج:
   - خطاهای نصب
   - خطاهای API
   - مشکلات ترجمه
   - مشکلات LLM
5. `CHANGELOG.md` — تاریخچه تغییرات (با فرمت Keep a Changelog)
6. `CONTRIBUTING.md` — راهنمای مشارکت
7. `LICENSE` — فایل MIT License با نام صاحب اثر

**خروجی:** مستندات کامل در پوشه‌ی `docs/`.

---

### D.13 — بسته‌بندی (Packaging)

**هدف:** خروجی `.exe` قابل توزیع برای ویندوز.

**گام‌ها:**

1. pywebview wrapper — `desktop/launcher.py`:
   - راه‌اندازی backend در thread جداگانه
   - باز کردن پنجره‌ی بومی با URL محلی
   - مدیریت lifecycle (بستن سرور هنگام خروج)
   - splash screen در حین بوت
2. PyInstaller spec — `desktop/build.spec`:
   - bundling تمام dependencies Python
   - جمع‌آوری `frontend/dist/` به عنوان data
   - جمع‌آوری `backend/app/` و migrationها
   - ساخت `.exe` تک‌فایل
   - آیکون برنامه (`assets/icon.ico`)
3. Inno Setup installer — `installer/setup.iss`:
   - نصب در `Program Files`
   - ساخت shortcut در Start Menu و Desktop
   - ثبت در Add/Remove Programs
   - uninstaller خودکار
4. اسکریپت build — `scripts/build-windows.bat`:
   - اجرای `npm run build` در frontend
   - کپی `dist/` به مسیر backend
   - اجرای PyInstaller
   - اجرای Inno Setup
5. تست بسته‌بندی:
   - تست روی ویندوز ARM64
   - تست روی ویندوز x64
   - تست پاک‌سازی و نصب مجدد

**خروجی:** فایل `RakeGlossary-Setup-x.y.z.exe`.

**چالش‌های پیش‌رو:**

- ARM64 vs x64 Python wheels
- اندازه‌ی فایل نهایی (احتمالاً 300-500 MB)
- سرعت startup (اولین اجرا کندتر)
- مسیر `data/` در `AppData` نه در کنار `.exe`

---

## 🎯 D.14 به بعد — ایده‌های توسعه

### 🥇 سطح ۱ — بهبود تجربه‌ی کاربر (High Priority)

#### 1. Search & Replace در Glossary

- جستجوی سریع در همه‌ی ستون‌ها
- فیلتر بر اساس source/POS/category
- ویرایش دسته‌ای (batch edit)
- جایگزینی الگو (regex optional)
- **مزیت:** سرعت ویرایش واژه‌نامه‌های بزرگ

#### 2. Undo/Redo در ویرایش entries

- Stack عملیات (حداقل 20 قدم)
- Keyboard: `Ctrl+Z`, `Ctrl+Y`
- نمایش toast با «Undo» button
- **مزیت:** کاهش خطر از دست دادن کار

#### 3. Keyboard Shortcuts

- `Ctrl+S` — ذخیره
- `Ctrl+Enter` — اجرای پردازش
- `Escape` — بستن dialog
- `Ctrl+F` — جستجو
- `Ctrl+K` — command palette
- **مزیت:** کارایی برای کاربران حرفه‌ای

#### 4. Auto-switch theme

- تشخیص `prefers-color-scheme`
- گزینه‌ی «Auto» در تنظیمات
- **مزیت:** تجربه‌ی طبیعی‌تر در شب/روز

#### 5. Notification پس از پردازش طولانی

- Notification API مرورگر
- پشتیبانی از صدای alert
- **مزیت:** کاربر می‌تواند در تب دیگر کار کند

#### 6. Export to PDF

- چیدمان دو ستونی
- فونت‌های قابل تنظیم
- شماره‌ی صفحه و فهرست
- **مزیت:** خروجی قابل چاپ و اشتراک

#### 7. Import from existing glossary

- پشتیبانی از TBX, TMX, CSV
- ادغام با واژه‌نامه‌ی موجود
- تشخیص تعارض و پیشنهاد
- **مزیت:** استفاده از واژه‌نامه‌های قبلی

---

### 🥈 سطح ۲ — قابلیت‌های پیشرفته (Medium Priority)

#### 8. Batch processing

- صف پردازش چند پروژه
- اجرای موازی یا ترتیبی
- مدیریت cancellation گروهی
- **مزیت:** پردازش کل کتابخانه

#### 9. Project templates

- قالب‌های آماده: رمان، علمی، فنی، حقوقی
- ذخیره‌ی تنظیمات مورد استفاده به عنوان template
- **مزیت:** شروع سریع‌تر پروژه‌های مشابه

#### 10. Multi-language support

- EN→AR, EN→DE, EN→FR, ...
- انتخاب زبان در UI
- فونت‌های مناسب هر زبان
- **مزیت:** کاربران غیرفارسی‌زبان

#### 11. Domain-specific models

- مدل‌های NLP آموزش‌دیده روی دامنه‌های خاص
- presets برای پزشکی، حقوقی، فنی
- **مزیت:** دقت بالاتر در دامنه‌های تخصصی

#### 12. Word frequency analysis

- نمایش فرکانس هر عبارت
- نمودار histogram
- فیلتر بر اساس بازه‌ی فرکانس
- **مزیت:** اولویت‌بندی واژه‌های مهم

#### 13. Custom RAKE parameters در UI

- تنظیم `min_length`, `max_length`
- انتخاب stopwords سفارشی
- preview قبل از پردازش کامل
- **مزیت:** تنظیم دقیق‌تر الگوریتم

#### 14. Term consistency checker

- بررسی ترجمه‌های متناقض
- پیشنهاد یکسان‌سازی
- **مزیت:** کیفیت بالاتر واژه‌نامه

---

### 🥉 سطح ۳ — معماری و اکوسیستم (Long-term)

#### 15. Plugin system

- API برای افزودن extractor سفارشی
- API برای افزودن translator
- API برای افزودن LLM provider
- نصب plugin از URL یا فایل
- **مزیت:** گسترش توسط جامعه

#### 16. CLI mode

- اجرای headless: `rakeglossary process --input book.pdf --output glossary.xlsx`
- مناسب برای automation
- **مزیت:** اسکریپت‌نویسی و CI

#### 17. Public API

- REST API عمومی برای integrations
- API key authentication
- Rate limiting
- Webhook برای اتمام پردازش
- **مزیت:** اتصال به ابزارهای دیگر (CAT tools)

#### 18. Cloud sync (اختیاری)

- همگام‌سازی پروژه‌ها بین دستگاه‌ها
- Self-hosted option (Nextcloud, WebDAV)
- رمزنگاری end-to-end
- **مزیت:** استفاده روی چند دستگاه

#### 19. Docker image

- `Dockerfile` چند مرحله‌ای
- `docker-compose.yml` برای dev
- اجرا در محیط containerized
- **مزیت:** استقرار ساده در سرور

#### 20. Integration با CAT tools

- خروجی XLIFF
- اتصال به Trados/MemoQ
- **مزیت:** یکپارچگی با workflow ترجمه

---

### 🏅 سطح ۴ — کیفیت و پایداری (Ongoing)

#### 21. Performance profiling

- Profiling با cProfile
- بهینه‌سازی extractors برای کتاب‌های بزرگ (1000+ صفحه)
- Stream کردن نتایج به جای نگه‌داشتن در RAM
- **مزیت:** سرعت بالاتر و مصرف رم کمتر

#### 22. Error boundary + Sentry

- Error boundary در React برای جلوگیری از blank page
- Sentry برای گزارش خودکار خطاها
- Opt-in برای کاربر
- **مزیت:** تشخیص سریع‌تر باگ‌ها

#### 23. E2E tests با Playwright

- تست کامل workflow: upload → process → export
- Cross-browser: Chromium, Firefox, WebKit
- Screenshot comparison
- **مزیت:** اطمینان از کارکرد end-to-end

#### 24. Accessibility (a11y)

- ARIA labels کامل
- Keyboard navigation
- Screen reader support
- کنتراست رنگ‌ها (WCAG AA)
- **مزیت:** قابل استفاده برای همه

#### 25. Internationalization کامل

- استخراج تمام متن‌های hardcoded
- پشتیبانی RTL/LTR خودکار
- فرمت تاریخ/عدد محلی
- **مزیت:** آماده برای ترجمه به زبان‌های دیگر

#### 26. Security hardening

- Sanitization فایل‌های آپلودی
- Rate limiting روی API
- CSP headers
- **مزیت:** امنیت بیشتر

#### 27. Logging بهتر

- Structured logging (JSON)
- Correlation ID برای ردیابی
- Log rotation بهتر
- **مزیت:** عیب‌یابی سریع‌تر

#### 28. Backup/restore

- پشتیبان‌گیری خودکار از پروژه‌ها
- Restore از فایل backup
- Export کامل پروژه
- **مزیت:** جلوگیری از از دست دادن داده

---

## 📊 ماتریس اولویت

| سطح | ویژگی | زمان تخمینی | تأثیر بر کاربر |
|---|---|---|---|
| 🥇 1 | Search & Replace | 2-3 روز | بالا |
| 🥇 2 | Undo/Redo | 1-2 روز | بالا |
| 🥇 3 | Keyboard Shortcuts | 1 روز | متوسط |
| 🥇 6 | Export to PDF | 2-3 روز | بالا |
| 🥈 8 | Batch processing | 3-5 روز | بالا |
| 🥈 10 | Multi-language | 3-4 روز | بالا |
| 🥉 15 | Plugin system | 1-2 هفته | بسیار بالا |
| 🥉 17 | Public API | 1-2 هفته | بالا |

---

## 🎯 پیشنهاد ترتیب اجرا

پس از **D.10 تا D.13**:

1. **D.14:** Search & Replace (سطح ۱، #1)
2. **D.15:** Undo/Redo (سطح ۱، #2)
3. **D.16:** Export to PDF (سطح ۱، #6)
4. **D.17:** Batch processing (سطح ۲، #8)
5. **D.18:** Multi-language (سطح ۲، #10)
6. **D.19:** E2E tests + Accessibility (سطح ۴)
7. **D.20:** Plugin system (سطح ۳، #15)

---

## 📝 یادداشت‌های فنی

### الگوهای mock کردن در تست‌ها

- `vi.mock('@/hooks/useAbout')` برای mock کردن hookها
- `vi.mock('react-i18next')` برای `t()` و `i18n.language`
- QueryClient با `retry: false` برای تست‌های سریع
- همیشه `beforeEach(() => vi.clearAllMocks())`

### الگوهای state management

- سرور state: TanStack Query
- ترجیحات کاربر: Zustand + persist
- UI state: React `useState`

### الگوهای i18n

- همیشه کلیدها را در `fa.ts` و `en.ts` هم‌زمان اضافه کن
- برای RTL از `ms-*`, `me-*` استفاده کن نه `ml-*`
- برای اعداد و نام‌های انگلیسی از `dir="ltr"` روی عنصر

### الگوهای error handling

- Backend: `raise HTTPException` با detail واضح
- Frontend: axios interceptor → `Error(message)`
- UI: toast برای خطاهای کاربر

### نکات Vite 8

- از `path.resolve(process.cwd(), 'src')` برای alias استفاده کن
- از `import.meta.dirname` در config پرهیز کن (مشکل با rolldown)
- فایل config فقط یکی باشد (`vite.config.ts` یا `.js` نه هر دو)

### درس‌های آموخته‌شده

- **همیشه قبل از debug عمیق، ساختار کامل پوشه را چک کن:**  
  `Get-ChildItem <folder>` — گاهی یک فایل با پسوند اشتباه (مثل `vite.config.ts.txt`) همه چیز را به‌هم می‌ریزد.
- **بعد از تغییر config، Vite cache را پاک کن:**  
  `Remove-Item -Recurse -Force node_modules\.vite`
- **aliasها در Vite dev و Vitest جداست:**  
  در Vitest کار می‌کند، در Vite dev نه — همیشه در هر دو محیط تست کن.

---

## 🔗 لینک‌های مفید

- Backend README: `../backend/README.md`
- Frontend README: `../frontend/README.md`
- GitHub Repo: https://github.com/mafeiznia/rakeglossary

---

**نکته:** این سند یک سند زنده است. با پیشرفت پروژه، آیتم‌ها را تیک بزن و تغییرات جدید اضافه کن.