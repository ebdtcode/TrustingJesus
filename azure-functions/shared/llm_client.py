"""Provider-agnostic LLM client.

Supported providers:
  - openai         (OpenAI API)
  - anthropic      (Anthropic Claude API)
  - google         (Google Gemini API)
  - azure_openai   (Azure-hosted OpenAI)
  - openai_compat  (Any OpenAI-compatible endpoint: Groq, Together, DeepSeek, Ollama, etc.)

Usage:
  client = LLMClient.from_config(config.llm)
  result = client.generate(system_prompt, user_prompt)
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from .config import LLMConfig

logger = logging.getLogger(__name__)

# Provider -> known base URLs (user can override via LLM_BASE_URL)
_KNOWN_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "fireworks": "https://api.fireworks.ai/inference/v1",
    "mistral": "https://api.mistral.ai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


class LLMClient:
    """Unified interface across LLM providers."""

    def __init__(self, config: LLMConfig):
        self.provider = config.provider.lower()
        self.model = config.model
        self._config = config
        self._client = None
        self._init_client()

    @classmethod
    def from_config(cls, config: LLMConfig) -> "LLMClient":
        return cls(config)

    # ------------------------------------------------------------------
    # Client initialization
    # ------------------------------------------------------------------

    def _init_client(self):
        p = self.provider

        if p in ("openai", "openai_compat", *_KNOWN_BASE_URLS):
            from openai import OpenAI

            base_url = (
                self._config.base_url
                or _KNOWN_BASE_URLS.get(p)
                or None
            )
            self._client = OpenAI(
                api_key=self._config.api_key,
                base_url=base_url,
            )
            self._generate_fn = self._openai_generate

        elif p == "azure_openai":
            from openai import AzureOpenAI

            self._client = AzureOpenAI(
                api_key=self._config.api_key,
                azure_endpoint=self._config.base_url,
                api_version=self._config.api_version or "2024-06-01",
            )
            self._generate_fn = self._openai_generate

        elif p == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._config.api_key)
            self._generate_fn = self._anthropic_generate

        elif p == "google":
            import google.generativeai as genai

            genai.configure(api_key=self._config.api_key)
            self._genai = genai
            self._generate_fn = self._google_generate

        else:
            # Fallback: treat as OpenAI-compatible with custom base_url
            from openai import OpenAI

            if not self._config.base_url:
                raise ValueError(
                    f"Unknown provider '{p}'. Set LLM_BASE_URL for custom endpoints."
                )
            self._client = OpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
            )
            self._generate_fn = self._openai_generate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 8192,
        temperature: float = 0.7,
    ) -> str:
        """Generate a text completion."""
        logger.info("LLM generate: provider=%s model=%s", self.provider, self.model)
        return self._generate_fn(system_prompt, user_prompt, max_tokens, temperature)

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 8192,
        temperature: float = 0.4,
        retries: int = 2,
    ) -> dict:
        """Generate and parse a JSON response.

        The prompt should instruct the model to return valid JSON.
        Falls back to extracting JSON from markdown code fences.
        Retries on parse failure with a nudge to fix the output.
        """
        last_error = None
        for attempt in range(1 + retries):
            raw = self.generate(
                system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature
            )
            try:
                return self._parse_json(raw)
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "JSON parse failed (attempt %d/%d): %s",
                    attempt + 1, 1 + retries, e,
                )
                user_prompt = (
                    f"Your previous response was not valid JSON. Error: {e}\n"
                    f"Please return ONLY valid JSON with no extra text."
                )
        raise ValueError(f"Failed to get valid JSON after {1 + retries} attempts: {last_error}")

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    def _openai_generate(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content

    def _anthropic_generate(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return resp.content[0].text

    def _google_generate(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        model = self._genai.GenerativeModel(
            self.model,
            system_instruction=system_prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp = model.generate_content(user_prompt)
        return resp.text

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract JSON from a response that might contain markdown fences."""
        text = raw.strip()
        # Strip ```json ... ``` fences
        if text.startswith("```"):
            first_nl = text.index("\n")
            last_fence = text.rfind("```")
            if last_fence > first_nl:
                text = text[first_nl + 1 : last_fence].strip()
        return json.loads(text)
