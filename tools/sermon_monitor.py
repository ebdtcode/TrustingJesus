#!/usr/bin/env python3
"""Automated YouTube sermon monitor and processor.

Runs on a local VM to bypass YouTube's cloud IP blocking of yt-dlp.

Flow:
  1. Check YouTube RSS feeds for new videos from configured channels
  2. Download audio locally with yt-dlp (residential/VM IP)
  3. Upload compressed audio to Azure Blob Storage
  4. Trigger Azure Function for transcription + content generation
  5. Track processed videos in a local state file

Usage:
    python3 sermon_monitor.py                           # Check + process new videos
    python3 sermon_monitor.py --dry-run                 # Check only, no processing
    python3 sermon_monitor.py --url "https://..."       # Process a specific video
    python3 sermon_monitor.py --url "https://..." --speaker "Name"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
STATE_FILE = SCRIPT_DIR / ".sermon_monitor_state.json"
CHANNELS_FILE = PROJECT_ROOT / "azure-functions" / "config" / "channels.json"

AZURE_FUNC_URL = os.environ.get("AZURE_FUNCTION_URL", "")
AZURE_FUNC_KEY = os.environ.get("AZURE_FUNCTION_KEY", "")
AZURE_STORAGE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
BLOB_CONTAINER = os.environ.get("BLOB_CONTAINER", "sermon-audio")

# yt-dlp cookie options
COOKIES_FILE = os.environ.get("YTDLP_COOKIES_FILE", "")
COOKIES_BROWSER = os.environ.get("YTDLP_COOKIES_BROWSER", "")

MAX_VIDEOS_PER_RUN = int(os.environ.get("MAX_VIDEOS_PER_RUN", "3"))
AUDIO_QUALITY = os.environ.get("AUDIO_QUALITY", "32K")
LOG_FILE = os.environ.get("SERMON_MONITOR_LOG", "")

YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger("sermon_monitor")


def setup_logging(log_file: str = "") -> None:
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"processed": {}, "last_check": ""}


def save_state(state: dict) -> None:
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# YouTube RSS
# ---------------------------------------------------------------------------


def load_channels() -> list[dict]:
    if not CHANNELS_FILE.exists():
        log.error("Channels config not found: %s", CHANNELS_FILE)
        return []
    data = json.loads(CHANNELS_FILE.read_text())
    return [ch for ch in data.get("channels", []) if ch.get("enabled", True)]


def fetch_rss(channel_id: str) -> list[dict]:
    url = f"{YOUTUBE_RSS_URL}?channel_id={channel_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel_title = ""
    title_el = root.find("atom:title", ATOM_NS)
    if title_el is not None and title_el.text:
        channel_title = title_el.text

    videos = []
    for entry in root.findall("atom:entry", ATOM_NS):
        vid_el = entry.find("yt:videoId", ATOM_NS)
        t_el = entry.find("atom:title", ATOM_NS)
        pub_el = entry.find("atom:published", ATOM_NS)

        if vid_el is None or t_el is None:
            continue

        title = t_el.text or ""

        videos.append({
            "video_id": vid_el.text or "",
            "title": title,
            "published_at": pub_el.text if pub_el is not None else "",
            "channel_id": channel_id,
            "channel_title": channel_title,
        })
    return videos


def apply_content_filter(video: dict, filters: dict) -> bool:
    title = video.get("title", "").lower()
    must_not = filters.get("title_must_not_contain", [])
    if any(word.lower() in title for word in must_not):
        return False
    must = filters.get("title_must_contain", [])
    if must and not any(word.lower() in title for word in must):
        return False
    return True


def check_new_videos(state: dict) -> list[dict]:
    channels = load_channels()
    if not channels:
        return []

    processed_ids = set(state.get("processed", {}).keys())
    new_videos = []

    for ch in channels:
        channel_id = ch["id"]
        log.info("Checking channel: %s (%s)", ch.get("name", ""), channel_id)

        try:
            videos = fetch_rss(channel_id)
        except Exception as e:
            log.error("Failed to check channel %s: %s", channel_id, e)
            continue

        content_filter = ch.get("content_filter", {})
        count = 0
        for v in videos:
            if v["video_id"] in processed_ids:
                continue
            if not apply_content_filter(v, content_filter):
                log.info("Filtered out: %s", v["title"])
                continue
            v["default_speaker"] = ch.get("default_speaker", "")
            v["default_series"] = ch.get("default_series", "")
            new_videos.append(v)
            count += 1

        log.info("  %d videos fetched, %d new", len(videos), count)

    return new_videos


# ---------------------------------------------------------------------------
# YouTube URL parsing (for --url mode)
# ---------------------------------------------------------------------------


def extract_video_id(url: str) -> str:
    url = url.strip()
    if len(url) == 11 and url.replace("-", "").replace("_", "").isalnum():
        return url

    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path or ""

    if "youtu.be" in host:
        return path.lstrip("/").split("/")[0].split("?")[0]

    if "youtube.com" in host:
        if "/watch" in path:
            qs = parse_qs(parsed.query)
            return qs.get("v", [""])[0]
        for prefix in ("/embed/", "/v/", "/shorts/", "/live/"):
            if path.startswith(prefix):
                return path[len(prefix):].split("/")[0].split("?")[0]

    return ""


# ---------------------------------------------------------------------------
# Audio download
# ---------------------------------------------------------------------------


def download_audio(video_id: str, tmp_dir: str) -> tuple[str, dict]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--format", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", AUDIO_QUALITY,
        "--postprocessor-args", "ffmpeg:-ac 1",
        "--output", f"{tmp_dir}/%(id)s.%(ext)s",
        "--print-json",
        "--no-simulate",
    ]

    # Add cookie auth
    if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
    elif COOKIES_BROWSER:
        cmd.extend(["--cookies-from-browser", COOKIES_BROWSER])

    cmd.append(url)
    log.info("Downloading audio for %s ...", video_id)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[:500]}")

    meta = json.loads(result.stdout.strip().split("\n")[-1])

    audio_file = ""
    for f in os.listdir(tmp_dir):
        if f.endswith(".mp3"):
            audio_file = os.path.join(tmp_dir, f)
            break

    if not audio_file:
        raise FileNotFoundError("No mp3 file produced by yt-dlp")

    size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    log.info("  Downloaded: %.1f MB", size_mb)

    if size_mb > 25:
        log.warning("  Audio is %.1f MB (>25 MB Whisper limit). May need lower quality.", size_mb)

    return audio_file, meta


# ---------------------------------------------------------------------------
# Azure Blob upload
# ---------------------------------------------------------------------------


def upload_to_blob(audio_file: str, blob_name: str) -> None:
    from azure.storage.blob import BlobServiceClient

    log.info("Uploading %s to blob storage...", blob_name)
    client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONN)
    blob = client.get_blob_client(BLOB_CONTAINER, blob_name)
    with open(audio_file, "rb") as f:
        blob.upload_blob(f, overwrite=True)
    log.info("  Uploaded to %s/%s", BLOB_CONTAINER, blob_name)


# ---------------------------------------------------------------------------
# Azure Function call
# ---------------------------------------------------------------------------


def call_process(payload: dict) -> dict:
    url = f"{AZURE_FUNC_URL}/api/process?code={AZURE_FUNC_KEY}"
    log.info("Calling Azure Function to process...")

    resp = requests.post(url, json=payload, timeout=600)
    data = resp.json()

    if resp.status_code == 200 and data.get("status") == "success":
        log.info("  Processing succeeded! Commit: %s", data.get("commit", "")[:8])
        log.info("  Files: %s", ", ".join(data.get("files", [])))
    else:
        log.error("  Processing failed (HTTP %d): %s",
                   resp.status_code, data.get("error", str(data)))

    return data


# ---------------------------------------------------------------------------
# Process a single video
# ---------------------------------------------------------------------------


def delete_blob(blob_name: str) -> None:
    """Delete a blob from Azure Storage (cleanup after processing)."""
    from azure.storage.blob import BlobServiceClient

    try:
        client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONN)
        blob = client.get_blob_client(BLOB_CONTAINER, blob_name)
        blob.delete_blob()
        log.info("  Deleted blob %s/%s", BLOB_CONTAINER, blob_name)
    except Exception as e:
        log.warning("  Failed to delete blob %s: %s", blob_name, e)


def process_video(
    video_id: str,
    speaker: str = "",
    category: str = "sermon",
    title: str = "",
    upload_date: str = "",
) -> dict:
    tmp_dir = tempfile.mkdtemp(prefix="sermon_")
    blob_name = f"{video_id}.mp3"
    blob_uploaded = False
    try:
        audio_file, meta = download_audio(video_id, tmp_dir)
        upload_to_blob(audio_file, blob_name)
        blob_uploaded = True

        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "speaker": speaker or meta.get("uploader", ""),
            "category": category,
            "audio_blob": blob_name,
            "title": title or meta.get("title", ""),
            "upload_date": upload_date or meta.get("upload_date", ""),
        }

        result = call_process(payload)
        return result

    finally:
        # Always clean up local temp files
        shutil.rmtree(tmp_dir, ignore_errors=True)
        # Clean up blob (Azure Function also attempts this, but belt-and-suspenders)
        if blob_uploaded:
            delete_blob(blob_name)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def validate_config() -> list[str]:
    errors = []
    if not AZURE_FUNC_URL:
        errors.append("AZURE_FUNCTION_URL is not set")
    if not AZURE_FUNC_KEY:
        errors.append("AZURE_FUNCTION_KEY is not set")
    if not AZURE_STORAGE_CONN:
        errors.append("AZURE_STORAGE_CONNECTION_STRING is not set")
    if not shutil.which("yt-dlp"):
        errors.append("yt-dlp is not installed")
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg is not installed")
    if not COOKIES_FILE and not COOKIES_BROWSER:
        log.warning("No cookie auth configured — yt-dlp may be blocked by YouTube")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated YouTube sermon monitor")
    parser.add_argument("--url", help="Process a specific YouTube video URL")
    parser.add_argument("--speaker", default="", help="Speaker name override")
    parser.add_argument("--category", default="sermon", help="Content category")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't process")
    parser.add_argument("--env-file", help="Path to .env file")
    args = parser.parse_args()

    # Load .env file if specified or if one exists next to the script
    env_file = args.env_file or str(SCRIPT_DIR / "sermon_monitor.env")
    if os.path.isfile(env_file):
        log.info("Loading env from %s", env_file)
        _load_env_file(env_file)

    setup_logging(LOG_FILE or os.environ.get("SERMON_MONITOR_LOG", ""))

    errors = validate_config()
    if errors:
        for e in errors:
            log.error("Config error: %s", e)
        return 1

    # Single video mode
    if args.url:
        video_id = extract_video_id(args.url)
        if not video_id:
            log.error("Could not extract video ID from: %s", args.url)
            return 1

        log.info("Processing single video: %s", video_id)
        result = process_video(video_id, speaker=args.speaker, category=args.category)
        return 0 if result.get("status") == "success" else 1

    # Monitor mode — check channels for new videos
    state = load_state()
    new_videos = check_new_videos(state)

    if not new_videos:
        log.info("No new videos found.")
        save_state(state)
        return 0

    log.info("Found %d new video(s)", len(new_videos))

    if args.dry_run:
        for v in new_videos:
            log.info("  [DRY RUN] %s — %s", v["video_id"], v["title"])
        return 0

    # Process up to MAX_VIDEOS_PER_RUN
    to_process = new_videos[:MAX_VIDEOS_PER_RUN]
    success = 0
    failed = 0

    for v in to_process:
        vid = v["video_id"]
        log.info("--- Processing: %s (%s) ---", v["title"], vid)
        try:
            result = process_video(
                vid,
                speaker=v.get("default_speaker", ""),
                category="sermon",
                title=v.get("title", ""),
            )
            if result.get("status") == "success":
                state.setdefault("processed", {})[vid] = {
                    "title": v.get("title", ""),
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "commit": result.get("commit", ""),
                }
                success += 1
            else:
                state.setdefault("processed", {})[vid] = {
                    "title": v.get("title", ""),
                    "status": "failed",
                    "error": result.get("error", ""),
                    "attempted_at": datetime.now(timezone.utc).isoformat(),
                }
                failed += 1

        except Exception as e:
            log.error("Error processing %s: %s", vid, e)
            state.setdefault("processed", {})[vid] = {
                "title": v.get("title", ""),
                "status": "failed",
                "error": str(e),
                "attempted_at": datetime.now(timezone.utc).isoformat(),
            }
            failed += 1

        # Save state after each video in case of crash
        save_state(state)

    log.info("=== Done: %d succeeded, %d failed ===", success, failed)
    return 0 if failed == 0 else 1


def _load_env_file(path: str) -> None:
    """Load KEY=VALUE lines from a file into os.environ."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:  # Don't override existing env
                    os.environ[key] = value
    # Reload module-level vars that read from env
    global AZURE_FUNC_URL, AZURE_FUNC_KEY, AZURE_STORAGE_CONN, BLOB_CONTAINER
    global COOKIES_FILE, COOKIES_BROWSER, MAX_VIDEOS_PER_RUN, AUDIO_QUALITY, LOG_FILE
    AZURE_FUNC_URL = os.environ.get("AZURE_FUNCTION_URL", "")
    AZURE_FUNC_KEY = os.environ.get("AZURE_FUNCTION_KEY", "")
    AZURE_STORAGE_CONN = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    BLOB_CONTAINER = os.environ.get("BLOB_CONTAINER", "sermon-audio")
    COOKIES_FILE = os.environ.get("YTDLP_COOKIES_FILE", "")
    COOKIES_BROWSER = os.environ.get("YTDLP_COOKIES_BROWSER", "")
    MAX_VIDEOS_PER_RUN = int(os.environ.get("MAX_VIDEOS_PER_RUN", "3"))
    AUDIO_QUALITY = os.environ.get("AUDIO_QUALITY", "32K")
    LOG_FILE = os.environ.get("SERMON_MONITOR_LOG", "")


if __name__ == "__main__":
    sys.exit(main())
