"""Unified multi-provider LLM wrapper (LiteLLM).

This is the single chokepoint where provider quirks live, so profiles and the
orchestrator stay provider-agnostic. Swap the body of `complete()` if we ever
move off LiteLLM; the rest of the app only knows this interface.
"""

from __future__ import annotations

from typing import Any

# Claude models where sampling params are removed (HTTP 400) or deprecated, and
# where reasoning is controlled via `effort` + adaptive thinking instead.
_CLAUDE_NO_SAMPLING = (
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-fable",
    "fable-5",
)
_SAMPLING_KEYS = ("temperature", "top_p", "top_k", "budget_tokens")


def _is_claude_no_sampling(model: str) -> bool:
    m = model.lower()
    return any(tag in m for tag in _CLAUDE_NO_SAMPLING)


def sanitize_params(model: str, params: dict[str, Any] | None) -> dict[str, Any]:
    """Drop params a given model would reject and translate intent.

    For Claude 4.x reasoning models: strip temperature/top_p/top_k/budget_tokens
    (they 400) and default to adaptive thinking. For other providers: pass through.
    """
    out: dict[str, Any] = dict(params or {})
    if _is_claude_no_sampling(model):
        for key in _SAMPLING_KEYS:
            out.pop(key, None)
        out.setdefault("thinking", {"type": "adaptive"})
    return out


class LLMClient:
    """Thin wrapper over litellm.completion."""

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        system: str | None = None,
        params: dict[str, Any] | None = None,
        json_mode: bool = False,
    ) -> str:
        import litellm  # imported lazily so tests can import sanitize_params without the dep

        msgs: list[dict[str, str]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        kwargs: dict[str, Any] = {"model": model, "messages": msgs, **sanitize_params(model, params)}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = litellm.completion(**kwargs)
        return resp.choices[0].message.content or ""

    def run_profile(self, profile: dict[str, Any], user_content: str, *, json_mode: bool = False) -> str:
        """Convenience: dispatch a hardcoded/seed profile dict."""
        return self.complete(
            model=profile["model"],
            system=profile.get("system_prompt"),
            messages=[{"role": "user", "content": user_content}],
            params=profile.get("params"),
            json_mode=json_mode,
        )
