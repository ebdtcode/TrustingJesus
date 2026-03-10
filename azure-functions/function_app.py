"""Azure Functions app: flexible sermon processing pipeline.

Endpoints:
  POST /api/process     Smart router — accepts any YouTube URL (video or channel)
                        and does the right thing. One endpoint for everything.

  POST /api/scan        Scan all configured channels for new videos.
                        Same logic the timer runs automatically.

  GET  /api/health      Health check with config summary.

Timer:
  check_channels        Runs every 6 hours, scans configured channels.

Usage examples:
  # Process a single video
  POST /api/process
  {"url": "https://youtube.com/watch?v=abc123", "speaker": "Pastor John"}

  # Scan a channel for new videos (ad-hoc)
  POST /api/process
  {"url": "https://youtube.com/@HarvestChurchDMV", "speaker": "Pastor John"}

  # Scan a channel by ID
  POST /api/process
  {"url": "UCxxxxxxxxxxxxxxxxxx", "speaker": "Pastor John"}

  # Scan all configured channels
  POST /api/scan
  {}
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone

import azure.functions as func

from shared.config import AppConfig
from shared.content_generator import (
    generate_prayer_points,
    generate_slides_json,
    generate_summary,
)
from shared.github_client import GitHubClient
from shared.llm_client import LLMClient
from shared.template_engine import render_presentation
from shared.transcriber import Transcriber
from shared.auth import check_access
from shared.youtube_downloader import download_audio
from shared.youtube_monitor import (
    URLType,
    YouTubeMonitor,
    classify_url,
    resolve_channel_id,
)

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "sermon", "prayer", "grace", "faith", "family",
    "marriage", "personal-development",
}

app = func.FunctionApp()


# ======================================================================
# POST /api/process — Smart router
# ======================================================================


@app.route(route="process", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def process(req: func.HttpRequest) -> func.HttpResponse:
    """Smart endpoint: auto-detects video vs channel URL and routes accordingly.

    Request body:
    {
      "url": "...",                     REQUIRED — any YouTube URL or ID
      "speaker": "Speaker Name",       optional (fallback: video uploader)
      "series": "Series Name",         optional
      "date": "YYYY-MM-DD",            optional (fallback: publish date or today)
      "category": "sermon",            optional (default: sermon)
      "language": "en",                optional (default: en)
      "auto_process": true,            optional — for channels: process new videos?
      "max_videos": 5                  optional — for channels: limit
    }

    For a VIDEO url:
      Downloads, transcribes, generates content, commits to GitHub.
      Returns: {"type": "video", "status": "success", "commit": "sha", ...}

    For a CHANNEL url:
      Scans for new videos not yet processed.
      If auto_process=true (default), processes each new video.
      Returns: {"type": "channel", "channel_id": "...", "new_videos": [...], ...}
    """
    denied = check_access(req, "process")
    if denied:
        return denied

    try:
        body = req.get_json()
    except ValueError:
        return _json_response({"error": "Invalid JSON body"}, 400)

    url = body.get("url", "").strip()
    if not url:
        return _json_response({"error": "url is required"}, 400)

    url_type, extracted_id = classify_url(url)

    if url_type == URLType.VIDEO:
        return _handle_video(body, extracted_id)
    elif url_type == URLType.CHANNEL:
        return _handle_channel(body, extracted_id)
    else:
        return _json_response(
            {
                "error": f"Could not identify URL type. Got: {url}",
                "hint": "Provide a YouTube video URL, channel URL, @handle, or channel ID.",
            },
            400,
        )


def _handle_video(body: dict, video_id: str) -> func.HttpResponse:
    """Process a single video."""
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    speaker = body.get("speaker", "")
    series = body.get("series", "")
    date_str = body.get("date", "")
    category = body.get("category", "sermon")
    language = body.get("language", "en")

    if category not in VALID_CATEGORIES:
        return _json_response(
            {
                "error": f"Invalid category: '{category}'",
                "valid_categories": sorted(VALID_CATEGORIES),
            },
            400,
        )

    try:
        result = _process_video(
            youtube_url, speaker, series, date_str, category, language
        )
        result["type"] = "video"
        result["video_id"] = video_id
        return _json_response(result, 200)
    except Exception as e:
        logger.exception("Failed to process video %s: %s", video_id, e)
        return _json_response({"type": "video", "error": str(e)}, 500)


def _handle_channel(body: dict, channel_ref: str) -> func.HttpResponse:
    """Scan a channel for new videos, optionally processing them."""
    config = AppConfig.from_env()
    monitor = YouTubeMonitor.from_config(config.youtube)
    gh = GitHubClient.from_config(config.github)

    # Resolve channel reference to an ID
    try:
        channel_id = resolve_channel_id(channel_ref)
    except Exception as e:
        return _json_response(
            {"error": f"Could not resolve channel: {e}"}, 400
        )

    speaker = body.get("speaker", "")
    series = body.get("series", "")
    category = body.get("category", "sermon")
    language = body.get("language", "en")
    auto_process = body.get("auto_process", True)
    max_videos = body.get("max_videos", 5)

    # Load processed state
    processed_data = _load_processed_state(gh)
    processed_ids = set(processed_data.get("videos", {}).keys())

    # Scan channel
    new_videos = monitor.check_single_channel(
        channel_id,
        processed_ids,
        default_speaker=speaker,
        default_series=series,
    )

    results = []
    for video in new_videos[:max_videos]:
        vid = video["video_id"]
        entry = {
            "video_id": vid,
            "title": video["title"],
            "published_at": video.get("published_at", ""),
        }

        if not auto_process:
            entry["status"] = "detected"
            processed_data.setdefault("videos", {})[vid] = {
                "title": video["title"],
                "status": "detected",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "channel_id": channel_id,
            }
        else:
            try:
                url = f"https://www.youtube.com/watch?v={vid}"
                date_str = body.get("date", video.get("published_at", "")[:10])
                process_result = _process_video(
                    url,
                    speaker=video.get("default_speaker", speaker),
                    series=video.get("default_series", series),
                    date_str=date_str,
                    category=category,
                    language=language,
                )
                entry["status"] = "processed"
                entry["commit"] = process_result.get("commit", "")
                entry["files"] = process_result.get("files", [])
                processed_data.setdefault("videos", {})[vid] = {
                    "title": video["title"],
                    "status": "completed",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "channel_id": channel_id,
                }
            except Exception as e:
                logger.exception("Failed to process video %s: %s", vid, e)
                entry["status"] = "failed"
                entry["error"] = str(e)
                processed_data.setdefault("videos", {})[vid] = {
                    "title": video["title"],
                    "status": "failed",
                    "error": str(e),
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "channel_id": channel_id,
                }

        results.append(entry)

    # Save state
    _update_processed_state(gh, processed_data)

    return _json_response(
        {
            "type": "channel",
            "channel_id": channel_id,
            "videos_found": len(new_videos),
            "videos_processed": len(results),
            "results": results,
        },
        200,
    )


# ======================================================================
# POST /api/scan — Scan all configured channels
# ======================================================================


@app.route(route="scan", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def scan(req: func.HttpRequest) -> func.HttpResponse:
    """Scan all configured channels for new videos.

    Optional request body:
    {
      "auto_process": true,      default: from channels.json settings
      "max_videos": 5            default: from channels.json settings
    }
    """
    denied = check_access(req, "scan")
    if denied:
        return denied

    try:
        body = req.get_json() if req.get_body() else {}
    except ValueError:
        body = {}

    try:
        result = _scan_all_channels(body)
        return _json_response(result, 200)
    except Exception as e:
        logger.exception("Scan failed: %s", e)
        return _json_response({"error": str(e)}, 500)


# ======================================================================
# Timer: Auto-scan configured channels
# ======================================================================


@app.timer_trigger(
    schedule="0 0 */6 * * *",  # Every 6 hours
    arg_name="timer",
    run_on_startup=False,
)
def check_channels(timer: func.TimerRequest) -> None:
    """Scheduled scan of all configured channels."""
    if os.environ.get("CHANNEL_CHECK_ENABLED", "true").lower() != "true":
        logger.info("Channel checking is disabled")
        return

    try:
        result = _scan_all_channels({})
        logger.info(
            "Scheduled scan complete: %d channels, %d new videos",
            result.get("channels_checked", 0),
            result.get("total_new", 0),
        )
    except Exception as e:
        logger.exception("Scheduled channel scan failed: %s", e)


# ======================================================================
# GET /api/health
# ======================================================================


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    config = AppConfig.from_env()
    return _json_response(
        {
            "status": "healthy",
            "llm_provider": config.llm.provider,
            "llm_model": config.llm.model,
            "whisper_provider": config.whisper.provider,
            "youtube_auth_mode": config.youtube.auth_mode,
            "channel_check_enabled": os.environ.get(
                "CHANNEL_CHECK_ENABLED", "true"
            ),
        }
    )


# ======================================================================
# GET /api/status — Processing history for mobile/agent clients
# ======================================================================


@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Return processing history and channel configuration.

    Used by mobile apps and agents to display what has been processed.
    Query params:
      ?limit=20     Max entries to return (default 20)
      ?status=...   Filter by status: completed, failed, detected, filtered
    """
    denied = check_access(req, "status")
    if denied:
        return denied

    config = AppConfig.from_env()
    gh = GitHubClient.from_config(config.github)

    processed_data = _load_processed_state(gh)
    channels_config = _load_channels_config()

    try:
        limit = int(req.params.get("limit", "20"))
    except ValueError:
        limit = 20
    status_filter = req.params.get("status", "")

    videos = processed_data.get("videos", {})

    # Build entries list sorted by most recent
    entries = []
    for vid, info in videos.items():
        if status_filter and info.get("status") != status_filter:
            continue
        entries.append({"video_id": vid, **info})

    entries.sort(
        key=lambda x: x.get("processed_at", x.get("detected_at", "")),
        reverse=True,
    )

    return _json_response(
        {
            "last_checked": processed_data.get("last_checked"),
            "total_processed": len(videos),
            "channels": [
                {"id": c["id"], "name": c.get("name", ""), "enabled": c.get("enabled", True)}
                for c in channels_config.get("channels", [])
            ],
            "recent": entries[:limit],
        }
    )


