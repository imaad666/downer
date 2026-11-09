# downer

Minimal, cobalt-inspired media downloader. Paste a link, pick audio/video/file, get the download.

## Stack

- **Frontend**: single-file HTML/CSS/JS in `public/index.html`
- **Backend**: FastAPI serverless functions (`app.py`) on Vercel
- **Engine**: `yt-dlp` + `ffmpeg` (via `imageio-ffmpeg`)

## Endpoints

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Web UI |
| `/api/inspect` | POST | Fetch media metadata for a URL |
| `/api/download` | POST | Download/convert and return the file |

## Local development

```bash
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:8000
```

## Deploy

```bash
vercel deploy --prod
```

Or connect the GitHub repo in the Vercel dashboard — no build step is required.

## Notes

- Audio downloads are converted server-side (MP3 320k / WAV / FLAC / M4A).
- Video links resolve to a direct stream and are proxied through the function.
- Direct file links (zip, pdf, mp3, …) are handed to the browser as-is.
- Vercel functions have a max duration (300s on Hobby); very long videos may time out.
