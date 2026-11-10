import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import downloader
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class DownloadRequest(BaseModel):
    url: str
    mode: str = "audio"      # "audio" | "video" | "file"
    format: str = "mp3"      # "mp3" | "wav" | "flac" | "m4a" | "mp4_best" | "mp4_1080" | "mp4_720" | "raw"
    title: str | None = None


@app.api_route("/", methods=["POST"])
@app.api_route("/{path:path}", methods=["POST"])
def download(req: DownloadRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    mode = req.mode or "audio"
    fmt = req.format or "mp3"

    # Plain files: hand the URL straight to the browser.
    if mode == "file" or downloader.is_direct_file(url):
        name = downloader.sanitize_filename(
            os.path.basename(urllib.parse.urlparse(url).path) or "download"
        )
        return JSONResponse({"kind": "redirect", "download_url": url, "filename": name})

    try:
        if mode == "audio":
            path, filename, media_type = downloader.download_audio(url, fmt)
        else:
            path, filename, media_type = downloader.download_video(url, fmt)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return FileResponse(path, filename=filename, media_type=media_type)
