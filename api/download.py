import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import downloader
from errors import DownloadError
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

    try:
        result = downloader.download(url, req.mode, req.format)
    except DownloadError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if result[0] == "json":
        return JSONResponse(result[1])

    _, path, filename, media_type = result
    return FileResponse(path, filename=filename, media_type=media_type)
