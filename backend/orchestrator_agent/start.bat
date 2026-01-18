@echo off
REM Startup script for Orchestrator Agent (Windows)

echo 🤖 Starting Orchestrator Agent...
echo ================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

REM Run migrations
echo Running migrations...
python manage.py migrate

REM Start server
echo.
echo ✅ Starting Orchestrator Agent on port 8005...
echo 📡 API endpoint: http://localhost:8005/api/orchestrator/chat
echo 🔍 Health check: http://localhost:8005/api/health
echo.
python manage.py runserver 8005
