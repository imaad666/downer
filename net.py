"""HTTP helpers and yt-dlp option factory."""

import os
import urllib.request
import urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

DIRECT_FILE_EXTS = (
    ".zip", ".rar", ".7z", ".tar", ".gz", ".pdf", ".iso",
    ".exe", ".dmg", ".apk", ".mp3", ".mp4", ".wav", ".flac",
)


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


def head_request(url: str, timeout: int = 6):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
    return urllib.request.urlopen(req, timeout=timeout)


def is_direct_file(url: str) -> bool:
    """True when the URL looks like a plain file rather than a media page."""
    try:
        with head_request(url) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if ctype and "text/html" not in ctype and "application/xhtml" not in ctype:
                return True
    except Exception:
        pass
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    return ext in DIRECT_FILE_EXTS
