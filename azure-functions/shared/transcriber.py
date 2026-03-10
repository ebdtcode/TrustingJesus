"""Audio transcription via Whisper API (multiple providers).

Supports:
  - openai        (OpenAI Whisper API)
  - azure_openai  (Azure-hosted Whisper)
  - groq          (Groq Whisper API)
  - openai_compat (Any OpenAI-compatible Whisper endpoint)

Handles files >25 MB by splitting into chunks with pydub.
"""

from __future__ import annotations

import logging
import math
import os
import tempfile
from pathlib import Path
from typing import Optional

from .config import WhisperConfig

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 24  # Stay under the 25 MB limit


class Transcriber:
    def __init__(self, config: WhisperConfig):
        self.provider = config.provider.lower()
        self.model = config.model or "whisper-1"
        self._config = config
        self._client = None
        self._init_client()

    @classmethod
    def from_config(cls, config: WhisperConfig) -> "Transcriber":
        return cls(config)

    def _init_client(self):
        p = self.provider
        if p in ("openai", "openai_compat", "groq"):
            from openai import OpenAI

            base_url = self._config.base_url or {
                "groq": "https://api.groq.com/openai/v1",
            }.get(p)
            self._client = OpenAI(
                api_key=self._config.api_key,
                base_url=base_url,
            )
        elif p == "azure_openai":
            from openai import AzureOpenAI

            self._client = AzureOpenAI(
                api_key=self._config.api_key,
                azure_endpoint=self._config.base_url,
                api_version="2024-06-01",
            )
        else:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
            )

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str = "en",
        prompt: Optional[str] = None,
    ) -> str:
        """Transcribe an audio file, chunking if needed."""
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(
            "Transcribing %s (%.1f MB) via %s/%s",
            audio_path, file_size_mb, self.provider, self.model,
        )

        if file_size_mb <= MAX_FILE_SIZE_MB:
            return self._transcribe_file(audio_path, language, prompt)

        return self._transcribe_chunked(audio_path, language, prompt)

    def _transcribe_file(
        self, path: str, language: str, prompt: Optional[str]
    ) -> str:
        with open(path, "rb") as audio_file:
            kwargs = {
                "model": self.model,
                "file": audio_file,
                "language": language,
                "response_format": "text",
            }
            if prompt:
                kwargs["prompt"] = prompt
            result = self._client.audio.transcriptions.create(**kwargs)
            return result if isinstance(result, str) else result.text

    def _transcribe_chunked(
        self, path: str, language: str, prompt: Optional[str]
    ) -> str:
        """Split audio into chunks and transcribe each with retry."""
        import time

        from pydub import AudioSegment

        logger.info("File exceeds %d MB, splitting into chunks", MAX_FILE_SIZE_MB)
        audio = AudioSegment.from_file(path)
        duration_ms = len(audio)

        # Target chunk size: ~20 MB worth of audio
        # Rough estimate: 1 min of mp3 ~ 1 MB at 128 kbps
        chunk_duration_ms = 20 * 60 * 1000  # 20 minutes per chunk
        num_chunks = math.ceil(duration_ms / chunk_duration_ms)

        segments = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i in range(num_chunks):
                start = i * chunk_duration_ms
                end = min((i + 1) * chunk_duration_ms, duration_ms)
                chunk = audio[start:end]

                chunk_path = os.path.join(tmp_dir, f"chunk_{i:03d}.mp3")
                chunk.export(chunk_path, format="mp3", bitrate="128k")

                logger.info(
                    "Transcribing chunk %d/%d (%.1f - %.1f min)",
                    i + 1, num_chunks, start / 60000, end / 60000,
                )

                last_error = None
                for attempt in range(3):
                    try:
                        text = self._transcribe_file(chunk_path, language, prompt)
                        segments.append(text.strip())
                        break
                    except Exception as e:
                        last_error = e
                        logger.warning(
                            "Chunk %d/%d attempt %d failed: %s",
                            i + 1, num_chunks, attempt + 1, e,
                        )
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(
                        f"Failed to transcribe chunk {i + 1}/{num_chunks} "
                        f"after 3 attempts: {last_error}"
                    )

        return "\n\n".join(segments)
