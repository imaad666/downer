# iOS Shortcut — Downer

Adds a share-sheet shortcut that downloads media through your deployed site
(`https://idowner.vercel.app`). Share any link (YouTube, SoundCloud, TikTok,
direct file, …) → pick a format → file saves to the Shortcuts output / Files.

## Build it (≈2 minutes)

1. Open **Shortcuts** → tap **+** (top right) → name it `Downer`.
2. Tap the shortcut name/settings icon → enable **Show in Share Sheet** and
   set **Receives** to `URLs`.
3. Add these actions in order:

### Action 1 — Choose from Menu
Add **Choose from Menu** with three options:

- `Audio (MP3)`
- `Video (MP4)`
- `Direct File`

### Inside each menu option

**Audio (MP3)** and **Video (MP4)** branches:

1. **Get Contents of URL**
   - URL: `https://idowner.vercel.app/api/download`
   - Method: `POST`
   - Request Body: `JSON`
     ```json
     { "url": "SHORTCUT INPUT", "mode": "audio", "format": "mp3" }
     ```
     (for Video use `"mode": "video", "format": "mp4_720"`)
   - Headers: `Content-Type: application/json`
2. **Save File**
   - File: *Contents of URL* from the previous action
   - Where: *Ask Each Time* (or iCloud Drive → Downloads)

**Direct File** branch:

1. **Get Contents of URL**
   - URL: `https://idowner.vercel.app/api/download`
   - Method: `POST`, Request Body `JSON`:
     ```json
     { "url": "SHORTCUT INPUT", "mode": "file" }
     ```
   - Headers: `Content-Type: application/json`
   - This returns JSON like `{"download_url": "...", "filename": "..."}`
2. **Get Dictionary Value** → key `download_url` from the JSON
3. **Get Contents of URL** → GET that `download_url`
4. **Save File** → save to Downloads

> Tip: to get a nice filename for audio/video, first call
> `POST /api/inspect` with `{"url": "SHORTCUT INPUT"}`, read the `title`
> dictionary value, and pass it as the filename in **Save File**.

## Use it

- In Safari/YouTube/TikTok → Share → **Downer** → pick a format → file saves.
- Or run it from the Shortcuts app and paste a link when prompted.

## Notes

- Downloads run through Vercel functions (max ~5 min). Long videos may fail —
  use Audio or a shorter clip.
- If the site URL changes, update every `Get Contents of URL` action.
