# 🗂️ File Organizer

[![Python](https://img.shields.io/badge/Python-3.6+-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Auto‑sort files by extension** | مرتب‌سازی خودکار فایل‌ها بر اساس پسوند

---

## 📖 English | انگلیسی

**File Organizer** is a command‑line tool that scans a directory and moves files into categorized folders (Images, Documents, Videos, etc.) based on their file extensions.

### ✨ Features

- ✅ Smart sorting into 7+ default categories  
- 📝 Custom categories via JSON config  
- 🔍 **Dry‑run mode** – preview changes without moving anything  
- ♻️ Conflict handling: `rename`, `skip`, or `overwrite`  
- 📂 Recursive mode for subfolders  
- 📄 Logging to file  
- 🐍 Pure Python, no external dependencies  

### 🚀 Quick Start

```bash
git clone https://github.com/mahdihejazipr-web/file-organizer.git
cd file-organizer
python organizer.py /path/to/folder
```

| Command | Description |
|---------|-------------|
| `python organizer.py .` | Sort current folder |
| `python organizer.py ~/Downloads --dry-run` | Preview only |
| `python organizer.py . --recursive --copy` | Copy (don’t move) into subfolders |
| `python organizer.py . --config rules.json` | Use custom JSON rules |

---

## 📖 فارسی | Persian

**مرتب‌ساز فایل** یک ابزار خط فرمان است که پوشه‌ها را اسکن کرده و بر اساس پسوند فایل‌ها، آن‌ها را در پوشه‌های دسته‌بندی شده (مثل تصاویر، اسناد، ویدیوها و ...) جابجا می‌کند.

### ✨ قابلیت‌ها

- ✅ دسته‌بندی هوشمند در ۷ گروه پیش‌فرض  
- 📝 تعریف دسته‌بندی سفارشی با فایل JSON  
- 🔍 **حالت آزمایشی (Dry‑run)** – فقط نمایش تغییرات بدون جابجایی واقعی  
- ♻️ مدیریت تداخل نام فایل‌ها: تغییر نام، رد شدن یا بازنویسی  
- 📂 پردازش زیرپوشه‌ها به صورت بازگشتی  
- 📄 ذخیره گزارش عملیات در فایل لاگ  
- 🐍 پایتون خالص، بدون نیاز به نصب کتابخانه اضافی  

### 🚀 شروع سریع

```bash
git clone https://github.com/mahdihejazipr-web/file-organizer.git
cd file-organizer
python organizer.py /مسیر/پوشه/مقصد
```

| دستور | توضیح |
|-------|-------|
| `python organizer.py .` | مرتب‌سازی پوشه جاری |
| `python organizer.py ~/Downloads --dry-run` | فقط پیش‌نمایش |
| `python organizer.py . --recursive --copy` | کپی (نه جابجایی) در زیرپوشه‌ها |
| `python organizer.py . --config rules.json` | استفاده از قوانین سفارشی JSON |

---

## ⚙️ Sample Config | نمونه تنظیمات (JSON)

Create a file like `my_rules.json` | فایلی مثل `my_rules.json` بسازید:

```json
{
  "categories": {
    "Spreadsheets": [".xlsx", ".xls", ".csv"],
    "Code": [".py", ".js", ".html", ".css"]
  }
}
```

Then run | سپس اجرا کنید:

```bash
python organizer.py . --config my_rules.json
```

---

## 📄 License | مجوز

MIT – free for personal and commercial use.  
استفاده شخصی و تجاری آزاد.

---

## ⭐ Show your support

If this tool helps you, give it a star on GitHub.  
اگر این ابزار به کارتان آمد، به مخزن ستاره دهید.
