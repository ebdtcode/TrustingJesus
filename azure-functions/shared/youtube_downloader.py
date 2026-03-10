"""Download audio from YouTube using yt-dlp.

Supports YouTube cookie authentication via the YOUTUBE_COOKIES env var
(base64-encoded Netscape cookie file) to bypass bot detection on cloud servers.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def _write_cookies_file(tmp_dir: str) -> Optional[str]:
    """Decode YOUTUBE_COOKIES env var to a temp file. Returns path or None."""
    cookies_b64 = os.environ.get("YOUTUBE_COOKIES", "")
    if not cookies_b64:
        return None
    try:
        cookies_bytes = base64.b64decode(cookies_b64)
        cookies_path = os.path.join(tmp_dir, "cookies.txt")
        with open(cookies_path, "wb") as f:
            f.write(cookies_bytes)
        logger.info("Using YouTube cookies from YOUTUBE_COOKIES env var")
        return cookies_path
    except Exception as e:
        logger.warning("Failed to decode YOUTUBE_COOKIES: %s", e)
        return None


def download_audio(
    url: str,
    *,
    output_dir: Optional[str] = None,
    format: str = "mp3",
    quality: str = "128",
) -> tuple[str, dict]:
    """Download audio from a YouTube URL.

    Returns:
        Tuple of (audio_file_path, metadata_dict)
        metadata_dict keys: title, uploader, upload_date, duration, description, id
    """
    import yt_dlp

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="sermon_audio_")

    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": format,
                "preferredquality": quality,
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    cookies_path = _write_cookies_file(output_dir)
    if cookies_path:
        ydl_opts["cookiefile"] = cookies_path

    # PO token for YouTube bot bypass (set YOUTUBE_PO_TOKEN env var)
    po_token = os.environ.get("YOUTUBE_PO_TOKEN", "")
    if po_token:
        ydl_opts.setdefault("extractor_args", {})["youtube"] = [
            f"po_token=web+{po_token}"
        ]

    logger.info("Downloading audio from: %s", url)

    # Try download with fallback client strategies
    strategies = [
        {},  # default
        {"extractor_args": {"youtube": {"player_client": ["mediaconnect"]}}},
        {"extractor_args": {"youtube": {"player_client": ["web_creator"]}}},
    ]

    last_error = None
    for i, extra_opts in enumerate(strategies):
        try:
            merged = {**ydl_opts, **extra_opts}
            with yt_dlp.YoutubeDL(merged) as ydl:
                info = ydl.extract_info(url, download=True)
            break
        except Exception as e:
            last_error = e
            logger.warning("Download strategy %d failed: %s", i + 1, e)
    else:
        raise RuntimeError(f"All download strategies failed: {last_error}")

    video_id = info.get("id", "unknown")
    audio_path = os.path.join(output_dir, f"{video_id}.{format}")

    # yt-dlp may produce a slightly different filename
    if not os.path.exists(audio_path):
        for f in os.listdir(output_dir):
            if f.endswith(f".{format}"):
                audio_path = os.path.join(output_dir, f)
                break

    metadata = {
        "id": video_id,
        "title": info.get("title", ""),
        "uploader": info.get("uploader", ""),
        "upload_date": info.get("upload_date", ""),
        "duration": info.get("duration", 0),
        "description": info.get("description", ""),
        "webpage_url": info.get("webpage_url", url),
    }

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    logger.info(
        "Downloaded: %s (%.1f MB, %d sec)",
        metadata["title"],
        file_size_mb,
        metadata["duration"],
    )

    return audio_path, metadata
