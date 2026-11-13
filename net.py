"""HTTP helpers and yt-dlp option factory."""

import base64
import os
import tempfile
import urllib.request
import urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

DIRECT_FILE_EXTS = (
    ".zip", ".rar", ".7z", ".tar", ".gz", ".pdf", ".iso",
    ".exe", ".dmg", ".apk", ".mp3", ".mp4", ".wav", ".flac",
)


def _looks_like_netscape_cookies(content: str) -> bool:
    """True when content has a Netscape header or at least one 7-field cookie line."""
    has_entry = False
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            lowered = line.lower()
            if "netscape" in lowered or "http cookie file" in lowered:
                return True
            continue
        # Netscape cookie lines are 7 tab-separated fields.
        if line.count("\t") >= 6:
            parts = line.split("\t")
            if len(parts) >= 7 and parts[0]:
                has_entry = True
    return has_entry


def _decode_cookie_env(content: str) -> str:
    """Decode YTDLP_COOKIES, accepting plain text or base64."""
    content = content.strip()
    if _looks_like_netscape_cookies(content.replace("\\n", "\n")):
        return content.replace("\\n", "\n")

    # Only attempt base64 when the value does not already look like cookies.
    try:
        decoded = base64.b64decode(content, validate=True).decode("utf-8")
        return decoded.replace("\\n", "\n")
    except Exception:
        return content.replace("\\n", "\n")


def cookie_file():
    """Write YTDLP_COOKIES env content to a temp cookies.txt, return its path.

    Returns None when unset or when the value is not a valid Netscape cookies file,
    so a bad Vercel env var cannot break every download.
    """
    raw = os.environ.get("YTDLP_COOKIES", "").strip()
    if not raw:
        return None

    content = _decode_cookie_env(raw)
    if not _looks_like_netscape_cookies(content):
        return None

    path = os.path.join(tempfile.gettempdir(), "yt_dlp_cookies.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")
    return path


def ydl_base_opts(**extra):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 8,
        "http_headers": {"User-Agent": UA},
    }
    cookies = cookie_file()
    if cookies:
        # Cookie-capable clients. Android clients ignore account cookies.
        opts["cookiefile"] = cookies
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["web", "web_safari", "tv"],
            }
        }
    else:
        # Datacenter IPs often fail the webpage bot-check; skip it and use
        # innertube clients that still serve public formats without cookies.
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["android_vr", "android"],
                "player_skip": ["webpage", "configs"],
            }
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
