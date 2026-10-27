@echo off
chcp 65001 >nul
rem اجرای برنامه با پایتون (نیاز به نصب پایتون + کتابخانه‌ها)
cd /d "%~dp0"
python -m pip install --quiet customtkinter pillow
start "" pythonw run.pyw
