#!/bin/bash
# Startup script for Orchestrator Agent

echo "🤖 Starting Orchestrator Agent..."
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start server
echo ""
echo "✅ Starting Orchestrator Agent on port 8005..."
echo "📡 API endpoint: http://localhost:8005/api/orchestrator/chat"
echo "🔍 Health check: http://localhost:8005/api/health"
echo ""
python manage.py runserver 8005
