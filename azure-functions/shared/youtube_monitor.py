"""YouTube channel monitor and URL resolver for detecting new public video uploads.

Auth modes (YOUTUBE_AUTH_MODE):
  - rss      (default) Zero-cost, no API key. Parses the public YouTube RSS feed.
                       Returns the latest ~15 videos per channel.
  - api_key            Uses YouTube Data API v3 key for richer metadata
                       (duration, statistics, descriptions). Free tier: 10,000
                       units/day which covers hundreds of channel checks.

URL resolution:
  Accepts any YouTube URL format and resolves it to either a video ID or channel ID:
    - youtube.com/watch?v=ID         -> video
    - youtu.be/ID                    -> video
    - youtube.com/channel/UCxxxx     -> channel
    - youtube.com/@Handle            -> channel (resolves via page scrape)
    - youtube.com/c/CustomName       -> channel (resolves via page scrape)
    - youtube.com/user/Name          -> channel (resolves via page scrape)
    - Raw channel ID (UCxxxx)        -> channel
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from urllib.parse import parse_qs, urlparse

import requests

from .config import YouTubeConfig

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml"

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


# ------------------------------------------------------------------
# URL parsing and resolution
# ------------------------------------------------------------------


class URLType(Enum):
    VIDEO = "video"
    CHANNEL = "channel"
    UNKNOWN = "unknown"


def classify_url(url: str) -> tuple[URLType, str]:
    """Classify a YouTube URL and extract the relevant ID.

    Returns:
        (URLType, id_string)
        - VIDEO:   id_string is the video ID
        - CHANNEL: id_string is the channel ID or a URL needing resolution
        - UNKNOWN: id_string is the original input
    """
    url = url.strip()

    # Raw channel ID (starts with UC, 24 chars)
    if re.match(r"^UC[\w-]{22}$", url):
        return URLType.CHANNEL, url

    # Raw video ID (11 chars, alphanumeric + dash/underscore)
    if re.match(r"^[\w-]{11}$", url):
        return URLType.VIDEO, url

    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path or ""

    # youtu.be/VIDEO_ID
    if "youtu.be" in host:
        video_id = path.lstrip("/").split("/")[0].split("?")[0]
        if video_id:
            return URLType.VIDEO, video_id

    if "youtube.com" not in host and "youtube" not in host:
        return URLType.UNKNOWN, url

    # youtube.com/watch?v=VIDEO_ID
    if "/watch" in path:
        qs = parse_qs(parsed.query)
        video_id = qs.get("v", [""])[0]
        if video_id:
            return URLType.VIDEO, video_id

    # youtube.com/embed/VIDEO_ID or /v/VIDEO_ID or /shorts/VIDEO_ID
    for prefix in ("/embed/", "/v/", "/shorts/"):
        if path.startswith(prefix):
            video_id = path[len(prefix):].split("/")[0].split("?")[0]
            if video_id:
                return URLType.VIDEO, video_id

    # youtube.com/channel/UCxxxx
    match = re.match(r"/channel/(UC[\w-]+)", path)
    if match:
        return URLType.CHANNEL, match.group(1)

    # youtube.com/@Handle or /c/Name or /user/Name
    if re.match(r"/(@[\w.-]+|/c/[\w.-]+|/user/[\w.-]+)", path):
        return URLType.CHANNEL, url  # Needs resolution

    # youtube.com/live/VIDEO_ID
    if path.startswith("/live/"):
        video_id = path[6:].split("/")[0].split("?")[0]
        if video_id:
            return URLType.VIDEO, video_id

    return URLType.UNKNOWN, url


def resolve_channel_id(url_or_id: str) -> str:
    """Resolve any channel reference to a channel ID (UCxxxx).

    Accepts:
      - Direct channel ID: "UCxxxx"
      - Channel URL: "youtube.com/channel/UCxxxx"
      - Handle URL:  "youtube.com/@HandleName"
      - Custom URL:  "youtube.com/c/CustomName"
      - User URL:    "youtube.com/user/UserName"
    """
    # Already a channel ID
    if re.match(r"^UC[\w-]{22}$", url_or_id):
        return url_or_id

    # Extract from /channel/ URL
    match = re.search(r"/channel/(UC[\w-]{22})", url_or_id)
    if match:
        return match.group(1)

    # For @handle, /c/, /user/ URLs: fetch page and extract channel ID
    fetch_url = url_or_id
    if not fetch_url.startswith("http"):
        fetch_url = f"https://www.youtube.com/{url_or_id.lstrip('/')}"

    logger.info("Resolving channel ID from: %s", fetch_url)
    resp = requests.get(
        fetch_url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
        allow_redirects=True,
    )
    resp.raise_for_status()

    # Look for channel ID in page content
    # Pattern 1: canonical link
    match = re.search(
        r'<link\s+rel="canonical"\s+href="https://www\.youtube\.com/channel/(UC[\w-]+)"',
        resp.text,
    )
    if match:
        return match.group(1)

    # Pattern 2: meta tag or JSON data
    match = re.search(r'"channelId"\s*:\s*"(UC[\w-]+)"', resp.text)
    if match:
        return match.group(1)

    # Pattern 3: browse endpoint data
    match = re.search(r'"browseId"\s*:\s*"(UC[\w-]+)"', resp.text)
    if match:
        return match.group(1)

    raise ValueError(f"Could not resolve channel ID from: {url_or_id}")


# ------------------------------------------------------------------
# Monitor class
# ------------------------------------------------------------------


class YouTubeMonitor:
    def __init__(self, config: YouTubeConfig):
        self.auth_mode = config.auth_mode.lower() if config.auth_mode else "rss"
        self._config = config

    @classmethod
    def from_config(cls, config: YouTubeConfig) -> "YouTubeMonitor":
        return cls(config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_recent_videos(
        self,
        channel_id: str,
        *,
        since: Optional[datetime] = None,
        max_results: int = 15,
    ) -> list[dict]:
        """Fetch recent videos from a channel.

        Uses RSS (default) or API key depending on auth_mode.
        Returns list of dicts: video_id, title, published_at, description,
                               thumbnail_url, channel_id, channel_title
        """
        if self.auth_mode == "api_key" and self._config.api_key:
            return self._get_videos_api(
                channel_id, since=since, max_results=max_results
            )
        return self._get_videos_rss(channel_id, since=since)

    def check_channels(
        self,
        channels: list[dict],
        processed_ids: set[str],
    ) -> list[dict]:
        """Check multiple channels for new unprocessed videos.

        Args:
            channels: List of channel configs with at least 'id' key and optional
                      'default_speaker', 'default_series', 'enabled' keys.
            processed_ids: Set of video IDs already processed.

        Returns:
            List of new video dicts with channel metadata merged in.
        """
        new_videos = []

        for ch in channels:
            if not ch.get("enabled", True):
                continue

            channel_id = ch["id"]
            logger.info("Checking channel: %s (%s)", ch.get("name", ""), channel_id)

            try:
                videos = self.get_recent_videos(channel_id)
            except Exception as e:
                logger.error("Failed to check channel %s: %s", channel_id, e)
                continue

            channel_new = 0
            for video in videos:
                if video["video_id"] in processed_ids:
                    continue

                video["default_speaker"] = ch.get("default_speaker", "")
                video["default_series"] = ch.get("default_series", "")
                new_videos.append(video)
                channel_new += 1

            logger.info(
                "Channel %s: %d videos fetched, %d new",
                ch.get("name", channel_id),
                len(videos),
                channel_new,
            )

        return new_videos

    def check_single_channel(
        self,
        channel_id: str,
        processed_ids: set[str],
        *,
        default_speaker: str = "",
        default_series: str = "",
    ) -> list[dict]:
        """Check a single channel for new unprocessed videos.

        Convenience wrapper for ad-hoc channel scans.
        """
        return self.check_channels(
            [
                {
                    "id": channel_id,
                    "name": "",
                    "default_speaker": default_speaker,
                    "default_series": default_series,
                    "enabled": True,
                }
            ],
            processed_ids,
        )

    # ------------------------------------------------------------------
    # RSS feed (default — no API key required)
    # ------------------------------------------------------------------

    def _get_videos_rss(
        self,
        channel_id: str,
        *,
        since: Optional[datetime] = None,
    ) -> list[dict]:
        """Parse the public YouTube RSS/Atom feed for a channel.

        Feed URL: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
        Returns the latest ~15 videos (YouTube's RSS limit).
        """
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
            video_id_el = entry.find("yt:videoId", ATOM_NS)
            title_el = entry.find("atom:title", ATOM_NS)
            published_el = entry.find("atom:published", ATOM_NS)
            media_group = entry.find("media:group", ATOM_NS)

            if video_id_el is None or title_el is None:
                continue

            video_id = video_id_el.text or ""
            title = title_el.text or ""
            published_str = (
                published_el.text if published_el is not None else ""
            )

            if since and published_str:
                try:
                    published_dt = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    )
                    if published_dt <= since:
                        continue
                except ValueError:
                    pass

            description = ""
            thumbnail_url = ""
            if media_group is not None:
                desc_el = media_group.find("media:description", ATOM_NS)
                if desc_el is not None and desc_el.text:
                    description = desc_el.text
                thumb_el = media_group.find("media:thumbnail", ATOM_NS)
                if thumb_el is not None:
                    thumbnail_url = thumb_el.get("url", "")

            videos.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "published_at": published_str,
                    "description": description,
                    "thumbnail_url": thumbnail_url
                    or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                }
            )

        return videos

    # ------------------------------------------------------------------
    # YouTube Data API v3 (optional — richer metadata)
    # ------------------------------------------------------------------

    def _api_get(self, endpoint: str, params: dict) -> dict:
        params["key"] = self._config.api_key
        resp = requests.get(
            f"{YOUTUBE_API_BASE}/{endpoint}",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _get_videos_api(
        self,
        channel_id: str,
        *,
        since: Optional[datetime] = None,
        max_results: int = 10,
    ) -> list[dict]:
        """Fetch recent videos via YouTube Data API v3 (requires API key)."""
        ch_data = self._api_get(
            "channels",
            {"part": "contentDetails", "id": channel_id},
        )
        items = ch_data.get("items", [])
        if not items:
            raise ValueError(f"Channel not found: {channel_id}")

        playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        data = self._api_get(
            "playlistItems",
            {
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": max_results,
            },
        )

        videos = []
        for item in data.get("items", []):
            snippet = item["snippet"]
            published_str = snippet.get("publishedAt", "")

            if since and published_str:
                published = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                )
                if published <= since:
                    continue

            videos.append(
                {
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "published_at": published_str,
                    "description": snippet.get("description", ""),
                    "thumbnail_url": (
                        snippet.get("thumbnails", {})
                        .get(
                            "high",
                            snippet.get("thumbnails", {}).get("default", {}),
                        )
                        .get("url", "")
                    ),
                    "channel_id": channel_id,
                    "channel_title": snippet.get("channelTitle", ""),
                }
            )

        return videos
