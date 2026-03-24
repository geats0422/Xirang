"""LLM provider registry."""

from __future__ import annotations

from typing import Any, Protocol


class LLMClientProtocol(Protocol):
    """Protocol for LLM client."""

    async def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]: ...


class LLMProvider:
    """Base class for LLM providers."""

    def __init__(self, name: str, client: LLMClientProtocol):
        self.name = name
        self.client = client


class ProviderRegistryError(Exception):
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProviderNotFoundError(ProviderRegistryError):
    status_code = 404


class ProviderRegistry:
    """Registry for LLM providers."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._default: str | None = None

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise ProviderNotFoundError(f"Provider not found: {name}")
        return self._providers[name]

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def set_default(self, name: str) -> None:
        if name not in self._providers:
            raise ProviderNotFoundError(f"Provider not found: {name}")
        self._default = name

    def get_default(self) -> LLMProvider | None:
        if self._default is None:
            return None
        return self._providers.get(self._default)
