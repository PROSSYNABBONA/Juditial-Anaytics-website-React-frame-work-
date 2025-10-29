#!/bin/bash

# Judicial Analytics Dashboard Startup Script

echo "Starting Judicial Analytics Dashboard..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed. Please install Node.js."
    exit 1
fi

# Start backend
echo "Starting backend server..."
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
echo "Starting frontend server..."
cd ../frontend
npm install
npm start &
FRONTEND_PID=$!

echo "Dashboard is starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait
