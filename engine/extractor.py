import urllib.request
import urllib.parse
import os
import yt_dlp
from core.platform import detect_platform
from core.formatters import format_duration

def inspect_media_url(url: str) -> dict:
    platform = detect_platform(url)
    ydl_opts = {
        'extract_flat': False,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
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
    except Exception:
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
