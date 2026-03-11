#!/usr/bin/env python3
"""Pure local sermon processing pipeline — no Azure dependency.

Downloads audio with yt-dlp, transcribes with faster-whisper, generates
content with Claude (Anthropic API), renders Reveal.js slides, and commits
to GitHub. Everything runs on the local VM.

Usage:
    python3 sermon_local.py                                 # Monitor + process new videos
    python3 sermon_local.py --dry-run                       # Check RSS only
    python3 sermon_local.py --url "https://youtu.be/..."    # Process a specific video
    python3 sermon_local.py --url "..." --speaker "Name"    # With speaker override

Requires:
    pip install faster-whisper anthropic PyGithub requests yt-dlp
    System: ffmpeg, yt-dlp
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

# ---------------------------------------------------------------------------
# Add azure-functions/shared to import path (reuse prompts, templates, etc.)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AZURE_FUNC_DIR = PROJECT_ROOT / "azure-functions"

sys.path.insert(0, str(AZURE_FUNC_DIR))

from shared.content_generator import (  # noqa: E402
    generate_prayer_points,
    generate_slides_json,
    generate_summary,
)
from shared.template_engine import render_presentation  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STATE_FILE = SCRIPT_DIR / ".sermon_local_state.json"
CHANNELS_FILE = AZURE_FUNC_DIR / "config" / "channels.json"

# LLM (Claude)
LLM_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")

# GitHub
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

# Whisper (local)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "auto")
WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE", "auto")

# yt-dlp
COOKIES_FILE = os.environ.get("YTDLP_COOKIES_FILE", "")
COOKIES_BROWSER = os.environ.get("YTDLP_COOKIES_BROWSER", "")
AUDIO_QUALITY = os.environ.get("AUDIO_QUALITY", "32K")

# Processing
MAX_VIDEOS_PER_RUN = int(os.environ.get("MAX_VIDEOS_PER_RUN", "3"))
CHURCH_NAME = os.environ.get("CHURCH_NAME", "")

YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

log = logging.getLogger("sermon_local")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


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
    t = root.find("atom:title", ATOM_NS)
    if t is not None and t.text:
        channel_title = t.text

    videos = []
    for entry in root.findall("atom:entry", ATOM_NS):
        vid_el = entry.find("yt:videoId", ATOM_NS)
        t_el = entry.find("atom:title", ATOM_NS)
        pub_el = entry.find("atom:published", ATOM_NS)
        if vid_el is None or t_el is None:
            continue
        videos.append({
            "video_id": vid_el.text or "",
            "title": t_el.text or "",
            "published_at": pub_el.text if pub_el is not None else "",
            "channel_id": channel_id,
            "channel_title": channel_title,
        })
    return videos


def apply_content_filter(video: dict, filters: dict) -> bool:
    title = video.get("title", "").lower()
    must_not = filters.get("title_must_not_contain", [])
    if any(w.lower() in title for w in must_not):
        return False
    must = filters.get("title_must_contain", [])
    if must and not any(w.lower() in title for w in must):
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
                log.info("  Filtered: %s", v["title"])
                continue
            v["default_speaker"] = ch.get("default_speaker", "")
            v["default_series"] = ch.get("default_series", "")
            new_videos.append(v)
            count += 1
        log.info("  %d fetched, %d new", len(videos), count)
    return new_videos


# ---------------------------------------------------------------------------
# URL parsing
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
            return parse_qs(parsed.query).get("v", [""])[0]
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
        "--extract-audio", "--audio-format", "mp3",
        "--audio-quality", AUDIO_QUALITY,
        "--postprocessor-args", "ffmpeg:-ac 1",
        "--output", f"{tmp_dir}/%(id)s.%(ext)s",
        "--print-json", "--no-simulate",
    ]
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
    audio_file = next(
        (os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.endswith(".mp3")),
        None,
    )
    if not audio_file:
        raise FileNotFoundError("No mp3 file produced by yt-dlp")

    size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    log.info("  Downloaded: %.1f MB", size_mb)
    return audio_file, meta


# ---------------------------------------------------------------------------
# Local Whisper transcription
# ---------------------------------------------------------------------------


def transcribe_local(audio_path: str, speaker: str = "") -> str:
    """Transcribe using faster-whisper locally."""
    from faster_whisper import WhisperModel

    device = WHISPER_DEVICE
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    compute = WHISPER_COMPUTE
    if compute == "auto":
        compute = "float16" if device == "cuda" else "int8"

    log.info("Loading Whisper model: %s (device=%s, compute=%s)", WHISPER_MODEL, device, compute)
    model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute)

    prompt = f"Sermon by {speaker}" if speaker else "Sermon transcription"
    if CHURCH_NAME:
        prompt += f" at {CHURCH_NAME}"

    log.info("Transcribing %s ...", os.path.basename(audio_path))
    segments, info = model.transcribe(
        audio_path,
        language="en",
        initial_prompt=f"{prompt}.",
        vad_filter=True,
        vad_parameters={
            "min_speech_duration_ms": 250,
            "min_silence_duration_ms": 2000,
            "speech_pad_ms": 400,
        },
        beam_size=5,
        best_of=5,
        temperature=0.0,
    )

    text_parts = [seg.text for seg in segments]
    transcript = "".join(text_parts).strip()
    duration_min = info.duration / 60
    log.info("  Transcribed: %.0f min, %d chars", duration_min, len(transcript))
    return transcript


# ---------------------------------------------------------------------------
# LLM client (Claude via Anthropic SDK)
# ---------------------------------------------------------------------------


def _create_llm_client():
    """Create an LLMClient using the shared module."""
    from shared.config import LLMConfig
    from shared.llm_client import LLMClient

    config = LLMConfig(
        provider=LLM_PROVIDER,
        api_key=LLM_API_KEY,
        model=LLM_MODEL,
    )
    return LLMClient.from_config(config)


# ---------------------------------------------------------------------------
# GitHub client
# ---------------------------------------------------------------------------


def _create_github_client():
    """Create a GitHubClient using the shared module."""
    from shared.config import GitHubConfig
    from shared.github_client import GitHubClient

    config = GitHubConfig(
        token=GITHUB_TOKEN,
        repo=GITHUB_REPO,
        branch=GITHUB_BRANCH,
    )
    return GitHubClient.from_config(config)


# ---------------------------------------------------------------------------
# Helpers (mirrored from function_app.py)
# ---------------------------------------------------------------------------


def _sanitize_title(title: str) -> str:
    for suffix in [
        " - YouTube", " | YouTube", " (Official)", " (Full Sermon)",
        " (Official Video)", " (Full Message)",
    ]:
        title = title.replace(suffix, "")
    return title.strip()


def _safe_filename(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s]+", "_", slug)
    return slug.strip("_")[:80]


def _build_transcript_md(transcript: str, metadata: dict) -> str:
    return f"""---
