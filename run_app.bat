@echo off
setlocal enabledelayedexpansion
title SAPA Analytics - Analisis Audit Media Sosial Personal - Kanwil Kepri
echo ======================================================================
echo          MENYALAKAN SISTEM ANALISIS AUDIT MEDSOS PERSONAL
echo                     KANWIL KEMENKUMHAM KEPRI
echo ======================================================================
echo.

cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo [*] Membersihkan proses pada port 5050 (jika ada)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050') do taskkill /f /pid %%a >nul 2>&1

echo [*] Menyiapkan environment Python...
if exist ".venv\Scripts\python.exe" (
    start "Audit Analytics Server" .venv\Scripts\python.exe app.py
) else (
    start "Audit Analytics Server" uv run --with flask --with pandas --with openpyxl --with pdfplumber --with reportlab python app.py
)

echo [*] Menunggu server untuk siap di port 5050...
timeout /t 3 /nobreak >nul

echo [*] Membuka Dashboard Analisis di browser...
start http://127.0.0.1:5050

echo.
echo ======================================================================
echo [OK] Aplikasi berhasil berjalan di http://127.0.0.1:5050
echo [!] Jendela ini dapat Anda minimize.
echo [!] Tekan tombol apa saja untuk menutup server.
echo ======================================================================
echo.
pause
echo [*] Menghentikan server Flask Analytics...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050') do taskkill /f /pid %%a >nul 2>&1
taskkill /FI "WINDOWTITLE eq Audit Analytics Server*" /F >nul 2>&1
exit
