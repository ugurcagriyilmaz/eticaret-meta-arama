@echo off
REM run_daily.bat - Windows tetikleyici
REM build_data.py'yi calistirir, sonra data.json'u repoya commit + push eder.
REM Zamanlanmis Gorev (Task Scheduler) ile gece calistirilabilir.

setlocal
cd /d "%~dp0.."

REM --- venv python ---
set PY=venv\Scripts\python.exe
if not exist "%PY%" set PY=python

REM --- toplayici (sorguyu buradan degistir) ---
set QUERY=beyaz erkek spor ayakkabi beden 42
"%PY%" backend\build_data.py "%QUERY%" --limit 8
if errorlevel 1 (
  echo [HATA] build_data.py basarisiz.
  exit /b 1
)

REM --- git push ---
git add data\data.json
git commit -m "data: gunluk guncelleme (%date% %time%)"
if errorlevel 1 (
  echo [bilgi] commit edilecek degisiklik yok.
) else (
  git push
)

echo Tamamlandi.
endlocal
