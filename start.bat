@echo off
echo Starting SonarQube AI Advisor...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo Please edit .env file with your SonarQube configuration before running the application.
    echo.
    pause
)

REM Start the application
echo Starting FastAPI application...
echo.
echo The API will be available at:
echo - Main API: http://localhost:8000
echo - Interactive docs: http://localhost:8000/docs
echo - Health check: http://localhost:8000/health
echo.
python main.py