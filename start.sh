#!/bin/bash
"""
Quick Start Script for TradeAssist

This script activates the virtual environment and starts the application.
Usage: ./start.sh
"""

echo "🚀 TradeAssist Quick Start"
echo "=========================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed. Installing now..."
    pip install -r requirements.txt
fi

echo "🔥 Starting TradeAssist backend..."
echo "   Access API docs at: http://localhost:8000/docs"
echo "   Health check at: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Run the application
python run.py