# ======================================================================
# Core processing pipeline
# ======================================================================


def _process_video(
    youtube_url: str,
    speaker: str,
    series: str,
    date_str: str,
    category: str = "sermon",
    language: str = "en",
) -> dict:
    """Full pipeline: download -> transcribe -> generate content -> push to GitHub."""
    config = AppConfig.from_env()

    llm = LLMClient.from_config(config.llm)
    whisper = Transcriber.from_config(config.whisper)
    gh = GitHubClient.from_config(config.github)

    tmp_dir = tempfile.mkdtemp(prefix="sermon_")

    try:
        # 1. Download audio
        audio_path, video_meta = download_audio(youtube_url, output_dir=tmp_dir)

        if not speaker:
            speaker = video_meta.get("uploader", "Unknown")
        if not date_str:
            raw_date = video_meta.get("upload_date", "")
            if raw_date and len(raw_date) == 8:
                date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            else:
                date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        title = _sanitize_title(video_meta.get("title", "Sermon"))

        metadata = {
            "title": title,
            "speaker": speaker,
            "date": date_str,
            "series": series,
            "category": category,
            "youtube_url": video_meta.get("webpage_url", youtube_url),
            "video_id": video_meta.get("id", ""),
        }

        # 2. Transcribe
        church_name = os.environ.get("CHURCH_NAME", "")
        whisper_prompt = f"Sermon by {speaker}"
        if church_name:
            whisper_prompt += f" at {church_name}"
        transcript = whisper.transcribe(
            audio_path,
            language=language,
            prompt=f"{whisper_prompt}.",
        )

        # 3. Generate sermon summary
        summary = generate_summary(llm, transcript, metadata)

        # 4. Generate prayer points
        prayer_points = generate_prayer_points(
            llm, transcript, summary, metadata
        )

        # 5. Generate presentation slides
        slides_json = generate_slides_json(llm, transcript, summary, metadata)
        presentation_html = render_presentation(slides_json)

        # 6. Build transcript markdown
        transcript_md = _build_transcript_md(transcript, metadata)

        # 7. Determine file paths
        safe_title = _safe_filename(title)
        year = date_str[:4] if date_str else str(datetime.now().year)

        files = {
            f"transcripts/sermon/{safe_title}/transcript.md": transcript_md,
            f"sermons_summaries/{safe_title}.md": summary,
            f"prayer_points/{year}/Week-{date_str}_{safe_title}.md": prayer_points,
            f"site/v2/presentations/{category}/{safe_title}.html": presentation_html,
        }

        # 8. Update presentations.js data
        presentations_js = gh.get_file_content("site/v2/data/presentations.js")
        if presentations_js:
            updated_js = _inject_presentation_entry(
                presentations_js, slides_json, metadata, safe_title
            )
            files["site/v2/data/presentations.js"] = updated_js

        # 9. Commit to GitHub
        commit_msg = f"feat: add sermon '{title}' ({date_str})"
        commit_sha = gh.commit_files(files, commit_msg)

        return {
            "status": "success",
            "commit": commit_sha,
            "title": title,
            "files": list(files.keys()),
            "video_id": metadata["video_id"],
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ======================================================================
# Scan all configured channels
# ======================================================================


def _scan_all_channels(overrides: dict) -> dict:
    """Core logic for scanning all configured channels.

    Used by both the POST /api/scan endpoint and the timer trigger.
    """
    config = AppConfig.from_env()
    gh = GitHubClient.from_config(config.github)
    monitor = YouTubeMonitor.from_config(config.youtube)

    channels_json = _load_channels_config()
    channels = channels_json.get("channels", [])
    settings = channels_json.get("settings", {})

    if not channels:
        return {"channels_checked": 0, "total_new": 0, "results": []}

    processed_data = _load_processed_state(gh)
    processed_ids = set(processed_data.get("videos", {}).keys())

    try:
        new_videos = monitor.check_channels(channels, processed_ids)
    except Exception as e:
        logger.error("Failed to check YouTube channels: %s", e)
        return {"error": str(e), "channels_checked": 0, "total_new": 0}

    if not new_videos:
        _update_processed_state(gh, processed_data, checked_only=True)
        return {
            "channels_checked": len([c for c in channels if c.get("enabled", True)]),
            "total_new": 0,
            "results": [],
        }

    auto_process = overrides.get(
        "auto_process", settings.get("auto_process", True)
    )
    max_videos = overrides.get(
        "max_videos", settings.get("max_videos_per_check", 5)
    )

    results = []
    for video in new_videos[:max_videos]:
        vid = video["video_id"]
        entry = {
            "video_id": vid,
            "title": video["title"],
            "channel_id": video["channel_id"],
        }

        channel_cfg = next(
            (c for c in channels if c["id"] == video["channel_id"]), {}
        )
        if not _passes_filter(video, channel_cfg.get("content_filter", {})):
            entry["status"] = "filtered"
            processed_data.setdefault("videos", {})[vid] = {
                "title": video["title"],
                "status": "filtered",
                "detected_at": datetime.now(timezone.utc).isoformat(),
            }
            results.append(entry)
            continue

        if not auto_process:
            entry["status"] = "detected"
            processed_data.setdefault("videos", {})[vid] = {
                "title": video["title"],
                "status": "detected",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "channel_id": video["channel_id"],
            }
        else:
            try:
                url = f"https://www.youtube.com/watch?v={vid}"
                process_result = _process_video(
                    url,
                    speaker=video.get("default_speaker", ""),
                    series=video.get("default_series", ""),
                    date_str=video.get("published_at", "")[:10],
                    category=settings.get("default_category", "sermon"),
                )
                entry["status"] = "processed"
                entry["commit"] = process_result.get("commit", "")
                processed_data.setdefault("videos", {})[vid] = {
                    "title": video["title"],
                    "status": "completed",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "channel_id": video["channel_id"],
                }
            except Exception as e:
                logger.exception("Failed to process video %s: %s", vid, e)
                entry["status"] = "failed"
                entry["error"] = str(e)
                processed_data.setdefault("videos", {})[vid] = {
                    "title": video["title"],
                    "status": "failed",
                    "error": str(e),
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                    "channel_id": video["channel_id"],
                }

        results.append(entry)

    _update_processed_state(gh, processed_data)

    return {
        "channels_checked": len(
            [c for c in channels if c.get("enabled", True)]
        ),
        "total_new": len(new_videos),
        "videos_processed": len(results),
        "results": results,
    }


# ======================================================================
# Helpers
# ======================================================================


def _json_response(data: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data, indent=2),
        status_code=status_code,
        mimetype="application/json",
    )


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
    js_content: str,
    slides_json: dict,
    metadata: dict,
    safe_title: str,
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
        return (
            js_content[:insert_pos]
            + "\n"
            + js_entry
            + ",\n"
            + js_content[insert_pos:]
        )

    bracket_idx = js_content.index("[")
    return (
        js_content[: bracket_idx + 1]
        + "\n"
        + js_entry
        + ",\n"
        + js_content[bracket_idx + 1 :]
    )


def _load_channels_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(__file__), "config", "channels.json"
    )
    with open(config_path) as f:
        return json.load(f)


def _load_processed_state(gh: GitHubClient) -> dict:
    content = gh.get_file_content(
        "azure-functions/config/processed_videos.json"
    )
    if content:
        return json.loads(content)
    return {"videos": {}, "last_checked": None}


def _update_processed_state(
    gh: GitHubClient, data: dict, checked_only: bool = False
) -> None:
    data["last_checked"] = datetime.now(timezone.utc).isoformat()
    gh.commit_files(
        {
            "azure-functions/config/processed_videos.json": json.dumps(
                data, indent=2
            )
        },
        "chore: update processed videos state",
    )


def _passes_filter(video: dict, content_filter: dict) -> bool:
    if not content_filter:
        return True

    title = video.get("title", "").lower()

    must_contain = content_filter.get("title_must_contain", [])
    if must_contain and not any(kw.lower() in title for kw in must_contain):
        return False

    must_not_contain = content_filter.get("title_must_not_contain", [])
    if any(kw.lower() in title for kw in must_not_contain):
        return False

    return True
