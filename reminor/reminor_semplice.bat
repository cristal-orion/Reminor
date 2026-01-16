@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cls
echo.
echo ========================================
echo     REMINOR - Launcher Semplificato
echo ========================================
echo.
echo Test UTF-8: à è ì ò ù é á í ó ú
echo.

REM Trova Go
if exist "C:\Program Files (x86)\Go\bin\go.exe" (
    set "GOEXE=C:\Program Files (x86)\Go\bin\go.exe"
    echo Go trovato in Program Files x86
) else (
    set GOEXE=go
    echo Go cercato nel PATH
)

REM Verifica Go
"%GOEXE%" version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Go non funziona!
    pause
    exit /b 1
)

echo Python e Go pronti!
echo.

REM Termina server precedenti
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    netstat -ano | findstr :8080 | findstr %%i >nul 2>&1
    if not errorlevel 1 (
        taskkill /pid %%i /f >nul 2>&1
    )
)

echo Avvio server Python...
start /B python memory_server.py >nul 2>&1
timeout /t 3 /nobreak >nul

echo Avvio Reminor...
echo Usa le frecce per navigare, Enter per selezionare, Esc per uscire
echo.

"%GOEXE%" run .

echo.
echo Terminazione server...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    netstat -ano | findstr :8080 | findstr %%i >nul 2>&1
    if not errorlevel 1 (
        taskkill /pid %%i /f >nul 2>&1
    )
)
echo Grazie per aver usato Reminor!
