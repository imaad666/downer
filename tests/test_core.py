import downloader
from platforms import detect_platform
from sanitize import sanitize_filename
from duration import format_duration


def test_sanitize_strips_illegal_chars():
    assert sanitize_filename('a/b\\c:d*e?f"g<h>i|j') == "abcdefghij"


def test_sanitize_collapses_whitespace():
    assert sanitize_filename("  hello   world  ") == "hello world"


def test_sanitize_empty_fallback():
    assert sanitize_filename("") == "download"
    assert sanitize_filename("   ") == "download"


def test_sanitize_truncates_long_names():
    assert len(sanitize_filename("x" * 300)) == 100


def test_detect_platform_known_sites():
    assert detect_platform("https://www.youtube.com/watch?v=x") == "YouTube"
    assert detect_platform("https://youtu.be/x") == "YouTube"
    assert detect_platform("https://soundcloud.com/a/b") == "SoundCloud"
    assert detect_platform("https://x.com/user/status/1") == "Twitter / X"
    assert detect_platform("https://v.redd.it/abc") == "Reddit"


def test_detect_platform_unknown():
    assert detect_platform("https://example.com/file.zip") == "Direct / Web"


def test_format_duration_variants():
    assert format_duration(None) == ""
    assert format_duration(0) == ""
    assert format_duration(65) == "1:05"
    assert format_duration(3661) == "1:01:01"
