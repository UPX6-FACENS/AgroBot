@echo off
REM ============================================================
REM  AgroBot - liga tudo com dois cliques:
REM    Docker (Evolution) -> bot (porta 8001) -> ngrok -> webhook
REM  Para desligar: desligar.bat
REM ============================================================
setlocal
cd /d "%~dp0"
title AgroBot - ligando

REM Dominio fixo do ngrok da conta logada nesta maquina (troque se usar outra conta)
set NGROK_DOMAIN=thumping-squad-qualifier.ngrok-free.dev
set "PATH=C:\Program Files\Docker\Docker\resources\bin;%PATH%"

echo.
echo [1/5] Verificando o Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo       Docker desligado. Abrindo o Docker Desktop, aguarde...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    for /l %%i in (1,1,60) do (
        timeout /t 3 /nobreak >nul
        docker info >nul 2>&1 && goto docker_ok
    )
    echo ERRO: o Docker nao subiu em 3 minutos. Abra o Docker Desktop na mao e rode de novo.
    pause
    exit /b 1
)
:docker_ok
echo       Docker OK.

echo.
echo [2/5] Subindo a Evolution API (containers)...
docker compose up -d
if errorlevel 1 (
    echo ERRO ao subir os containers.
    pause
    exit /b 1
)

echo.
echo [3/5] Abrindo o bot numa janela nova (porta 8001)...
set PY=python
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe
start "AgroBot - bot" cmd /k %PY% -m uvicorn main:app --port 8001

echo.
echo [4/5] Abrindo o ngrok numa janela nova...
start "AgroBot - ngrok" cmd /k ngrok http --url=%NGROK_DOMAIN% 8001

echo.
echo [5/5] Configurando a Evolution (instancia, webhook, ignorar grupos)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0configurar.ps1" -NgrokUrl https://%NGROK_DOMAIN%

echo.
echo ============================================================
echo  Pronto. Deixe as janelas "AgroBot - bot" e "AgroBot - ngrok"
echo  abertas. Mande uma foto de teste para o numero do bot.
echo ============================================================
pause
