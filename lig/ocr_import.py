# -*- coding: utf-8 -*-
"""
واردات اطلاعات از اسکرین‌شات / عکس جدول لیگ
- OCR با Tesseract (در صورت نصب بودن) یا پیاده‌سازی سادهٔ داخلی
- تشخیص خطوط جدول، جدا کردن تیم/امتیاز/برد/... و پیش‌نمایش قبل از ذخیره
"""

import os
import re
import shutil
import subprocess
import sys

SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def normalize_digits(text):
    out = []
    for ch in text:
        i = PERSIAN_DIGITS.find(ch)
        if i >= 0:
            out.append(str(i))
            continue
        i = ARABIC_DIGITS.find(ch)
        if i >= 0:
            out.append(str(i))
            continue
        out.append(ch)
    return "".join(out)


def find_tesseract():
    """مسیر اجرایی tesseract را پیدا می‌کند (ویندوز/لينوکس)."""
    exe = shutil.which("tesseract")
    if exe:
        return exe
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def ocr_available():
    return find_tesseract() is not None or _pytesseract_ok()


def _pytesseract_ok():
    try:
        import pytesseract  # noqa: F401
        return True
    except Exception:
        return False


def image_to_text(path):
    """تبدیل عکس به متن. اول pytesseract، بعد فراخوانی مستقیم CLI."""
    path = str(path)
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(path)
        for lang in ("fas", "eng", ""):
            try:
                txt = pytesseract.image_to_string(img, lang=lang) if lang \
                    else pytesseract.image_to_string(img)
                if txt and txt.strip():
                    return txt
            except Exception:
                continue
    except Exception:
        pass
    exe = find_tesseract()
    if exe:
        try:
            res = subprocess.run([exe, path, "stdout", "-l", "fas+eng"],
                                 capture_output=True, text=True, timeout=60)
            if res.stdout.strip():
                return res.stdout
            res = subprocess.run([exe, path, "stdout"], capture_output=True, text=True, timeout=60)
            return res.stdout
        except Exception:
            pass
    raise RuntimeError(
        "موتور OCR روی سیستم پیدا نشد.\n"
        "برای واردات از اسکرین‌شات، Tesseract را نصب کنید:\n"
        "https://github.com/UB-Mannheim/tesseract/wiki\n"
        "یا متن تصویر را دستی در کادر وارد کنید.")


# ------------------ پارسر جدول ------------------
TEAM_STOP_WORDS = {"تیم", "باشگاه", "fc", "cf"}

# ترتیب ستون‌ها در جدول لیگ برتر (پیش‌فرض رایج در سایت‌های فارسی)
COLS_FA = ["رتبه", "تیم", "بازی", "برد", "تساوی", "باخت", "گل زده", "گل خورده", "گل تفاضل", "امتیاز"]


def _split_numbers(line):
    nums = re.findall(r"\d+", normalize_digits(line))
    return [int(n) for n in nums]


def _team_name_from_line(line):
    # حذف اعداد و کاراکترهای جداکننده؛ هر چه مانده نام تیم است
    name = re.sub(r"\d+", " ", line)
    name = re.sub(r"[|:/\\\-–—_=+*.,،()\[\]{}<>#%]", " ", name)
    parts = [p.strip() for p in name.split() if p.strip() and p.strip().lower() not in TEAM_STOP_WORDS]
    return " ".join(parts).strip()


