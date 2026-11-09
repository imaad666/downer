# Architecture Overview

Downer operates as a lightweight local web server with a reactive frontend:
- **FastAPI / Uvicorn**: Async API server handling URL inspection, streaming, and queueing.
- **yt-dlp**: Universal multi-platform media and stream extractor.
- **imageio-ffmpeg**: Embedded high-performance FFmpeg binary for audio transcoding (MP3 320k, WAV, FLAC) and video container muxing.
- **Cobalt-Style Frontend**: Minimalist single-page application communicating over REST endpoints.
