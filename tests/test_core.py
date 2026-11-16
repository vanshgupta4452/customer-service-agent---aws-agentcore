from types import SimpleNamespace

import pytest

from customer_service_agent.config import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_LLAMA_MODEL,
    DEFAULT_NOVA_MODEL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OPENAI_COMPATIBLE_MODEL,
    SKILLS_DIR,
    Settings,
    build_model,
)
from customer_service_agent.hooks.rate_limiter import RateLimiterHook


def test_settings_overrides_are_immutable_copies():
    settings = Settings()
    updated = settings.with_overrides(enable_steering=False, max_tool_calls=9)

    assert settings.enable_steering is True
    assert updated.enable_steering is False
    assert updated.max_tool_calls == 9


def test_resolve_model_id_defaults():
    assert Settings(model_provider="nova").resolve_model_id() == DEFAULT_NOVA_MODEL
    assert Settings(model_provider="ollama").resolve_model_id() == DEFAULT_OLLAMA_MODEL
    assert Settings(model_provider="llama").resolve_model_id() == DEFAULT_LLAMA_MODEL
    assert Settings(model_provider="gemini").resolve_model_id() == DEFAULT_GEMINI_MODEL
    assert (
        Settings(model_provider="openai").resolve_model_id()
        == DEFAULT_OPENAI_COMPATIBLE_MODEL
    )
    assert Settings(model_provider="bedrock").resolve_model_id() is None
    assert Settings(model_provider="bedrock", model_id="x").resolve_model_id() == "x"


def test_from_env_reads_ollama_cloud_settings(monkeypatch):
    monkeypatch.setenv("CS_AGENT_MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("CS_AGENT_OLLAMA_HOST", "https://ollama.com")
    monkeypatch.setenv("CS_AGENT_MODEL_ID", "gpt-oss:120b")
    monkeypatch.setenv("OLLAMA_API_KEY", "test-ollama-key")

    settings = Settings.from_env()

    assert settings.model_provider == "ollama"
    assert settings.ollama_host == "https://ollama.com"
    assert settings.model_id == "gpt-oss:120b"
    assert settings.ollama_api_key == "test-ollama-key"


def test_from_env_reads_gemini_api_key(monkeypatch):
    monkeypatch.setenv("CS_AGENT_MODEL_PROVIDER", "gemini")
    monkeypatch.setenv("CS_AGENT_MODEL_ID", "gemini-3.5-flash")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    settings = Settings.from_env()

    assert settings.model_provider == "gemini"
    assert settings.model_id == "gemini-3.5-flash"
    assert settings.gemini_api_key == "test-gemini-key"


def test_api_key_providers_require_keys():
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        build_model(Settings(model_provider="gemini"))
    with pytest.raises(ValueError, match="LLAMA_API_KEY"):
        build_model(Settings(model_provider="llama"))
    with pytest.raises(ValueError, match="API key"):
        build_model(Settings(model_provider="openai"))


def test_rate_limiter_cancels_after_limit():
    hook = RateLimiterHook(max_calls=1)
    hook.reset(SimpleNamespace())

    first = SimpleNamespace(tool_use={"name": "lookup_customer"}, cancel_tool=None)
    hook.check(first)
    assert first.cancel_tool is None

    second = SimpleNamespace(tool_use={"name": "lookup_customer"}, cancel_tool=None)
    hook.check(second)
    assert second.cancel_tool is not None
    assert "limit" in second.cancel_tool


def test_skills_are_packaged():
    skills = sorted(path.parent.name for path in SKILLS_DIR.glob("*/SKILL.md"))
    assert skills == ["account-troubleshooting", "order-tracking", "refund-processing"]
