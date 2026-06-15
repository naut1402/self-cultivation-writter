"""AC for #6b: the wrapper must never send sampling params to Claude 4.x models,
and must pass them through for models that accept them."""

from app.llm.client import resolve_api_base, sanitize_params


def test_strips_temperature_for_claude_opus_4_8():
    out = sanitize_params("anthropic/claude-opus-4-8", {"temperature": 0.8, "max_tokens": 4000})
    assert "temperature" not in out
    assert out["max_tokens"] == 4000
    assert out["thinking"] == {"type": "adaptive"}


def test_strips_all_sampling_keys_for_claude_4x():
    out = sanitize_params(
        "anthropic/claude-sonnet-4-6",
        {"temperature": 0.5, "top_p": 0.9, "top_k": 40, "budget_tokens": 1000},
    )
    for key in ("temperature", "top_p", "top_k", "budget_tokens"):
        assert key not in out


def test_passes_temperature_through_for_openai():
    out = sanitize_params("openai/gpt-4o", {"temperature": 0.7})
    assert out["temperature"] == 0.7
    assert "thinking" not in out


def test_passes_through_for_openrouter_deepseek():
    out = sanitize_params("openrouter/deepseek/deepseek-chat", {"temperature": 0.9})
    assert out["temperature"] == 0.9


def test_ollama_resolves_to_local_base():
    assert resolve_api_base("ollama_chat/qwen2.5:14b") == "http://localhost:11434"


def test_first_party_providers_have_no_api_base():
    assert resolve_api_base("anthropic/claude-opus-4-8") is None
    # openai/ slug only gets a base when OPENAI_BASE_URL is configured (unset in tests)
    assert resolve_api_base("openai/gpt-4o") is None