def parse_table_text(text):
    """
    خروجی: لیستی از دیکشنری با کلیدهای team, played, w, d, l, gf, ga, gd, pts
    منطق: هر خط => یک عددِ آخر = امتیاز (یا اگر ۹ عدد داشت ترتیب ستون‌ها)
    """
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if any(w in low for w in ("رتبه", "تیم", "امتیاز", "بازی", "headtohead", "next")):
            # سطر سرستون
            if sum(map(str.isdigit, normalize_digits(line))) < 3:
                continue
        nums = _split_numbers(line)
        name = _team_name_from_line(line)
        if not name or len(nums) < 2:
            continue
        row = {"team": name, "played": None, "w": None, "d": None, "l": None,
               "gf": None, "ga": None, "gd": None, "pts": None}
        if len(nums) >= 9:
            # رتبه + ۸ ستون آمار
            vals = nums[-8:]
            row.update(dict(zip(("played", "w", "d", "l", "gf", "ga", "gd", "pts"), vals)))
        elif len(nums) == 8:
            vals = nums
            row.update(dict(zip(("played", "w", "d", "l", "gf", "ga", "gd", "pts"), vals)))
        elif len(nums) == 5:
            # بازی، برد، تساوی، باخت، امتیاز
            p, w, d, l, pts = nums
            row.update(dict(played=p, w=w, d=d, l=l, pts=pts, gd=w - l))
        elif len(nums) == 2:
            row["pts"] = nums[1]
        else:
            row["pts"] = nums[-1]
            rest = nums[:-1]
            if len(rest) >= 4:
                row.update(dict(played=rest[-4], w=rest[-3], d=rest[-2], l=rest[-1]))
        if row["pts"] is not None and row["pts"] <= 300:
            rows.append(row)
    return rows


def parse_matches_text(text, known_teams):
    """استخراج نتایج/بازی‌های برنامه‌ریزی‌شده از متن: «A 2 - 1 B» یا «A - B»"""
    out = []
    teams_sorted = sorted(known_teams, key=len, reverse=True)
    for raw in text.splitlines():
        line = normalize_digits(raw.strip())
        if not line:
            continue
        m = re.match(r"^(.+?)\s*(\d+)\s*[-–x:]\s*(\d+)\s*(.+)$", line)
        if m:
            h, hg, ag, a = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4).strip()
            out.append(dict(home=h, away=a, home_goals=hg, away_goals=ag))
            continue
        m = re.match(r"^(.+?)\s*[-–]\s*(.+)$", line)
        if m:
            h, a = m.group(1).strip(), m.group(2).strip()
            if h and a and not any(ch.isdigit() for ch in h + a):
                out.append(dict(home=h, away=a, home_goals=None, away_goals=None))
    # اعتبارسنجی نام‌ها با تیم‌های شناخته‌شده
    valid = []
    for it in out:
        th = _match_team(it["home"], teams_sorted)
        ta = _match_team(it["away"], teams_sorted)
        if th and ta and th != ta:
            valid.append(dict(it, home_id=th, away_id=ta))
    return valid


def _match_team(fragment, teams_sorted):
    fragment = re.sub(r"\d+", "", fragment).strip()
    frag_clean = re.sub(r"[^0-9A-Za-z\u0600-\u06FF ]", " ", fragment)
    frag_clean = " ".join(frag_clean.split())
    for t in teams_sorted:
        tn = " ".join(re.sub(r"[^0-9A-Za-z\u0600-\u06FF ]", " ", t).split())
        if tn and (tn in frag_clean or frag_clean in tn):
            return t
    return None


def save_screenshot_copy(img_path):
    """کپی اسکرین‌شات داخل پوشهٔ برنامه برای آرشیو؛ مسیر جدید را برمی‌گرداند."""
    os.makedirs(SHOT_DIR, exist_ok=True)
    base = os.path.basename(str(img_path)) or "shot.png"
    dest = os.path.join(SHOT_DIR, base)
    if os.path.abspath(str(img_path)) != os.path.abspath(dest):
        shutil.copy2(str(img_path), dest)
    return dest


def grab_screen_clipboard_image():
    """اگر تصویری در کلیپ‌بورد ویندوز باشد آن را در فایل ذخیره و مسیر می‌دهد."""
    if sys.platform != "win32":
        return None
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            os.makedirs(SHOT_DIR, exist_ok=True)
            from datetime import datetime
            dest = os.path.join(SHOT_DIR, f"clip_{datetime.now():%Y%m%d_%H%M%S}.png")
            img.save(dest)
            return dest
    except Exception:
        pass
    return None
