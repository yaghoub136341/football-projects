@echo off
chcp 65001 >nul
rem ============================================================
rem  ساخت فایل اجرایی EXE + فایل نصبی Installer
rem  برنامهٔ جدول لیگ برتر ایران (LeaguePro)
rem  - فقط روی ویندوز اجرا کنید (نیاز به پایتون: python.org)
rem ============================================================
cd /d "%~dp0"

echo [1/4] نصب کتابخانه‌های مورد نیاز...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install customtkinter pillow pyinstaller nsis
if errorlevel 1 (
    echo نصب کتابخانه‌ها ناموفق بود. پایتون را از python.org نصب کنید.
    pause & exit /b 1
)

echo [2/4] ساخت آیکون برنامه...
python make_icon.py

echo [3/4] ساخت فایل اجرایی با PyInstaller...
pyinstaller --noconfirm --clean --onefile --windowed --name "LeaguePro" ^
  --icon "assets\LeaguePro.ico" ^
  --collect-all customtkinter ^
  --add-data "assets;assets" ^
  run.pyw
if errorlevel 1 (
    echo ساخت EXE ناموفق بود.
    pause & exit /b 1
)

echo [4/4] ساخت فایل نصبی (Installer)...
if exist installer\makensis.exe (
    installer\makensis.exe /DAPP_VERSION=1.0.0 installer\LeaguePro.nsi
) else (
    makensis /DAPP_VERSION=1.0.0 installer\LeaguePro.nsi
)
if errorlevel 1 (
    echo.
    echo *** makensis پیدا نشد؛ فایل EXE ساخته شد اما نصبی ساخته نشد.
    echo *** می‌توانید NSIS را از https://nsis.sourceforge.io نصب کنید و دوباره اجرا کنید.
    goto :end
)

:end
echo.
echo ================================================
echo  فایل اجرایی :  dist\LeaguePro.exe
echo  فایل نصبی   :  installer\LeaguePro-Setup.exe
echo ================================================
pause
