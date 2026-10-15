# Providers

A `Provider` is a thin wrapper around one model vendor: `complete(system_prompt, user_prompt) -> str`, plus an `info` property identifying `vendor` and `model`. That's the whole interface — everything else in this package only ever talks to providers through it.

## Shipped out of the box

- **`AnthropicProvider`** (`anthropic_provider.py`) — real calls to the Anthropic API. Requires `ANTHROPIC_API_KEY`.
- **`MockProvider`** (`mock_provider.py`) — deterministic, rule-based stand-in for a vendor, used by the demo so the whole pipeline runs without five sets of live API keys. **Not** a simulation of what a real model would say — just enough signal, tuned per persona bias, to show real disagreement between "vendors" in the demo.

## Adding a real additional vendor

To add OpenAI, Gemini, Grok, DeepSeek, or a local model, write a class implementing `Provider` and point a persona at an instance of it. Two ways to do this:

1. **Direct SDK** — same pattern as `anthropic_provider.py`: wrap the vendor's own client, normalize errors to `ProviderError`.
2. **Via [any-llm](https://github.com/mozilla-ai/any-llm)** (Mozilla.ai's provider-abstraction library) — one dependency gets you a consistent interface across many vendors, which is less code than writing N direct-SDK providers if you're going past two or three vendors. Wrap `any_llm`'s call in a `Provider` subclass the same way.

Either way, nothing else in `the-panel` needs to change. The orchestrator, quorum engine, and audit trail only know about the `Provider` interface and `ProviderInfo` — not which vendor is behind it.

## Why this separation matters

The book this ships alongside spends a whole chapter on treating model providers as a vendor-risk surface: no provider should back more than a defined share of review authority, and the persona that writes code and the persona that reviews it for security should never share a provider. `ProviderInfo.vendor` is what the quorum engine's concentration-risk check reads to enforce that — see `panel/quorum.py`.
