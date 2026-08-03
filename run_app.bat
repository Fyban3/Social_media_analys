@echo off
title Aplikasi Analisis Audit Media Sosial Personal - Kanwil Kemenkumham Kepri
echo ======================================================================
echo          MENYALAKAN SISTEM ANALISIS AUDIT MEDSOS PERSONAL
echo                     KANWIL KEMENKUMHAM KEPRI
echo ======================================================================
echo.
echo [*] Menyiapkan environment Python via UV...
echo [*] Meluncurkan server backend Flask di port 5050...
echo.

cd /d "%~dp0"

echo [*] Membersihkan proses pada port 5050 (jika ada)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050') do taskkill /f /pid %%a >nul 2>&1

:: Launch Flask server
start "Audit Analytics Server" cmd /c "uv run --with flask --with pandas --with openpyxl --with pdfplumber python app.py"

echo [*] Menunggu server untuk siap...
timeout /t 3 /nobreak >nul

echo [*] Membuka Dashboard Analisis di browser Anda...
start http://127.0.0.1:5050

echo.
echo ======================================================================
echo [OK] Aplikasi berhasil berjalan di http://127.0.0.1:5050
echo [!] Jendela ini dapat Anda minimize.
echo ======================================================================
echo.
pause
