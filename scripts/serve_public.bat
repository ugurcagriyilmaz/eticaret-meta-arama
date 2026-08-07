@echo off
chcp 65001 >nul
title Canli Arama - ACIK (kapatinca tunel kapanir)
cd /d "%~dp0.."

echo ==================================================================
echo   TR E-Ticaret Meta Arama - CANLI ARAMA sunucusu
echo.
echo   Bu pencere ACIK oldugu surece: public canli arama CALISIR.
echo   Kapatmak icin: bu pencereyi KAPAT  (ya da Ctrl+C)
echo   Kapaninca API + Cloudflare Tunnel otomatik durur.
echo ==================================================================
echo.

REM API + tunnel'i baslat, URL'i api.json'a push'la, pencere kapanana kadar acik tut.
REM Pencere kapaninca konsol CTRL_CLOSE olayi uvicorn+cloudflared'i de durdurur.
venv\Scripts\python.exe scripts\serve_public.py

echo.
echo [temizlik] kalan tunel sureci kapatiliyor...
taskkill /F /IM cloudflared.exe >nul 2>&1
echo.
echo Canli arama durduruldu. Pencereyi kapatabilirsiniz.
pause >nul
