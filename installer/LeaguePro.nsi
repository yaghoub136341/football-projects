; ============================================================
;  اسکریپت نصب LeaguePro (نصبی جدول لیگ برتر ایران) - NSIS
;  اجرا توسط build_exe.bat  یا  makensis LeaguePro.nsi
; ============================================================
!include "MUI2.nsh"

Name "LeaguePro - Persian League Table"
OutFile "LeaguePro-Setup.exe"
InstallDir "$PROGRAMFILES64\LeaguePro"
InstallDirRegKey HKLM "Software\LeaguePro" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

!ifndef APP_VERSION
  !define APP_VERSION "1.0.0"
!endif
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey ProductName "LeaguePro"
VIAddVersionKey FileVersion "${APP_VERSION}"

!define MUI_ICON "..\assets\LeaguePro.ico"
!define MUI_UNICON "..\assets\LeaguePro.ico"
!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "LeaguePro" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  File "..\dist\LeaguePro.exe"
  File "..\assets\LeaguePro.ico"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; میان‌بر منوی شروع و دسکتاپ
  CreateDirectory "$SMPROGRAMS\LeaguePro"
  CreateShortcut "$SMPROGRAMS\LeaguePro\LeaguePro.lnk" "$INSTDIR\LeaguePro.exe" "" "$INSTDIR\LeaguePro.exe"
  CreateShortcut "$SMPROGRAMS\LeaguePro\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\LeaguePro.lnk" "$INSTDIR\LeaguePro.exe" "" "$INSTDIR\LeaguePro.exe"

  WriteRegStr HKLM "Software\LeaguePro" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LeaguePro" "DisplayName" "LeaguePro - Persian League Table"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LeaguePro" "DisplayIcon" "$INSTDIR\LeaguePro.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LeaguePro" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LeaguePro" "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\LeaguePro.exe"
  Delete "$INSTDIR\LeaguePro.ico"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$DESKTOP\LeaguePro.lnk"
  RMDir /r "$SMPROGRAMS\LeaguePro"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LeaguePro"
  DeleteRegKey HKLM "Software\LeaguePro"
  ; داده‌های کاربر در %USERPROFILE%\LeaguePro باقی می‌ماند
SectionEnd
