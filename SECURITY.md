# Security Policy

## Reporting a vulnerability

Please do not open public issues for security vulnerabilities.
Email the maintainer directly or use GitHub's private vulnerability
reporting (Security → Report a vulnerability) on this repository.

## Scope

- `api/` serverless functions and `downloader.py` pipeline
- The `public/` frontend (no user data is stored or transmitted beyond
  the URLs you submit)

## Notes

- No accounts, cookies, or persistent storage are used.
- Downloads are processed ephemerally inside Vercel functions.
