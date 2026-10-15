# the-panel

A working reference implementation of "the panel" — the independent, multi-persona, mixed-model-provider review mechanism from the book **[*The Panel: Building Software You Can Trust in the Age of AI*](https://claude.ai/artifact/8zxXh2m7g1HDQ93dL5xs26)**.

This isn't a product. It's proof that the pattern the book describes — five personas, each running a positive approach and a negative approach, voting toward a quorum that a dissent can't be silently outvoted from, with a generated audit trail instead of a design doc that trails the code — actually runs, end to end, today.

## What's here

- **`panel/providers/`** — a one-method `Provider` interface (`complete(system, user) -> str`), so a persona can be bound to any model vendor. Ships with a real `AnthropicProvider` and a deterministic `MockProvider` (so the demo runs with zero API keys). See `providers/README.md` for wiring in OpenAI, Gemini, Grok, DeepSeek, or a local model.
- **`panel/personas.py`** — the five personas (Requirements, Developer, Security, Test, Ops), each with a positive-approach and negative-approach prompt. Security and Test are marked `required_for_quorum`, matching the book.
- **`panel/quorum.py`** — the actual rules: ≥4/5 approval, Security + Test approval mandatory, a dissent blocks until it's resolved on the record (never silently outvoted), and a concentration-risk check (no vendor backs too many seats; Developer and Security can't share a vendor).
- **`panel/audit.py`** — generates the book's three artifacts from a run: the TL;DR, the issue & risk log, and the dissent log.
- **`panel/orchestrator.py`** — `run_panel(...)` ties it all together. A provider that's unreachable fails *closed* (counted as a dissent, not skipped), matching the book's degraded-provider discussion.
- **`panel/demos/fenwick_fallback_carrier.py`** — the book's own Chapter 3 story, run twice: round one blocks on Security's real finding (a certification check reading from a six-hour cache), round two re-votes 5/5 after the fix. Run it with `panel demo`. (`examples/fenwick_fallback_carrier.py` is a thin shim to the same demo, for `python -m examples.fenwick_fallback_carrier` from a repo checkout without installing.)

## Quickstart

```bash
pip install -e .
panel demo                                          # the book's own story, end to end
panel review --task "Add a rate limiter to the checkout endpoint." --owner "you"
python -m pytest                                    # 10 tests, all passing, no API keys needed
```

Everything above runs on `MockProvider` — deterministic, rule-based stand-ins for five "vendors," good enough to prove the architecture, not a simulation of what a real model would say. To run it for real, bind any seat to `AnthropicProvider` (ships in this repo, needs `ANTHROPIC_API_KEY`) or write a thin wrapper around another vendor's SDK or [any-llm](https://github.com/mozilla-ai/any-llm) — see `panel/providers/README.md`.

## What this is *not*

It's not a CI gate, it's not wired into a git host, and it doesn't have a UI. It's the smallest thing that proves the mechanism: decompose a task, fan it out to independent personas on independent providers, compute a real quorum, and write down what happened in a form a human can audit later. Everything past that — webhook triggers, a PR-bot front end, a database for the dissent log instead of a markdown table — is integration work on top of this core, not a change to it.

## License

MIT.
