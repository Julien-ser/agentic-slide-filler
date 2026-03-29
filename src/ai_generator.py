"""AI Content Generator using OpenAI API with caching and fallback."""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import openai
from openai import OpenAI
import logging

from .prompts import get_prompt

logger = logging.getLogger(__name__)


class AIContentGenerator:
    """
    Generates presentation content using OpenAI's API with caching,
    retry logic, and fallback models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        cache_dir: str = "cache",
        model: str = "gpt-4",
        fallback_model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided or set in OPENAI_API_KEY env var"
            )
        self.client = OpenAI(api_key=self.api_key)
        self.temperature = temperature
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.model = model
        self.fallback_model = fallback_model
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def generate(self, placeholder_type: str, **context: Any) -> str:
        """
        Generate content for a given placeholder type.

        Args:
            placeholder_type: Type of placeholder (e.g., "TITLE", "BODY").
            **context: Variables required by the prompt template.

        Returns:
            Generated content string.

        Raises:
            ValueError: If no prompt template exists or required context is missing.
            RuntimeError: If API calls fail after retries and fallback.
        """
        # Render the prompt
        prompt = get_prompt(placeholder_type, **context)

        # Compute cache key based on prompt and model (use primary model first)
        cache_key = self._compute_cache_key(prompt, self.model)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug("Cache hit for prompt (model: %s)", self.model)
            return cached

        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are a helpful presentation assistant.",
            },
            {"role": "user", "content": prompt},
        ]

        # Try primary model with retries
        try:
            content = self._call_api_with_retry(messages, self.model)
        except Exception as e:
            logger.warning(
                "Primary model %s failed: %s. Attempting fallback %s.",
                self.model,
                e,
                self.fallback_model,
            )
            if self.fallback_model and self.fallback_model != self.model:
                fallback_key = self._compute_cache_key(prompt, self.fallback_model)
                cached_fallback = self._get_from_cache(fallback_key)
                if cached_fallback is not None:
                    logger.debug("Cache hit for fallback model")
                    return cached_fallback
                try:
                    content = self._call_api_with_retry(messages, self.fallback_model)
                    # Cache under fallback key
                    self._save_to_cache(fallback_key, content)
                    return content
                except Exception as e2:
                    logger.error("Fallback model also failed: %s", e2)
                    raise RuntimeError(
                        f"Both primary model {self.model} and fallback {self.fallback_model} failed"
                    ) from e2
            else:
                raise

        # Cache the successful result
        self._save_to_cache(cache_key, content)
        return content

    def _call_api_with_retry(self, messages: list, model: str) -> str:
        """Call OpenAI API with exponential backoff retry."""
        retries = 0
        while retries <= self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                )
                choice = response.choices[0]
                if choice.message.content is None:
                    raise RuntimeError("Empty response from API")
                return choice.message.content.strip()
            except (
                openai.RateLimitError,
                openai.APIConnectionError,
                openai.APIError,
            ) as e:
                if retries == self.max_retries:
                    logger.error("API error after %s retries: %s", retries, e)
                    raise
                sleep_time = self.backoff_factor * (2**retries)
                logger.warning(
                    "API error (%s). Retrying in %.2f seconds...", e, sleep_time
                )
                time.sleep(sleep_time)
                retries += 1
        # This point should never be reached; added for type safety
        raise RuntimeError("_call_api_with_retry exhausted retries without success")

    def _compute_cache_key(self, prompt: str, model: str) -> str:
        """Compute a unique cache key based on prompt and model."""
        key_str = f"{model}:{prompt}"
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Retrieve cached content if it exists."""
        cache_file = self.cache_dir / f"{cache_key}.txt"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        return None

    def _save_to_cache(self, cache_key: str, content: str) -> None:
        """Save generated content to cache."""
        cache_file = self.cache_dir / f"{cache_key}.txt"
        cache_file.write_text(content, encoding="utf-8")
