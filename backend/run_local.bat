@echo off
echo Starting Books Management System Backend...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check if dependencies are installed
echo Checking dependencies...
pip install -q -r requirements.txt

echo.
echo Starting FastAPI server...
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
