"""Audio download + conversion via yt-dlp/ffmpeg."""

import os
import tempfile

import yt_dlp
import imageio_ffmpeg

from errors import DownloadError
from net import ydl_base_opts
from sanitize import sanitize_filename

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

MEDIA_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
}


def _new_tmpdir(prefix="dl_"):
    return tempfile.mkdtemp(prefix=prefix)


def download_audio(url: str, fmt: str):
    """Returns (file_path, filename, media_type)."""
    codec = fmt if fmt in ("wav", "flac", "m4a") else "mp3"
    tmpdir = _new_tmpdir()
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
        raise DownloadError(f"Download failed: {str(e)[:200]}")

    filename = f"{sanitize_filename(info.get('title') or 'audio')}.{codec}"
    return _pick_output(tmpdir, codec), filename, MEDIA_TYPES.get(codec, "application/octet-stream")


def _pick_output(tmpdir: str, ext: str):
    produced = [
        os.path.join(tmpdir, f)
        for f in os.listdir(tmpdir)
        if f.lower().endswith(f".{ext}")
    ]
    if not produced:
        produced = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    if not produced:
        raise DownloadError("Conversion produced no file")
    return produced[0]
