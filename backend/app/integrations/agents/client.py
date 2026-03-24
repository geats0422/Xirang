from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.services.llm.provider_registry import LLMProvider, ProviderRegistry


class OpenAIClient:
    def __init__(self, api_key: str | None) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        response_format = kwargs.get("response_format")
        try:
            params: dict[str, Any] = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
            }
            if response_format and response_format.get("type") == "json_object":
                params["response_format"] = response_format

            response = await self._client.chat.completions.create(**params)
            content = response.choices[0].message.content or ""

            if response_format and response_format.get("type") == "json_object":
                try:
                    return {"content": content, "structured_output": json.loads(content)}
                except json.JSONDecodeError:
                    return {"content": content}

            return {"content": content}
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}") from e


class AgentsClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or getattr(get_settings(), "openai_api_key", None)
        self._registry = ProviderRegistry()
        self._registry.register(
            "openai",
            LLMProvider(
                name="openai",
                client=OpenAIClient(api_key=self._api_key),
            ),
        )
        if self._registry.get_default() is None:
            self._registry.set_default("openai")

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    async def generate(
        self,
        prompt: str,
        *,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        provider = self._registry.get_default()
        if provider is None:
            raise RuntimeError("No default LLM provider configured")

        return await provider.client.generate(prompt, response_format=response_format)
