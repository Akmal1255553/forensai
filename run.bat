@echo off
cd /d "%~dp0"
if not exist .env copy .env.example .env
pip install -r requirements.txt -q
echo.
echo ========================================
echo   AI Forensic Expert
echo   http://127.0.0.1:8000
echo ========================================
echo   Добавьте GEMINI_API_KEY в .env для полного анализа
echo.
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
