"""Deterministic mock providers that stand in for real model vendors.

These exist so the Panel can be demoed end-to-end without live API keys
for five different vendors. They are NOT a simulation of what an LLM would
say — they are simple, rule-based pattern checks, each tuned to resemble
one persona's blind spots, so the demo produces genuinely different
findings per "vendor" instead of identical boilerplate.

Swap any of these out for AnthropicProvider, or a provider you write for
OpenAI/Gemini/Grok/DeepSeek (see providers/README.md), without touching
anything else in the package.
"""

from __future__ import annotations

import re

from .base import Provider, ProviderInfo


class MockProvider(Provider):
    """A deterministic, pattern-matching stand-in for a real model vendor.

    `bias` controls which kinds of issues this mock vendor is relatively
    good at catching, which is the point: real models disagree for real
    reasons, and the demo should show disagreement, not unanimous noise.
    """

    def __init__(self, vendor: str, bias: str = "general"):
        self._vendor = vendor
        self._bias = bias

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(vendor=self._vendor, model=f"{self._vendor}-mock-1")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        # The orchestrator passes the task text and the persona's framing in
        # user_prompt; the persona name is embedded by the caller so the mock
        # can decide which checks to run. This keeps MockProvider dumb and
        # the real intelligence (persona framing) in personas.py.
        findings = []

        is_negative_pass = "NEGATIVE APPROACH" in system_prompt

        if self._bias in ("developer",):
            if re.search(r"\bTODO\b|\bFIXME\b|\bhack\b", user_prompt, re.I):
                findings.append(
                    "Task text references unfinished or hacky work directly."
                )

        if self._bias in ("security", "general"):
            if re.search(r"\bcache\b", user_prompt, re.I) and re.search(
                r"certif|auth|permission|credential", user_prompt, re.I
            ):
                findings.append(
                    "A cached value is used for an authorization/certification "
                    "check. If the cache has any staleness window, a decision "
                    "made during that window may act on revoked or expired status."
                )
            if re.search(r"\bapi[_ ]?key\b|\bsecret\b|\bpassword\b", user_prompt, re.I):
                findings.append(
                    "Credential-like material is referenced directly in the "
                    "task text. Confirm it is not being hardcoded or logged."
                )

        if self._bias in ("test", "general"):
            if not re.search(r"\btest|\bvalidate|\bverify", user_prompt, re.I):
                findings.append(
                    "No test or validation step is mentioned for this change. "
                    "Recommend stating what evidence would show this works."
                )
            if re.search(
                r"\bfallback\b|\bbackup\b|\bretry\b", user_prompt, re.I
            ) and not re.search(r"failure-path test", user_prompt, re.I):
                findings.append(
                    "Fallback/retry logic is mentioned but no failure-path test "
                    "case is described. The failure path is usually where the "
                    "real bugs live."
                )

        if self._bias in ("ops", "general"):
            if re.search(
                r"\bscal|\bcapacity|\bload\b", user_prompt, re.I
            ) and not re.search(r"runbook entry", user_prompt, re.I):
                findings.append(
                    "Capacity or scaling behavior is implicated. Confirm there is "
                    "a runbook entry or alert for this path."
                )

        if self._bias in ("requirements", "general"):
            if len(user_prompt.split()) < 25:
                findings.append(
                    "This task statement is short enough that an agent "
                    "implementing it will have to fill several gaps with "
                    "assumptions. Consider stating the constraints explicitly."
                )

        if not findings:
            text = "No issues found in this persona's area of review."
            if is_negative_pass:
                text = "Checked and clear. " + text
                text += "\nVERDICT: APPROVE"
            return text

        if is_negative_pass:
            # The negative approach must produce either a specific finding or
            # an explicit "checked and clear" - never a vague "looks fine".
            text = "Negative-approach findings:\n- " + "\n- ".join(findings)
            text += "\nVERDICT: DISSENT"
            return text

        return "Reviewed. Noted the following for the record:\n- " + "\n- ".join(
            findings
        )
