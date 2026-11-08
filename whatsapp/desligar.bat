@echo off
REM ============================================================
REM  AgroBot - desliga tudo: ngrok, bot e containers da Evolution.
REM  A sessao do WhatsApp fica salva (nao apaga os volumes).
REM ============================================================
setlocal
cd /d "%~dp0"
set "PATH=C:\Program Files\Docker\Docker\resources\bin;%PATH%"

echo Parando o ngrok...
taskkill /f /im ngrok.exe >nul 2>&1

echo Parando o bot (porta 8001)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
taskkill /f /fi "WINDOWTITLE eq AgroBot - bot*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AgroBot - ngrok*" >nul 2>&1

echo Parando os containers da Evolution...
docker compose down

echo.
echo Tudo desligado.
pause
