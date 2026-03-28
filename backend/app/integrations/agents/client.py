from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.services.llm.provider_registry import LLMProvider, ProviderRegistry


class OpenAIClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ) -> None:
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url and base_url.strip():
            client_kwargs["base_url"] = base_url.strip()
        self._client = AsyncOpenAI(**client_kwargs)
        self._model = model

    async def list_models(self) -> list[str]:
        """List available models from the provider's /models endpoint."""
        try:
            response = await self._client.models.list()
            return [m.id for m in response.data]
        except Exception:
            return [self._model]

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        response_format = kwargs.get("response_format")
        try:
            params: dict[str, Any] = {
                "model": self._model,
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
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        settings = get_settings()
        resolved_api_key = api_key or settings.llm_api_key or settings.openai_api_key
        resolved_model = model or settings.llm_model
        resolved_base_url = base_url if base_url is not None else settings.llm_base_url

        self._registry = ProviderRegistry()
        self._registry.register(
            "openai",
            LLMProvider(
                name="openai",
                client=OpenAIClient(
                    api_key=resolved_api_key,
                    model=resolved_model,
                    base_url=resolved_base_url,
                ),
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
