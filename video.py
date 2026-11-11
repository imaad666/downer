"""Video download + merge via yt-dlp/ffmpeg."""

import os

import yt_dlp
import imageio_ffmpeg

from errors import DownloadError
from net import ydl_base_opts
from sanitize import sanitize_filename

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

MEDIA_TYPES = {
    "mp4": "video/mp4",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
    "mov": "video/quicktime",
}

VIDEO_EXTS = (".mp4", ".mkv", ".webm", ".mov")


def _format_string(fmt: str) -> str:
    height = {"mp4_720": 720, "mp4_1080": 1080}.get(fmt)
    if height:
        return (
            f"bestvideo[height<={height}][ext=mp4][vcodec!*=none]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height}]+bestaudio/"
            f"best[height<={height}]/best"
        )
    return "bestvideo[ext=mp4][vcodec!*=none]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"


def download_video(url: str, fmt: str):
    """Returns (file_path, filename, media_type)."""
    import tempfile

    tmpdir = tempfile.mkdtemp(prefix="dlv_")
    outtmpl = os.path.join(tmpdir, "%(title).80s.%(ext)s")

    postprocessors = [{"key": "FFmpegMetadata"}]

    ydl_opts = ydl_base_opts(
        format=_format_string(fmt),
        outtmpl=outtmpl,
        merge_output_format="mp4",
        postprocessors=postprocessors,
        ffmpeg_location=FFMPEG_PATH,
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        raise DownloadError(f"Download failed: {str(e)[:200]}")

    produced = [
        os.path.join(tmpdir, f)
        for f in os.listdir(tmpdir)
        if f.lower().endswith(VIDEO_EXTS)
    ]
    if not produced:
        produced = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
    if not produced:
        raise DownloadError("Download produced no file")

    path = produced[0]
    ext = os.path.splitext(path)[1].lstrip(".") or "mp4"
    filename = f"{sanitize_filename(info.get('title') or 'video')}.{ext}"
    return path, filename, MEDIA_TYPES.get(ext, "application/octet-stream")
