#!/usr/bin/env python3
"""
Attendance System Startup Script
This script starts both the backend API server and frontend web server
"""

import os
import sys
import subprocess
import time
import webbrowser
from threading import Thread

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting Backend Server...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'ai-service')
    
    try:
        # Change to ai-service directory and start Flask app
        os.chdir(backend_dir)
        subprocess.run([sys.executable, 'app.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
        return True

def start_frontend():
    """Start the frontend web server"""
    print("🌐 Starting Frontend Server...")
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    try:
        # Change to frontend directory and start HTTP server
        os.chdir(frontend_dir)
        subprocess.run([sys.executable, '-m', 'http.server', '8080'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
        return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'ai-service')
    
    try:
        # Check if we can import the main dependencies
        import flask
        import cv2
        import face_recognition
        import numpy as np
        import pandas as pd
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Please run: pip install -r ai-service/requirements.txt")
        return False

def main():
    """Main function to start the attendance system"""
    print("=" * 50)
    print("🎓 Face Recognition Attendance System")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    print("\n📝 Instructions:")
    print("1. Backend will start on http://localhost:5000")
    print("2. Frontend will start on http://localhost:8080")
    print("3. Browser will open automatically")
    print("4. Press Ctrl+C to stop both servers")
    print("\n" + "=" * 50)
    
    # Start backend in a separate thread
    backend_thread = Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend in main thread (this blocks)
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:8080')
        
        browser_thread = Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        start_frontend()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Attendance System...")
        sys.exit(0)

if __name__ == "__main__":
    main()
