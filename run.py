#!/usr/bin/env python3
"""
Run script for Synchronous Research Assistant
"""

import subprocess
import sys
import time
import os
from multiprocessing import Process

def run_backend_sync():
    """Run the synchronous FastAPI backend"""
    os.chdir("backend/api")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

def run_frontend_sync():
    """Run the synchronous Streamlit frontend"""
    # Wait for backend to start
    time.sleep(3)
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/app.py", 
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

def main():
    """Main function to run both services"""
    print("🚀 Starting Synchronous Research Assistant...")
    print("📡 Backend (sync): http://localhost:8000")
    print("🖼️  Frontend (sync): http://localhost:8501")
    print("⚡ Mode: Synchronous Processing")
    print("\n" + "="*60)
    
    # Start backend process
    backend_process = Process(target=run_backend_sync)
    backend_process.start()
    
    try:
        # Run frontend in main process
        run_frontend_sync()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_process.terminate()
        backend_process.join()

if __name__ == "__main__":
    main()