from typing import Optional
from pydantic import BaseModel

class InspectRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    mode: Optional[str] = "audio"     # "audio" | "video" | "raw"
    format: Optional[str] = "mp3"    # "mp3" | "wav" | "flac" | "m4a" | "mp4_best" | "mp4_1080" | "mp4_720" | "raw"
    title: Optional[str] = None
    thumbnail: Optional[str] = None
