#!/usr/bin/env python3
"""
TradeAssist Application Runner

This script provides a proper entry point for running the TradeAssist application
while maintaining correct Python package structure with relative imports.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import the application
from src.backend.main import app
from src.backend.config import settings

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting TradeAssist Application")
    print(f"📍 Host: {settings.HOST}")
    print(f"🔌 Port: {settings.PORT}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"📊 Database: {settings.DATABASE_URL}")
    print("-" * 50)
    
    # Use string import for reload functionality
    uvicorn.run(
        "src.backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )