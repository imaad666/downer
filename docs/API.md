# API Specification

- `POST /api/inspect`: Inspects URL metadata and detects provider platform.
- `POST /api/download`: Pushes download/transcode task to thread-safe worker queue.
- `GET /api/queue`: Polls real-time download and conversion progress.
- `POST /api/open-downloads-folder`: Opens local output directory in OS File Explorer.
- `GET /api/download-file/{filename}`: Streams finished asset to browser client.
