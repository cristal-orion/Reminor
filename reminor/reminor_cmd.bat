@echo off
REM ========================================
REM REMINOR - Launcher ottimizzato UTF-8
REM ========================================

REM Imposta codepage UTF-8 per caratteri accentati italiani
chcp 65001 > nul

REM Configura variabili di ambiente per UTF-8
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cls
echo.
echo ========================================
echo      REMINOR - Launcher UTF-8
echo ========================================
echo.
echo Test caratteri: a e i o u
echo.

REM Trova Go
set GO_PATH=
if exist "C:\Program Files (x86)\Go\bin\go.exe" (
    set GO_PATH="C:\Program Files (x86)\Go\bin\go.exe"
    echo (OK) Go trovato in Program Files (x86)
) else if exist "C:\Program Files\Go\bin\go.exe" (
    set GO_PATH="C:\Program Files\Go\bin\go.exe"
    echo (OK) Go trovato in Program Files
) else (
    go version >nul 2>&1
    if not errorlevel 1 (
        set GO_PATH=go
        echo (OK) Go trovato nel PATH
    ) else (
        echo (X) Go non trovato!
        pause
        exit /b 1
    )
)

REM Controlla Python
python --version >nul 2>&1
if errorlevel 1 (
    echo (X) Python non trovato!
    pause
    exit /b 1
) else (
    echo (OK) Python trovato
)

REM Controlla GROQ API Key
if exist "..\.env" (
    findstr "gsk_" "..\.env" >nul
    if not errorlevel 1 (
        echo (OK) GROQ API Key configurata
    ) else (
        echo (!) GROQ API Key non configurata
    )
) else (
    echo (!) File .env non trovato
)

echo.
echo ========================================
echo        AVVIO REMINOR
echo ========================================
echo.

REM Termina eventuali server precedenti
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    netstat -ano | findstr :8080 | findstr %%i >nul 2>&1
    if not errorlevel 1 (
        echo Terminazione server precedente PID: %%i
        taskkill /pid %%i /f >nul 2>&1
    )
)

REM Avvia server Python
echo Avvio server Python...
start /B python memory_server.py >nul 2>&1
timeout /t 3 /nobreak >nul

REM Verifica server
netstat -an | findstr :8080 >nul
if errorlevel 1 (
    echo (!) Server Python potrebbe non essere avviato
) else (
    echo (OK) Server Python attivo su porta 8080
)

echo.
echo Avvio Reminor con supporto UTF-8...
echo Caratteri accentati supportati: a e i o u
echo.

REM Avvia l'applicazione Go
%GO_PATH% run .

REM Cleanup al termine
echo.
echo Terminazione server Python...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul') do (
    netstat -ano | findstr :8080 | findstr %%i >nul 2>&1
    if not errorlevel 1 (
        taskkill /pid %%i /f >nul 2>&1
    )
)

echo.
echo Grazie per aver usato Reminor!
pause
