"""Shared download logic for the Vercel serverless functions."""

import os
import re
import tempfile
import urllib.request
import urllib.parse
from typing import Optional

import yt_dlp
import imageio_ffmpeg

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


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


def ydl_base_opts(**extra):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 8,
        "http_headers": {"User-Agent": UA},
    }
    opts.update(extra)
    return opts


def inspect(url: str) -> dict:
    platform = detect_platform(url)

    try:
        with yt_dlp.YoutubeDL(ydl_base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)

        if info.get("entries"):
            first = info["entries"][0] or {}
            title = f"{info.get('title', 'Playlist')} ({len(info['entries'])} items)"
            uploader = info.get("uploader") or first.get("uploader") or ""
            thumbnail = info.get("thumbnail") or first.get("thumbnail") or ""
            duration = info.get("duration") or first.get("duration") or 0
        else:
            title = info.get("title") or "Media Track"
            uploader = (
                info.get("uploader")
                or info.get("artist")
                or info.get("channel")
                or ""
            )
            thumbnail = info.get("thumbnail") or ""
            duration = info.get("duration") or 0

        return {
            "url": url,
            "title": title,
            "uploader": uploader,
            "platform": platform,
            "duration": duration,
            "duration_formatted": format_duration(duration),
            "thumbnail": thumbnail,
            "type": "media",
        }
    except Exception:
        # Direct file or unsupported page — do a lightweight HEAD probe.
        try:
            head = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
            with urllib.request.urlopen(head, timeout=6) as resp:
                content_len = resp.headers.get("Content-Length")
                size_mb = (
                    f"{int(content_len) / (1024 * 1024):.1f} MB"
                    if content_len
                    else "Unknown size"
                )
                parsed = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed.path) or "downloaded_file"
                return {
                    "url": url,
                    "title": filename,
                    "uploader": resp.headers.get("Server", platform),
                    "platform": platform,
                    "duration": 0,
                    "duration_formatted": size_mb,
                    "thumbnail": "",
                    "type": "direct_file",
                }
        except Exception:
            pass

        parsed = urllib.parse.urlparse(url)
        return {
            "url": url,
            "title": os.path.basename(parsed.path) or url,
            "uploader": parsed.netloc or platform,
            "platform": platform,
            "duration": 0,
            "duration_formatted": "",
            "thumbnail": "",
            "type": "url",
        }


def is_direct_file(url: str) -> bool:
    """True when the URL looks like a plain file rather than a media page."""
    try:
        head = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(head, timeout=6) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if ctype and "text/html" not in ctype and "application/xhtml" not in ctype:
                return True
    except Exception:
        pass
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    return ext in (
        ".zip", ".rar", ".7z", ".tar", ".gz", ".pdf", ".iso",
        ".exe", ".dmg", ".apk", ".mp3", ".mp4", ".wav", ".flac",
    )


def download_audio(url: str, fmt: str):
    """Returns (file_path, filename, media_type)."""
    codec = fmt if fmt in ("wav", "flac", "m4a") else "mp3"
    tmpdir = tempfile.mkdtemp(prefix="dl_")
    outtmpl = os.path.join(tmpdir, "%(title).80s.%(ext)s")

    postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": codec}]
    if codec == "mp3":
        postprocessors[0]["preferredquality"] = "320"

    ydl_opts = ydl_base_opts(
        format="bestaudio/best",
        outtmpl=outtmpl,
        postprocessors=postprocessors,
        ffmpeg_location=FFMPEG_PATH,
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        raise RuntimeError(f"Download failed: {str(e)[:200]}")

    title = sanitize_filename(info.get("title") or "audio")
    filename = f"{title}.{codec}"

    produced = [
        os.path.join(tmpdir, f)
        for f in os.listdir(tmpdir)
        if f.lower().endswith(f".{codec}")
    ]
    if not produced:
        produced = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    if not produced:
        raise RuntimeError("Conversion produced no file")

    media_types = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "m4a": "audio/mp4",
    }
    return produced[0], filename, media_types.get(codec, "application/octet-stream")


def download_video(url: str, fmt: str):
    """Returns (file_path, filename, media_type)."""
    height = {"mp4_720": 720, "mp4_1080": 1080}.get(fmt)
    if height:
        v_format = (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height}]+bestaudio/"
            f"best[height<={height}]/best"
        )
    else:
        v_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

    tmpdir = tempfile.mkdtemp(prefix="dlv_")
    outtmpl = os.path.join(tmpdir, "%(title).80s.%(ext)s")

    ydl_opts = ydl_base_opts(
        format=v_format,
        outtmpl=outtmpl,
        merge_output_format="mp4",
        ffmpeg_location=FFMPEG_PATH,
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        raise RuntimeError(f"Download failed: {str(e)[:200]}")

    produced = [
        os.path.join(tmpdir, f)
        for f in os.listdir(tmpdir)
        if f.lower().endswith((".mp4", ".mkv", ".webm", ".mov"))
    ]
    if not produced:
        produced = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    if not produced:
        raise RuntimeError("Download produced no file")

    path = produced[0]
    ext = os.path.splitext(path)[1].lstrip(".") or "mp4"
    filename = f"{sanitize_filename(info.get('title') or 'video')}.{ext}"
    media_types = {
        "mp4": "video/mp4",
        "mkv": "video/x-matroska",
        "webm": "video/webm",
        "mov": "video/quicktime",
    }
    return path, filename, media_types.get(ext, "application/octet-stream")
