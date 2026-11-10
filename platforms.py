"""Platform detection from URL."""


def detect_platform(url: str) -> str:
    u = url.lower()
    if "soundcloud.com" in u:
        return "SoundCloud"
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube"
    if "tiktok.com" in u:
        return "TikTok"
    if "twitter.com" in u or "x.com" in u:
        return "Twitter / X"
    if "instagram.com" in u:
        return "Instagram"
    if "reddit.com" in u or "v.redd.it" in u:
        return "Reddit"
    if "twitch.tv" in u:
        return "Twitch"
    if "vimeo.com" in u:
        return "Vimeo"
    if "bilibili.com" in u:
        return "Bilibili"
    return "Direct / Web"
