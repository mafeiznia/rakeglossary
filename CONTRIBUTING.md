# Contributing to RakeGlossary

> راهنمای مشارکت در پروژه. با تشکر از اینکه می‌خواهی کمک کنی! 🙏

**English version below.**

---

## 🇮🇷 راهنمای فارسی

### خوش آمدید

RakeGlossary یک پروژه‌ی متن‌باز است که برای ساخت واژه‌نامه‌های دو زبانه از کتاب و متن طراحی شده. هر نوع مشارکتی — از گزارش باگ تا افزودن ویژگی جدید — ارزشمند است.

### راه‌های مشارکت

1. **گزارش باگ** — از template `Bug report` استفاده کن
2. **پیشنهاد ویژگی** — از template `Feature request` استفاده کن
3. **بهبود مستندات** — حتی اصلاح یک غلط تایپی کمک است
4. **ارسال کد** — برای باگ‌ها یا ویژگی‌های تأییدشده
5. **ترجمه** — پشتیبانی از زبان‌های جدید (فعلاً fa/en)

### پیش از ارسال Issue

1. **جستجو کن** — احتمالاً کسی قبلاً همین مشکل را گزارش کرده
2. **نسخه را چک کن** — مطمئن شو روی آخرین `main` هستی
3. **حداقل بازتولید** — مراحل دقیق برای بازتولید مشکل را بنویس
4. **محیط** — نسخه‌ی OS، Python، Node، مرورگر را ذکر کن

### راه‌اندازی محیط توسعه

به [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) مراجعه کن.

خلاصه:

```powershell
# 1) کلون
git clone https://github.com/mafeiznia/rakeglossary.git
cd rakeglossary

# 2) Backend
cd backend
python -m venv ..\venv312
..\venv312\Scripts\activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

# 3) Frontend
cd ..\frontend
npm install
```

### روند کار (Workflow)

1. **Fork** روی GitHub
2. **Branch** بساز: `git checkout -b feature/my-feature` یا `fix/my-bug`
3. **کد** بنویس
4. **تست** بنویس/به‌روز کن
5. **اجرای همه‌ی ابزارها:**
   ```powershell
   # Backend
   cd backend
   ruff check app/
   black app/
   mypy app/
   python -m pytest tests/ -v
   
   # Frontend
   cd frontend
   npx tsc --noEmit
   npm run lint
   npm test
   ```
6. **Commit** با پیام معنادار (پایین را ببین)
7. **Push** و **Pull Request**

### قواعد Commit Message

از فرمت زیر استفاده کن:

```
<type>(<scope>): <short summary>

<optional body with more details>

<optional footer>
```

**Typeهای مجاز:**
- `feat` — ویژگی جدید
- `fix` — رفع باگ
- `docs` — تغییر مستندات
- `test` — افزودن/اصلاح تست
- `refactor` — بازنویسی کد بدون تغییر رفتار
- `chore` — کارهای جانبی (deps, config, ...)
- `ci` — تغییر در CI/CD

**مثال‌های خوب:**
```
feat(glossary): add inline editing for entries
fix(extractor): handle empty PDF pages correctly
docs(readme): update Python version requirement to 3.12
ci(backend): bump actions/checkout to v5
```

**مثال‌های بد:**
```
fixed bug
update
WIP
asdf
```

### Pull Request

**قبل از ارسال:**
- [ ] کد را روی آخرین `main` rebase کردی
- [ ] همه‌ی تست‌های backend پاس می‌شوند (۲۰۴ تست)
- [ ] همه‌ی تست‌های frontend پاس می‌شوند (۱۵۰ تست)
- [ ] ruff / black / mypy بدون خطا
- [ ] tsc / oxlint بدون خطا
- [ ] اگر ویژگی جدیدی است، تست نوشتی
- [ ] اگر رفتار عوض شده، مستندات به‌روز شد
- [ ] پیام commit استاندارد است

**PR Template:**
```markdown
## توضیح
چه چیزی تغییر کرد و چرا؟

## نوع تغییر
- [ ] Bug fix
- [ ] Feature
- [ ] Breaking change
- [ ] Documentation

## تست‌ها
- [ ] تست‌های موجود پاس می‌شوند
- [ ] تست‌های جدید اضافه شدند

## Checklist
- [ ] کد با style راهنما مطابقت دارد
- [ ] مستندات به‌روز شد
- [ ] هیچ warning جدیدی اضافه نشد

## Issue مرتبط
Closes #XXX
```

### سبک کد

- **Backend:** `snake_case` برای توابع، `PascalCase` برای کلاس‌ها
- **Frontend:** `camelCase` برای متغیرها، `PascalCase` برای componentها
- **Imports:** alphabetical + grouped (stdlib، third-party، local)
- **Type hints:** اجباری (Python + TypeScript strict)
- **Comments:** فقط «چرا»، نه «چه»

### ساختار تست‌ها

- **Backend:** `backend/tests/` (pytest)
- **Frontend:** `frontend/tests/` (Vitest)
- هر تست جدید باید حداقل happy path + یک error case را پوشش دهد

### Code Review

- انتظار feedback محترمانه داشته باش
- تغییرات خواسته‌شده را در همان PR اعمال کن
- اگر مخالفی، دلیلت را توضیح بده
- Squash کن اگر commitهایت زیاد هستند

### مجوز (License)

با ارسال PR، موافقت می‌کنی که کدت تحت [MIT License](LICENSE) منتشر شود.

### ارتباط

- **Issue:** https://github.com/mafeiznia/rakeglossary/issues
- **Discussion:** https://github.com/mafeiznia/rakeglossary/discussions
- **Email:** ma.feiznia@gmail.com

---

## 🇬🇧 English Version

### Welcome

RakeGlossary is an open-source project for building bilingual glossaries from books and documents. Any contribution is welcome — from bug reports to new features.

### Ways to Contribute

1. **Report bugs** — use the `Bug report` template
2. **Suggest features** — use the `Feature request` template
3. **Improve docs** — even a typo fix helps
4. **Submit code** — for approved bugs/features
5. **Translate** — add new language support (currently fa/en)

### Before Opening an Issue

1. **Search first** — someone may have reported it
2. **Check version** — ensure you're on latest `main`
3. **Minimal reproduction** — exact steps to reproduce
4. **Environment** — OS, Python, Node, browser versions

### Development Setup

See [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md).

### Workflow

1. **Fork** on GitHub
2. **Create a branch:** `git checkout -b feature/my-feature` or `fix/my-bug`
3. **Write code**
4. **Write/update tests**
5. **Run all tools:**
   ```powershell
   # Backend
   cd backend
   ruff check app/
   black app/
   mypy app/
   python -m pytest tests/ -v
   
   # Frontend
   cd frontend
   npx tsc --noEmit
   npm run lint
   npm test
   ```
6. **Commit** with a meaningful message
7. **Push** and open a **Pull Request**

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

### Pull Request Checklist

- [ ] Rebased on latest `main`
- [ ] Backend tests pass (204 tests)
- [ ] Frontend tests pass (150 tests)
- [ ] No new linter warnings
- [ ] New tests added for new behavior
- [ ] Docs updated if behavior changed
- [ ] Commit message follows convention

### Code Style

- **Backend:** snake_case functions, PascalCase classes
- **Frontend:** camelCase variables, PascalCase components
- **Type hints:** required (Python + TypeScript strict)

### License

By submitting a PR, you agree that your code is released under the [MIT License](LICENSE).

### Contact

- **Issues:** https://github.com/mafeiznia/rakeglossary/issues
- **Email:** ma.feiznia@gmail.com

---

**Thanks for contributing! 🙌**