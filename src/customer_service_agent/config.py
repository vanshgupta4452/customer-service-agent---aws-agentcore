"""Configuration for the customer service agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SKILLS_DIR = PACKAGE_ROOT / "skills"

DEFAULT_SESSION_ID = "customer-session-001"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_NOVA_MODEL = "amazon.nova-pro-v1:0"
DEFAULT_LLAMA_MODEL = "Llama-4-Maverick-17B-128E-Instruct-FP8"
DEFAULT_OPENAI_COMPATIBLE_MODEL = DEFAULT_LLAMA_MODEL
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"

# Meta's OpenAI-compatible endpoint (recommended when using the Llama API
# through the OpenAI SDK/provider). Llama API also has a native base URL.
LLAMA_API_BASE_URL = "https://api.llama.com/compat/v1"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings for building agents.

    Every field can be overridden from the environment (see ``from_env``) or
    programmatically, which keeps the harness config-driven rather than
    hard-coded.
    """

    model_provider: str = "bedrock"
    model_id: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    ollama_host: str = "http://localhost:11434"
    ollama_api_key: str | None = None
    gemini_api_key: str | None = None
    session_id: str = DEFAULT_SESSION_ID
    session_dir: Path = Path("./sessions")
    max_tool_calls: int = 5
    enable_skills: bool = True
    enable_steering: bool = True
    enable_rate_limit: bool = True
    enable_multi_agent: bool = True
    use_session_persistence: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from ``CS_AGENT_*`` environment variables."""
        from dotenv import load_dotenv

        load_dotenv()
        return cls(
            model_provider=os.getenv("CS_AGENT_MODEL_PROVIDER", "bedrock").strip().lower(),
            model_id=os.getenv("CS_AGENT_MODEL_ID") or None,
            api_key=os.getenv("LLAMA_API_KEY") or os.getenv("CS_AGENT_API_KEY") or None,
            base_url=os.getenv("CS_AGENT_BASE_URL") or None,
            ollama_host=os.getenv("CS_AGENT_OLLAMA_HOST", "http://localhost:11434"),
            ollama_api_key=os.getenv("OLLAMA_API_KEY") or None,
            gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
            session_id=os.getenv("CS_AGENT_SESSION_ID", DEFAULT_SESSION_ID),
            session_dir=Path(os.getenv("CS_AGENT_SESSION_DIR", "./sessions")),
            max_tool_calls=int(os.getenv("CS_AGENT_MAX_TOOL_CALLS", "5")),
            enable_skills=_env_bool("CS_AGENT_ENABLE_SKILLS", True),
            enable_steering=_env_bool("CS_AGENT_ENABLE_STEERING", True),
            enable_rate_limit=_env_bool("CS_AGENT_ENABLE_RATE_LIMIT", True),
            enable_multi_agent=_env_bool("CS_AGENT_ENABLE_MULTI_AGENT", True),
            use_session_persistence=_env_bool("CS_AGENT_USE_SESSION_PERSISTENCE", True),
        )

    def with_overrides(self, **kwargs) -> "Settings":
        """Return a copy of the settings with the given fields replaced."""
        return replace(self, **kwargs)

    def resolve_model_id(self) -> str | None:
        """Resolve the effective model id for the configured provider."""
        if self.model_id:
            return self.model_id
        if self.model_provider == "ollama":
            return DEFAULT_OLLAMA_MODEL
        if self.model_provider == "nova":
            return DEFAULT_NOVA_MODEL
        if self.model_provider == "llama":
            return DEFAULT_LLAMA_MODEL
        if self.model_provider in {"openai", "openai-compatible"}:
            return DEFAULT_OPENAI_COMPATIBLE_MODEL
        if self.model_provider == "gemini":
            return DEFAULT_GEMINI_MODEL
        return None


def build_model(settings: Settings):
    """Create a Strands model for the configured provider.

    Returning ``None`` for the default Bedrock provider lets Strands pick its
    default model, which keeps this project aligned with the SDK defaults.
    """
    provider = settings.model_provider
    model_id = settings.resolve_model_id()

    if provider == "llama":
        if not settings.api_key:
            raise ValueError(
                "Using the Llama API requires LLAMA_API_KEY (or CS_AGENT_API_KEY)."
            )
        from strands.models.llamaapi import LlamaAPIModel

        return LlamaAPIModel(
            client_args={"api_key": settings.api_key},
            model_id=model_id or DEFAULT_LLAMA_MODEL,
        )

    if provider in {"openai", "openai-compatible"}:
        if not settings.api_key:
            raise ValueError(
                "Using an OpenAI-compatible endpoint requires an API key "
                "(LLAMA_API_KEY or CS_AGENT_API_KEY)."
            )
        from strands.models.openai import OpenAIModel

        client_args = {"api_key": settings.api_key}
        base_url = settings.base_url or LLAMA_API_BASE_URL
        client_args["base_url"] = base_url
        return OpenAIModel(
            client_args=client_args,
            model_id=model_id or DEFAULT_OPENAI_COMPATIBLE_MODEL,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("Using Gemini requires GEMINI_API_KEY.")
        from strands.models.gemini import GeminiModel

        return GeminiModel(
            client_args={"api_key": settings.gemini_api_key},
            model_id=model_id or DEFAULT_GEMINI_MODEL,
        )

    if provider == "ollama":
        from strands.models import OllamaModel

        client_args: dict = {}
        if settings.ollama_api_key:
            client_args["headers"] = {
                "Authorization": f"Bearer {settings.ollama_api_key}"
            }

        return OllamaModel(
            host=settings.ollama_host,
            ollama_client_args=client_args or None,
            model_id=model_id or DEFAULT_OLLAMA_MODEL,
        )

    if provider in {"bedrock", "nova"}:
        if model_id is None:
            return None
        from strands.models import BedrockModel

        return BedrockModel(model_id=model_id)

    raise ValueError(
        f"Unsupported CS_AGENT_MODEL_PROVIDER={provider!r}. Use 'gemini', 'llama', "
        "'openai', 'bedrock', 'nova', or 'ollama'."
    )
