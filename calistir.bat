@echo off
chcp 65001 >nul
set PYTHONUTF8=1
title Site Klonlayici 
cls
echo.
echo  Baslatiyor...
echo.
python "%~dp0siteklonlayici.py"
if %errorlevel% neq 0 (
    echo.
    echo  [HATA] Python bulunamadi veya bir hata olustu.
    echo  Lutfen Python 3.8+ yukleyin: https://www.python.org/downloads/
    echo.
    pause
)
