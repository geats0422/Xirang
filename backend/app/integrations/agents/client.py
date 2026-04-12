from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.services.llm.provider_registry import LLMProvider, ProviderRegistry


class OpenAIClient:
    """OpenAI-compatible LLM client (works with OpenAI, NVIDIA Build API, etc.)."""

    def __init__(
        self, api_key: str | None, base_url: str | None = None, model: str = "gpt-4o-mini"
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        response_format = kwargs.get("response_format")
        try:
            params: dict[str, Any] = {
                "model": kwargs.get("model", self._model),
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
            raise RuntimeError(f"LLM API call failed: {e}") from e


class AgentsClient:
    """LLM client with provider registry support for OpenAI-compatible APIs."""

    def __init__(
        self, api_key: str | None = None, base_url: str | None = None, model: str | None = None
    ) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.llm_api_key
        self._base_url = base_url or settings.llm_base_url
        self._model = model or settings.llm_model
        self._registry = ProviderRegistry()

        if self._api_key:
            self._registry.register(
                "default",
                LLMProvider(
                    name="default",
                    client=OpenAIClient(
                        api_key=self._api_key,
                        base_url=self._base_url,
                        model=self._model,
                    ),
                ),
            )
            self._registry.set_default("default")

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
