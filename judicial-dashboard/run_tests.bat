@echo off
REM Judicial Analytics Dashboard - Test Runner (Windows)
REM Student: FRANK LYAGOBA
REM Roll Number: 011240174

echo Starting Judicial Analytics Dashboard Tests...
echo Student: FRANK LYAGOBA (011240174)
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required but not installed.
    exit /b 1
)

REM Navigate to backend directory
cd backend

REM Create virtual environment if it doesn't exist
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

REM Run backend tests
echo Running backend tests...
echo ========================
python -m pytest tests/ -v --tb=short

REM Check test results
if errorlevel 1 (
    echo ❌ Some backend tests failed!
    exit /b 1
) else (
    echo ✅ All backend tests passed!
)

REM Navigate to frontend directory
cd ..\frontend

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Warning: Node.js not found. Skipping frontend tests.
    exit /b 0
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo Warning: npm not found. Skipping frontend tests.
    exit /b 0
)

REM Install frontend dependencies
echo Installing frontend dependencies...
npm install

REM Run frontend tests (if test script exists)
echo Running frontend tests...
echo ========================
npm test -- --watchAll=false

if errorlevel 1 (
    echo ❌ Some frontend tests failed!
) else (
    echo ✅ All frontend tests passed!
)

echo ================================================
echo Test execution completed!
echo Student: FRANK LYAGOBA (011240174)
echo Course: Master of Science in Information Technology
