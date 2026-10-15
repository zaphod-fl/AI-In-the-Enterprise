"""Provider abstraction.

A Provider is a thin wrapper around one model vendor's API. The whole point
of the Panel is that personas can be bound to *different* providers, so a
blind spot in one vendor's model doesn't appear on both sides of a check
that's supposed to be independent (see the book's vendor-risk chapter).

Every provider implements one method: complete(). It takes a system prompt
and a user prompt and returns plain text. Anything provider-specific
(auth, retries, model selection) stays inside the provider implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderInfo:
    """Identity of a provider, used for the concentration-risk check."""

    vendor: str  # e.g. "anthropic", "openai", "google", "mock-A"
    model: str  # e.g. "claude-sonnet-5", "gpt-5", "gemini-3-pro"


class Provider(ABC):
    """Abstract base class every model backend implements."""

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Identity used for concentration-risk accounting."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's raw text response to one prompt pair.

        Implementations should raise ProviderError on any failure (auth,
        network, rate limit) rather than letting a provider-specific
        exception escape, so the orchestrator can handle degraded-provider
        cases uniformly (see the book's fail-open/fail-closed discussion).
        """


class ProviderError(RuntimeError):
    """Raised by a Provider when it cannot produce a completion."""
