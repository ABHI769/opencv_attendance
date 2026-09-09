import os
import sys
import subprocess
import time
import webbrowser
from threading import Thread

def start_backend():
    print("🚀 Starting Backend Server...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'ai-service')
    
    try:
        os.chdir(backend_dir)
        subprocess.run([sys.executable, 'app.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
        return True

def check_dependencies():
    print("🔍 Checking dependencies...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'ai-service')
    
    try:
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
    print("=" * 50)
    print("Face Recognition Attendance System")
    print("=" * 50)
    
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    print("\nInstructions:")
    print("1. Backend will start on http://localhost:5000")
    print("2. Browser will open automatically")
    print("3. Press Ctrl+C to stop the server")
    print("\n" + "=" * 50)
    
    try:
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        browser_thread = Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        start_backend()
    except KeyboardInterrupt:
        print("\nShutting down Attendance System...")
        sys.exit(0)

if __name__ == "__main__":
    main()
