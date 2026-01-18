@echo off
echo Starting Reminor...

:: Start backend in new window
start "Reminor Backend" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && cd backend && python -m uvicorn api.main:app --reload --port 8000"

:: Start frontend in new window
start "Reminor Frontend" cmd /k "cd /d %~dp0reminor-frontend && npm run dev"

echo.
echo Servers starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo.
