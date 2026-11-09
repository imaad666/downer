import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
import subprocess
import threading
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import imageio_ffmpeg

app = FastAPI(title="Cobalt-Inspired Universal Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "downloads"))
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(STATIC_DIR, exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

queue_lock = threading.Lock()
download_queue = []
worker_running = False

class InspectRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    mode: Optional[str] = "audio"     # "audio" | "video" | "raw"
    format: Optional[str] = "mp3"    # "mp3" | "wav" | "flac" | "m4a" | "mp4_best" | "mp4_1080" | "mp4_720" | "raw"
    title: Optional[str] = None
    thumbnail: Optional[str] = None

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', '', filename)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:100] if cleaned else "download"

def format_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return ""
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def detect_platform(url: str) -> str:
    u = url.lower()
    if "soundcloud.com" in u:
        return "SoundCloud"
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube"
    if "tiktok.com" in u:
        return "TikTok"
    if "twitter.com" in u or "x.com" in u:
        return "Twitter / X"
    if "instagram.com" in u:
        return "Instagram"
    if "reddit.com" in u or "v.redd.it" in u:
        return "Reddit"
    if "twitch.tv" in u:
        return "Twitch"
    if "vimeo.com" in u:
        return "Vimeo"
    if "bilibili.com" in u:
        return "Bilibili"
    return "Direct / Web"

@app.post("/api/inspect")
def inspect_url(req: InspectRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    platform = detect_platform(url)

    # Fast probe with yt-dlp
    ydl_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # If playlist / multi-item
            if 'entries' in info and info['entries']:
                first = info['entries'][0] or {}
                title = f"{info.get('title', 'Playlist')} ({len(info['entries'])} items)"
                uploader = info.get('uploader') or first.get('uploader') or ""
                thumbnail = info.get('thumbnail') or first.get('thumbnail') or ""
                duration = info.get('duration') or first.get('duration') or 0
            else:
                title = info.get('title') or "Media Track"
                uploader = info.get('uploader') or info.get('artist') or info.get('channel') or ""
                thumbnail = info.get('thumbnail') or ""
                duration = info.get('duration') or 0

            return {
                "url": url,
                "title": title,
                "uploader": uploader,
                "platform": platform,
                "duration": duration,
                "duration_formatted": format_duration(duration),
                "thumbnail": thumbnail,
                "type": "media"
            }
    except Exception as e:
        # Check if direct HTTP file link
        try:
            head_req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='HEAD')
            with urllib.request.urlopen(head_req, timeout=6) as resp:
                content_type = resp.headers.get('Content-Type', '')
                content_len = resp.headers.get('Content-Length')
                size_mb = f"{int(content_len) / (1024*1024):.1f} MB" if content_len else "Unknown size"
                parsed = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed.path) or "downloaded_file"
                return {
                    "url": url,
                    "title": filename,
                    "uploader": resp.headers.get('Server', platform),
                    "platform": platform,
                    "duration": 0,
                    "duration_formatted": size_mb,
                    "thumbnail": "",
                    "type": "direct_file"
                }
        except Exception:
            pass

        # Return generic fallback preview
        parsed = urllib.parse.urlparse(url)
        return {
            "url": url,
            "title": os.path.basename(parsed.path) or url,
            "uploader": parsed.netloc or platform,
            "platform": platform,
            "duration": 0,
            "duration_formatted": "",
            "thumbnail": "",
            "type": "url"
        }

def download_worker():
    global worker_running
    while True:
        target_item = None
        with queue_lock:
            for item in download_queue:
                if item["status"] == "queued":
                    target_item = item
                    item["status"] = "downloading"
                    item["progress"] = 5.0
                    break
            if not target_item:
                worker_running = False
                break

        item_id = target_item["id"]
        url = target_item["url"]
        mode = target_item.get("mode", "audio")
        fmt = target_item.get("format", "mp3")

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes') or 0
                pct = (downloaded / total * 100) if total > 0 else 0
                speed = d.get('speed')
                speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else ""
                with queue_lock:
                    for item in download_queue:
                        if item["id"] == item_id:
                            item["progress"] = round(min(max(pct, 5.0), 95.0), 1)
                            item["speed"] = speed_str
                            break
            elif d['status'] == 'finished':
                with queue_lock:
                    for item in download_queue:
                        if item["id"] == item_id:
                            item["status"] = "processing"
                            item["progress"] = 96.0
                            break

        try:
            # Check if direct file stream (non-yt-dlp)
            parsed = urllib.parse.urlparse(url)
            file_ext = os.path.splitext(parsed.path)[1].lower()
            
            if mode == "raw" or (fmt == "raw" and file_ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.pdf', '.iso', '.exe', '.dmg', '.apk')):
                # Direct streaming download
                raw_filename = sanitize_filename(os.path.basename(parsed.path) or "downloaded_file")
                out_path = os.path.join(DOWNLOADS_DIR, raw_filename)
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as resp, open(out_path, 'wb') as f:
                    total_bytes = int(resp.headers.get('Content-Length') or 0)
                    downloaded = 0
                    chunk_size = 1024 * 128
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_bytes:
                            pct = round(downloaded / total_bytes * 100, 1)
                            with queue_lock:
                                for item in download_queue:
                                    if item["id"] == item_id:
                                        item["progress"] = pct
                                        break
                
                with queue_lock:
                    for item in download_queue:
                        if item["id"] == item_id:
                            item["status"] = "completed"
                            item["progress"] = 100.0
                            item["filename"] = raw_filename
                            break
                continue

            # YT-DLP Setup for Media (Audio or Video)
            out_tmpl = os.path.join(DOWNLOADS_DIR, '%(title).80s - %(uploader).40s.%(ext)s')

            if mode == "video":
                # Video modes
                if fmt == "mp4_1080":
                    v_format = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
                elif fmt == "mp4_720":
                    v_format = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
                else: # mp4_best
                    v_format = "bestvideo+bestaudio/best"

                ydl_opts = {
                    'format': v_format,
                    'outtmpl': out_tmpl,
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': FFMPEG_PATH,
                    'progress_hooks': [progress_hook],
                    'socket_timeout': 30,
                    'retries': 15,
                    'windowsfilenames': True,
                    'quiet': True,
                    'no_warnings': True,
                }
            else:
                # Audio modes (MP3 320k, WAV, FLAC, M4A)
                target_codec = fmt if fmt in ('wav', 'flac', 'm4a') else 'mp3'
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': target_codec,
                }]
                if target_codec == 'mp3':
                    postprocessors[0]['preferredquality'] = '320'

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': out_tmpl,
                    'postprocessors': postprocessors,
                    'ffmpeg_location': FFMPEG_PATH,
                    'progress_hooks': [progress_hook],
                    'socket_timeout': 30,
                    'retries': 15,
                    'windowsfilenames': True,
                    'quiet': True,
                    'no_warnings': True,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                prepared = ydl.prepare_filename(info)
                
                # Determine final file name after postprocessing
                base, _ = os.path.splitext(prepared)
                if mode == "audio":
                    ext = f".{target_codec}"
                else:
                    ext = ".mp4"
                
                final_filename = os.path.basename(base + ext)
                if not os.path.exists(os.path.join(DOWNLOADS_DIR, final_filename)):
                    # Check if original exists
                    if os.path.exists(prepared):
                        final_filename = os.path.basename(prepared)

                with queue_lock:
                    for item in download_queue:
                        if item["id"] == item_id:
                            item["title"] = info.get('title') or item["title"]
                            item["uploader"] = info.get('uploader') or item.get("uploader", "")
                            item["status"] = "completed"
                            item["progress"] = 100.0
                            item["filename"] = final_filename
                            break

        except Exception as e:
            clean_err = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
            if "policy: snip" in clean_err.lower() or "go+" in clean_err.lower():
                clean_err = "Track locked by subscription (Preview only)."
            elif "timed out" in clean_err.lower():
                clean_err = "Connection timed out. Please retry."
            with queue_lock:
                for item in download_queue:
                    if item["id"] == item_id:
                        item["status"] = "failed"
                        item["error"] = clean_err[:120]
                        break

