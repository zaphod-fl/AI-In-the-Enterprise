"""A real provider backed by the Anthropic API.

Requires the ANTHROPIC_API_KEY environment variable. If it isn't set,
construction fails fast with a clear ProviderError rather than a confusing
auth error later, mid-review.
"""

from __future__ import annotations

import os

from .base import Provider, ProviderError, ProviderInfo


class AnthropicProvider(Provider):
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: str | None = None):
        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ProviderError(
                "AnthropicProvider requires ANTHROPIC_API_KEY to be set. "
                "Use a MockProvider instead for a demo run without live keys."
            )
        try:
            import anthropic  # noqa: F401 - import check only
        except ImportError as exc:
            raise ProviderError(
                "The 'anthropic' package is required for AnthropicProvider "
                "(pip install anthropic)."
            ) from exc

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(vendor="anthropic", model=self._model)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:  # noqa: BLE001 - normalize all SDK errors
            raise ProviderError(f"Anthropic API call failed: {exc}") from exc

        return "".join(
            block.text for block in response.content if block.type == "text"
        )
