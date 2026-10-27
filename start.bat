@echo off
chcp 65001 >nul
echo ========================================================
echo        SuvNazorat Tizimini Ishga Tushirish
echo ========================================================
echo.

echo 1. Backend server ishga tushirilmoqda (8000-port)...
start "SuvNazorat - Backend" cmd /k "cd apps\backend && .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo 2. Frontend veb-dashboard ishga tushirilmoqda (3000-port)...
start "SuvNazorat - Frontend" cmd /k "cd apps\frontend && npm run dev"

echo 3. Telegram Bot ishga tushirilmoqda...
start "SuvNazorat - Bot" cmd /k "cd apps\bot && .venv\Scripts\python main.py"

echo.
echo ========================================================
echo Barcha servislar alohida oynalarda ishga tushirildi!
echo Veb-sayt: http://localhost:3000
echo Backend API Docs: http://localhost:8000/docs
echo Login: admin  (yoki ali)
echo Parol: Admin12345678!
echo ========================================================
pause

