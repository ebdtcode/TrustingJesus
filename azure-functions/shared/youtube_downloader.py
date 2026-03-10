"""Download audio from YouTube using yt-dlp."""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


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

    logger.info("Downloading audio from: %s", url)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

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
