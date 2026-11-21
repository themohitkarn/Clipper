import os
import sys
import webbrowser
import threading
import time

def print_banner():
    banner = """
================================================================================
   ____ _ _                            _    ___ 
  / ___| (_)_ __  _ __   ___ _ __     / \  |_ _|
 | |   | | | '_ \| '_ \ / _ \ '__|   / _ \  | | 
 | |___| | | |_) | |_) |  __/ |     / ___ \ | | 
  \____|_|_| .__/| .__/ \___|_|    /_/   \_\___|
           |_|   |_|                            
================================================================================
   Turn Any Long Video (10m - 24hr) into Viral Shorts & Reels (100% Free)
   Repository: https://github.com/themohitkarn/Clipper
================================================================================
"""
    print(banner)

def open_browser():
    time.sleep(1.8)
    print("\n[+] Opening Clipper Web Dashboard in your browser: http://localhost:8000")
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

def main():
    print_banner()
    
    # Ensure current directory is on PYTHONPATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Start browser opener thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Uvicorn server
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )

if __name__ == "__main__":
    main()