title: "{metadata['title']}"
speaker: "{metadata['speaker']}"
date: "{metadata['date']}"
series: "{metadata.get('series', '')}"
youtube_url: "{metadata.get('youtube_url', '')}"
---

## Full Transcript

{transcript}
"""


def _inject_presentation_entry(
    js_content: str, slides_json: dict, metadata: dict, safe_title: str,
) -> str:
    category = metadata.get("category", "sermon")
    tags_str = json.dumps(
        [t for t in [category, metadata.get("series", "").lower()] if t]
    )
    js_entry = (
        f'  {{\n'
        f'    title: "{metadata["title"]}",\n'
        f'    speaker: "{metadata["speaker"]}",\n'
        f'    description: "",\n'
        f'    slides: {slides_json.get("total_slides", len(slides_json.get("slides", [])))},\n'
        f'    file: "presentations/{category}/{safe_title}.html",\n'
        f'    id: "{safe_title.lower().replace("_", "-")}",\n'
        f'    category: "{category}",\n'
        f'    icon: "&#128156;",\n'
        f'    tags: {tags_str},\n'
        f'    featured: true,\n'
        f'    date: "{metadata["date"]}"\n'
        f'  }}'
    )
    match = re.search(r"(const\s+presentations\s*=\s*\[)", js_content)
    if match:
        insert_pos = match.end()
        return js_content[:insert_pos] + "\n" + js_entry + ",\n" + js_content[insert_pos:]
    bracket_idx = js_content.index("[")
    return js_content[:bracket_idx + 1] + "\n" + js_entry + ",\n" + js_content[bracket_idx + 1:]


# ---------------------------------------------------------------------------
# Process a single video (full local pipeline)
# ---------------------------------------------------------------------------


def process_video(
    video_id: str,
    speaker: str = "",
    category: str = "sermon",
    series: str = "",
    title: str = "",
    upload_date: str = "",
) -> dict:
    """Full local pipeline: download → transcribe → generate → commit → cleanup."""
    tmp_dir = tempfile.mkdtemp(prefix="sermon_local_")
    try:
        # 1. Download audio
        audio_file, meta = download_audio(video_id, tmp_dir)
        title = _sanitize_title(title or meta.get("title", "Sermon"))
        speaker = speaker or meta.get("uploader", "Unknown")
        raw_date = (upload_date or meta.get("upload_date", "")).replace("-", "")
        if raw_date and len(raw_date) == 8:
            date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        metadata = {
            "title": title,
            "speaker": speaker,
            "date": date_str,
            "series": series,
            "category": category,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "video_id": video_id,
        }

        # 2. Transcribe locally with faster-whisper
        log.info("--- Step 2: Local transcription ---")
        transcript = transcribe_local(audio_file, speaker)

        # Audio no longer needed after transcription — delete immediately
        os.remove(audio_file)
        log.info("  Deleted local audio file")

        # 3. Generate content with Claude
        log.info("--- Step 3: Content generation (Claude) ---")
        llm = _create_llm_client()

        log.info("  Generating summary...")
        summary = generate_summary(llm, transcript, metadata)

        log.info("  Generating prayer points...")
        prayer_points = generate_prayer_points(llm, transcript, summary, metadata)

        log.info("  Generating slides...")
        slides_json = generate_slides_json(llm, transcript, summary, metadata)

        # 4. Render slides HTML
        presentation_html = render_presentation(slides_json)

        # 5. Build transcript markdown
        transcript_md = _build_transcript_md(transcript, metadata)

        # 6. Prepare files for commit
        safe_title = _safe_filename(title)
        year = date_str[:4]

        files = {
            f"transcripts/sermon/{safe_title}/transcript.md": transcript_md,
            f"sermons_summaries/{safe_title}.md": summary,
            f"prayer_points/{year}/Week-{date_str}_{safe_title}.md": prayer_points,
            f"site/v2/presentations/{category}/{safe_title}.html": presentation_html,
        }

        # 7. Update presentations.js catalog
        gh = _create_github_client()
        presentations_js = gh.get_file_content("site/v2/data/presentations.js")
        if presentations_js:
            updated_js = _inject_presentation_entry(
                presentations_js, slides_json, metadata, safe_title
            )
            files["site/v2/data/presentations.js"] = updated_js

        # 8. Commit to GitHub
        log.info("--- Step 4: Committing to GitHub ---")
        commit_msg = f"feat: add sermon '{title}' ({date_str})"
        commit_sha = gh.commit_files(files, commit_msg)

        log.info("  Committed %d files: %s", len(files), commit_sha[:8])
        return {
            "status": "success",
            "commit": commit_sha,
            "title": title,
            "files": list(files.keys()),
            "video_id": video_id,
        }

    finally:
        # Always clean up temp directory (audio + any intermediary files)
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------


def validate_config() -> list[str]:
    errors = []
    if not LLM_API_KEY:
        errors.append("ANTHROPIC_API_KEY (or LLM_API_KEY) is not set")
    if not GITHUB_TOKEN:
        errors.append("GITHUB_TOKEN is not set")
    if not GITHUB_REPO:
        errors.append("GITHUB_REPO is not set")
    if not shutil.which("yt-dlp"):
        errors.append("yt-dlp is not installed")
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg is not installed")
    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError:
        errors.append("faster-whisper is not installed (pip install faster-whisper)")
    if not COOKIES_FILE and not COOKIES_BROWSER:
        log.warning("No cookie auth configured — yt-dlp may be blocked by YouTube")
    return errors


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------


def _load_env_file(path: str) -> None:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value

    # Reload module-level vars
    global LLM_API_KEY, LLM_MODEL, LLM_PROVIDER
    global GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH
    global WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE
    global COOKIES_FILE, COOKIES_BROWSER, AUDIO_QUALITY
    global MAX_VIDEOS_PER_RUN, CHURCH_NAME

    LLM_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
    GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "auto")
    WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE", "auto")
    COOKIES_FILE = os.environ.get("YTDLP_COOKIES_FILE", "")
    COOKIES_BROWSER = os.environ.get("YTDLP_COOKIES_BROWSER", "")
    AUDIO_QUALITY = os.environ.get("AUDIO_QUALITY", "32K")
    MAX_VIDEOS_PER_RUN = int(os.environ.get("MAX_VIDEOS_PER_RUN", "3"))
    CHURCH_NAME = os.environ.get("CHURCH_NAME", "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Pure local sermon processing pipeline")
    parser.add_argument("--url", help="Process a specific YouTube video URL")
    parser.add_argument("--speaker", default="", help="Speaker name override")
    parser.add_argument("--category", default="sermon", help="Content category")
    parser.add_argument("--series", default="", help="Sermon series name")
    parser.add_argument("--dry-run", action="store_true", help="Check only, don't process")
    parser.add_argument("--env-file", help="Path to .env file")
    args = parser.parse_args()

    # Load .env
    env_file = args.env_file or str(SCRIPT_DIR / "sermon_local.env")
    if os.path.isfile(env_file):
        _load_env_file(env_file)

    setup_logging(os.environ.get("SERMON_MONITOR_LOG", ""))

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
        log.info("=== Processing single video: %s ===", video_id)
        result = process_video(
            video_id, speaker=args.speaker, category=args.category, series=args.series,
        )
        if result.get("status") == "success":
            log.info("=== Success! Commit: %s ===", result["commit"][:8])
            for f in result["files"]:
                log.info("  %s", f)
        return 0 if result.get("status") == "success" else 1

    # Monitor mode
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

    to_process = new_videos[:MAX_VIDEOS_PER_RUN]
    success = 0
    failed = 0

    for v in to_process:
        vid = v["video_id"]
        log.info("\n=== Processing: %s (%s) ===", v["title"], vid)
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
        save_state(state)

    log.info("\n=== Done: %d succeeded, %d failed ===", success, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
