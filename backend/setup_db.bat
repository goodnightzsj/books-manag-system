@echo off
echo Setting up database...
echo.

REM Activate virtual environment
call venv\Scripts\activate

echo Running database migrations...
alembic upgrade head

echo.
echo Creating admin user...
python scripts/create_admin.py

echo.
echo Database setup completed!
pause
