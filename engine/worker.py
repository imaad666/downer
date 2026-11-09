import os
import re
import urllib.request
import urllib.parse
import threading
import yt_dlp
from core.config import DOWNLOADS_DIR
from core.sanitizer import sanitize_filename
from engine.ffmpeg_locator import get_ffmpeg_binary

queue_lock = threading.Lock()
download_queue = []
worker_running = False

def run_download_queue():
    global worker_running
    ffmpeg_path = get_ffmpeg_binary()
    
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
            out_tmpl = os.path.join(DOWNLOADS_DIR, '%(title).80s - %(uploader).40s.%(ext)s')
            if mode == "video":
                v_format = "bestvideo+bestaudio/best"
                ydl_opts = {
                    'format': v_format,
                    'outtmpl': out_tmpl,
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': ffmpeg_path,
                    'progress_hooks': [progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                }
            else:
                target_codec = fmt if fmt in ('wav', 'flac', 'm4a') else 'mp3'
                postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': target_codec}]
                if target_codec == 'mp3':
                    postprocessors[0]['preferredquality'] = '320'
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': out_tmpl,
                    'postprocessors': postprocessors,
                    'ffmpeg_location': ffmpeg_path,
                    'progress_hooks': [progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                prepared = ydl.prepare_filename(info)
                base, _ = os.path.splitext(prepared)
                ext = f".{target_codec}" if mode == "audio" else ".mp4"
                final_filename = os.path.basename(base + ext)

                with queue_lock:
                    for item in download_queue:
                        if item["id"] == item_id:
                            item["title"] = info.get('title') or item["title"]
                            item["status"] = "completed"
                            item["progress"] = 100.0
                            item["filename"] = final_filename
                            break

        except Exception as e:
            clean_err = re.sub(r'\x1b\[[0-9;]*m', '', str(e))
            with queue_lock:
                for item in download_queue:
                    if item["id"] == item_id:
                        item["status"] = "failed"
                        item["error"] = clean_err[:120]
                        break
