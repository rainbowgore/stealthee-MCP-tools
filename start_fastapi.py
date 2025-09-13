#!/usr/bin/env python3
"""
Startup script for FastAPI server
"""
import uvicorn
from fastapi_server import app

if __name__ == "__main__":
    print("🚀 Starting Stealth Launch Radar FastAPI Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔧 Smithery compatible endpoints available")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
