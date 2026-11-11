"""Audio download + conversion via yt-dlp/ffmpeg."""

import os
import subprocess
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
    # Embed cover art + tags where the container supports it (wav cannot).
    if codec in ("mp3", "m4a", "flac"):
        postprocessors.append({"key": "EmbedThumbnail"})
        postprocessors.append({"key": "FFmpegMetadata"})

    ydl_opts = ydl_base_opts(
        format="bestaudio/best",
        outtmpl=outtmpl,
        postprocessors=postprocessors,
        ffmpeg_location=FFMPEG_PATH,
        writethumbnail=True,
    )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        raise DownloadError(f"Download failed: {str(e)[:200]}")

    filename = f"{sanitize_filename(info.get('title') or 'audio')}.{codec}"
    out = _pick_output(tmpdir, codec)

    # Windows Explorer reads ID3v2.3 far more reliably than v2.4 — remux MP3s.
    if codec == "mp3":
        out = _remux_id3v23(out)

    return out, filename, MEDIA_TYPES.get(codec, "application/octet-stream")


def _remux_id3v23(path: str) -> str:
    dst = path + ".v23.mp3"
    try:
        subprocess.run(
            [
                FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
                "-i", path, "-map", "0", "-c", "copy", "-id3v2_version", "3", dst,
            ],
            check=True,
            capture_output=True,
        )
        os.replace(dst, path)
    except Exception:
        pass  # keep the v2.4 file rather than fail the download
    return path


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
