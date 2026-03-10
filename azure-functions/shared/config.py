"""Central configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    provider: str = ""
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    api_version: str = ""

    @classmethod
    def from_env(cls):
        return cls(
            provider=os.environ.get("LLM_PROVIDER", "openai"),
            api_key=os.environ.get("LLM_API_KEY", ""),
            model=os.environ.get("LLM_MODEL", "gpt-4o"),
            base_url=os.environ.get("LLM_BASE_URL", ""),
            api_version=os.environ.get("LLM_API_VERSION", ""),
        )


@dataclass
class WhisperConfig:
    provider: str = ""
    api_key: str = ""
    model: str = ""
    base_url: str = ""

    @classmethod
    def from_env(cls):
        return cls(
            provider=os.environ.get("WHISPER_PROVIDER", "openai"),
            api_key=os.environ.get("WHISPER_API_KEY", ""),
            model=os.environ.get("WHISPER_MODEL", "whisper-1"),
            base_url=os.environ.get("WHISPER_BASE_URL", ""),
        )


@dataclass
class YouTubeConfig:
    auth_mode: str = "rss"  # "rss" (free, no key) or "api_key" (richer metadata)
    api_key: str = ""       # Only needed if auth_mode=api_key

    @classmethod
    def from_env(cls):
        return cls(
            auth_mode=os.environ.get("YOUTUBE_AUTH_MODE", "rss"),
            api_key=os.environ.get("YOUTUBE_API_KEY", ""),
        )


@dataclass
class GitHubConfig:
    token: str = ""
    repo: str = ""
    branch: str = "main"

    @classmethod
    def from_env(cls):
        return cls(
            token=os.environ.get("GITHUB_TOKEN", ""),
            repo=os.environ.get("GITHUB_REPO", ""),
            branch=os.environ.get("GITHUB_BRANCH", "main"),
        )


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)

    @classmethod
    def from_env(cls):
        return cls(
            llm=LLMConfig.from_env(),
            whisper=WhisperConfig.from_env(),
            youtube=YouTubeConfig.from_env(),
            github=GitHubConfig.from_env(),
        )
