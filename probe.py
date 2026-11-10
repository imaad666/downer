"""Metadata probing for inspect endpoint."""

import os
import urllib.parse

import yt_dlp

from duration import format_duration
from net import UA, head_request, ydl_base_opts
from platforms import detect_platform


def _playlist_info(info):
    first = info["entries"][0] or {}
    return {
        "title": f"{info.get('title', 'Playlist')} ({len(info['entries'])} items)",
        "uploader": info.get("uploader") or first.get("uploader") or "",
        "thumbnail": info.get("thumbnail") or first.get("thumbnail") or "",
        "duration": info.get("duration") or first.get("duration") or 0,
    }


def _media_info(info):
    return {
        "title": info.get("title") or "Media Track",
        "uploader": (
            info.get("uploader")
            or info.get("artist")
            or info.get("channel")
            or ""
        ),
        "thumbnail": info.get("thumbnail") or "",
        "duration": info.get("duration") or 0,
    }


def _payload(url, platform, meta, type_):
    return {
        "url": url,
        "title": meta["title"],
        "uploader": meta["uploader"],
        "platform": platform,
        "duration": meta["duration"],
        "duration_formatted": format_duration(meta["duration"]),
        "thumbnail": meta["thumbnail"],
        "type": type_,
    }


def inspect(url: str) -> dict:
    platform = detect_platform(url)

    try:
        with yt_dlp.YoutubeDL(ydl_base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)

        meta = _playlist_info(info) if info.get("entries") else _media_info(info)
        return _payload(url, platform, meta, "media")
    except Exception:
        # Direct file or unsupported page — do a lightweight HEAD probe.
        try:
            with head_request(url) as resp:
                content_len = resp.headers.get("Content-Length")
                size_mb = (
                    f"{int(content_len) / (1024 * 1024):.1f} MB"
                    if content_len
                    else "Unknown size"
                )
                parsed = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed.path) or "downloaded_file"
                meta = {
                    "title": filename,
                    "uploader": resp.headers.get("Server", platform),
                    "thumbnail": "",
                    "duration": 0,
                }
                out = _payload(url, platform, meta, "direct_file")
                out["duration_formatted"] = size_mb
                return out
        except Exception:
            pass

        parsed = urllib.parse.urlparse(url)
        meta = {
            "title": os.path.basename(parsed.path) or url,
            "uploader": parsed.netloc or platform,
            "thumbnail": "",
            "duration": 0,
        }
        return _payload(url, platform, meta, "url")
