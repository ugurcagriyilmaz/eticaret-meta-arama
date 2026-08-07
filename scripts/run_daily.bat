@echo off
REM run_daily.bat - Windows gecelik tetikleyici
REM   build_data.py'yi calistirir -> data.json uretir -> repoya commit + push eder.
REM Kullanim:
REM   run_daily.bat                        (varsayilan sorgu)
REM   run_daily.bat "haki erkek mont"      (kendi sorgun)
REM Task Scheduler ile gece calistirilabilir.
REM
REM NOTLAR:
REM  - Playwright GORUNUR (headless=False) tarayici acar; masaustu oturumu gerekir.
REM  - GoodbyeDPI ACIKSA Python TLS'i bozabilir; toplayici icin kapali onerilir.

setlocal
cd /d "%~dp0.."

REM --- venv python ---
set PY=venv\Scripts\python.exe
if not exist "%PY%" set PY=python

REM --- sorgu: argumandan al, yoksa varsayilan ---
set "QUERY=%~1"
if "%QUERY%"=="" set "QUERY=beyaz erkek spor ayakkabi beden 42"

set "LOG=scripts\run_daily.log"
echo. >> "%LOG%"
echo ==== %date% %time% ^| sorgu: %QUERY% ==== >> "%LOG%"

REM --- toplayici ---
"%PY%" backend\build_data.py "%QUERY%" --limit 9 >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [HATA] build_data.py basarisiz - detay: %LOG%
  echo [HATA] build_data.py basarisiz. >> "%LOG%"
  exit /b 1
)

REM --- git commit + push (degisiklik varsa) ---
git add data\data.json
git commit -m "data: gunluk guncelleme (%date% %time%)" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [bilgi] commit edilecek degisiklik yok.
  echo [bilgi] commit edilecek degisiklik yok. >> "%LOG%"
) else (
  git push >> "%LOG%" 2>&1
  echo [ok] push edildi.
)

echo Tamamlandi. Log: %LOG%
endlocal
