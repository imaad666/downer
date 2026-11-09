import webbrowser
import threading
import time
import uvicorn
from app import app

def open_browser():
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 60)
    print(" 🎵 WaveCloud — SoundCloud WAV Queue & Downloader")
    print(" 👉 Running at: http://127.0.0.1:8000")
    print("=" * 60)
    
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info", access_log=False)
    server = uvicorn.Server(config)
    server.run()
