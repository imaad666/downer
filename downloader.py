"""Top-level download orchestration."""

import os
import urllib.parse

from audio import download_audio
from errors import DownloadError
from net import is_direct_file
from sanitize import sanitize_filename
from video import download_video


def download(url: str, mode: str, fmt: str):
    """
    Returns either:
      ("file", path, filename, media_type)  — server-generated file to stream back
      ("json", payload)                     — redirect payload for the browser
    """
    mode = mode or "audio"
    fmt = fmt or "mp3"

    # Plain files: hand the URL straight to the browser.
    if mode == "file" or is_direct_file(url):
        name = sanitize_filename(
            os.path.basename(urllib.parse.urlparse(url).path) or "download"
        )
        return "json", {"kind": "redirect", "download_url": url, "filename": name}

    if mode == "audio":
        path, filename, media_type = download_audio(url, fmt)
    else:
        path, filename, media_type = download_video(url, fmt)

    return "file", path, filename, media_type
