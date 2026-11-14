from __future__ import annotations

import os
from typing import Any, AsyncIterator, Iterator, Optional

import openai

__version__ = "0.1.0"
DEFAULT_BASE_URL = "https://api.outrun.to/v1"
_HEADER = "X-Outrun-SDK"


class OutrunError(openai.OpenAIError):
    """Raised when the client is misconfigured (for example, no API key)."""


def _resolve(api_key: Optional[str], base_url: Optional[str], kwargs: dict) -> tuple:
    key = api_key or os.environ.get("OUTRUN_API_KEY")
    if not key:
        raise OutrunError(
            "No API key. Pass api_key=... or set the OUTRUN_API_KEY environment variable. "
            "Get a key at https://outrun.to/key"
        )
    headers = {_HEADER: f"python/{__version__}"}
    headers.update(kwargs.pop("default_headers", None) or {})
    return key, base_url or DEFAULT_BASE_URL, headers


def _messages(prompt: str, system: Optional[str]) -> list:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


class Outrun(openai.OpenAI):
    """OpenAI client defaulting to the Outrun API. Everything on openai.OpenAI still works."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs: Any):
        key, url, headers = _resolve(api_key, base_url, kwargs)
        super().__init__(api_key=key, base_url=url, default_headers=headers, **kwargs)

    def ask(self, model: str, prompt: str, *, system: Optional[str] = None, **kwargs: Any) -> str:
        """Send one prompt, return the reply text."""
        r = self.chat.completions.create(model=model, messages=_messages(prompt, system), **kwargs)
        return r.choices[0].message.content or ""

    def ask_stream(
        self, model: str, prompt: str, *, system: Optional[str] = None, **kwargs: Any
    ) -> Iterator[str]:
        """Send one prompt, yield reply text as it arrives."""
        stream = self.chat.completions.create(
            model=model, messages=_messages(prompt, system), stream=True, **kwargs
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AsyncOutrun(openai.AsyncOpenAI):
    """Async version of Outrun."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs: Any):
        key, url, headers = _resolve(api_key, base_url, kwargs)
        super().__init__(api_key=key, base_url=url, default_headers=headers, **kwargs)

    async def ask(self, model: str, prompt: str, *, system: Optional[str] = None, **kwargs: Any) -> str:
        r = await self.chat.completions.create(
            model=model, messages=_messages(prompt, system), **kwargs
        )
        return r.choices[0].message.content or ""

    async def ask_stream(
        self, model: str, prompt: str, *, system: Optional[str] = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        stream = await self.chat.completions.create(
            model=model, messages=_messages(prompt, system), stream=True, **kwargs
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
