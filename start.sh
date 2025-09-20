#!/bin/bash

echo "Starting SonarQube AI Advisor..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo
    echo "Please edit .env file with your SonarQube configuration before running the application."
    echo
    read -p "Press enter to continue..."
fi

# Start the application
echo "Starting FastAPI application..."
echo
echo "The API will be available at:"
echo "- Main API: http://localhost:8000"
echo "- Interactive docs: http://localhost:8000/docs"
echo "- Health check: http://localhost:8000/health"
echo

python main.py