@app.post("/api/download")
def start_download(req: DownloadRequest, bg_tasks: BackgroundTasks):
    global worker_running
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    item_id = f"dl_{int(time.time() * 1000)}_{abs(hash(url)) % 10000}"
    item = {
        "id": item_id,
        "url": url,
        "title": req.title or url,
        "uploader": "",
        "thumbnail": req.thumbnail or "",
        "platform": detect_platform(url),
        "mode": req.mode or "audio",
        "format": req.format or "mp3",
        "status": "queued",
        "progress": 0.0,
        "speed": "",
        "filename": "",
        "error": ""
    }

    with queue_lock:
        download_queue.insert(0, item)
        if not worker_running:
            worker_running = True
            threading.Thread(target=download_worker, daemon=True).start()

    return {"status": "queued", "item": item}

@app.get("/api/queue")
def get_queue():
    with queue_lock:
        return {"queue": list(download_queue)}

@app.delete("/api/queue/{item_id}")
def remove_queue_item(item_id: str):
    with queue_lock:
        for idx, item in enumerate(download_queue):
            if item["id"] == item_id:
                if item["status"] not in ("downloading", "processing"):
                    download_queue.pop(idx)
                    return {"deleted": True, "id": item_id}
                else:
                    item["status"] = "failed"
                    item["error"] = "Cancelled"
                    return {"cancelled": True, "id": item_id}
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/api/queue/clear-completed")
def clear_completed():
    with queue_lock:
        to_keep = [it for it in download_queue if it["status"] in ("queued", "downloading", "processing")]
        download_queue.clear()
        download_queue.extend(to_keep)
    return {"status": "ok"}

@app.post("/api/open-downloads-folder")
def open_downloads_folder():
    try:
        if sys.platform == "win32":
            os.startfile(DOWNLOADS_DIR)
        elif sys.platform == "darwin":
            subprocess.run(["open", DOWNLOADS_DIR])
        else:
            subprocess.run(["xdg-open", DOWNLOADS_DIR])
        return {"status": "opened", "path": DOWNLOADS_DIR}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open directory: {str(e)}")

@app.get("/api/download-file/{filename}")
def download_local_file(filename: str):
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print(" 🚀 Cobalt-Style Universal Downloader")
    print(" 👉 Open at: http://127.0.0.1:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
