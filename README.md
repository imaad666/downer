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

## YouTube bot-check / cookies

YouTube sometimes blocks datacenter IPs with
`Sign in to confirm you're not a bot`. To fix it, give yt-dlp your browser
cookies via a Vercel environment variable:

1. Install a cookies export extension (e.g. "Get cookies.txt LOCALLY") in
   Chrome/Firefox and export cookies for youtube.com.
2. In Vercel → project **idowner** → Settings → Environment Variables, add:

   | Name | Value |
   | --- | --- |
   | `YTDLP_COOKIES` | full contents of the exported `cookies.txt` |

3. Redeploy (push any commit or run `vercel redeploy`).

The app reads `YTDLP_COOKIES` at runtime and writes it to a temp file for
yt-dlp. Never commit cookies to the repo.
