# downer

Minimal, cobalt-inspired media downloader. Paste a link, pick audio/video/file, get the download.

## Stack

- **Frontend**: single-file HTML/CSS/JS in `public/index.html` (served statically)
- **Backend**: Python serverless functions on Vercel
  - `api/inspect.py` → `POST /api/inspect` (media metadata)
  - `api/download.py` → `POST /api/download` (download/convert, returns the file)
- **Shared logic**: `downloader.py` (`yt-dlp` + `ffmpeg` via `imageio-ffmpeg`)

## Local development

```bash
npx vercel dev
# or: pip install -r requirements.txt && python -m http.server 8000 -d public
```

## Deploy

```bash
vercel deploy --prod
```

Live at: https://idowner.vercel.app

## iOS Shortcut

See `IOS_SHORTCUT.md` for share-sheet setup.

## Notes

- Audio downloads are converted server-side (MP3 320k / WAV / FLAC / M4A).
- Video links are downloaded and merged server-side.
- Direct file links (zip, pdf, mp3, …) are handed to the browser as-is.
- Vercel functions have a max duration (~5 min on Hobby); very long videos may time out.
