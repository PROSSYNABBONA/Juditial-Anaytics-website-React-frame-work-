#!/bin/bash

# Judicial Analytics Dashboard - Test Runner
# Student: FRANK LYAGOBA
# Roll Number: 011240174

echo "Starting Judicial Analytics Dashboard Tests..."
echo "Student: FRANK LYAGOBA (011240174)"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Navigate to backend directory
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run backend tests
echo "Running backend tests..."
echo "========================"
python -m pytest tests/ -v --tb=short

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All backend tests passed!"
else
    echo "❌ Some backend tests failed!"
    exit 1
fi

# Navigate to frontend directory
cd ../frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js not found. Skipping frontend tests."
    exit 0
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Warning: npm not found. Skipping frontend tests."
    exit 0
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
npm install

# Run frontend tests (if test script exists)
if [ -f "package.json" ] && grep -q '"test"' package.json; then
    echo "Running frontend tests..."
    echo "========================"
    npm test -- --watchAll=false
    
    if [ $? -eq 0 ]; then
        echo "✅ All frontend tests passed!"
    else
        echo "❌ Some frontend tests failed!"
    fi
else
    echo "No frontend tests configured."
fi

echo "================================================"
echo "Test execution completed!"
echo "Student: FRANK LYAGOBA (011240174)"
echo "Course: Master of Science in Information Technology"
