"""Build the customer service agent with every workshop capability wired in."""

from __future__ import annotations

from strands import Agent

from customer_service_agent.agents.tech_support import create_tech_support_tool
from customer_service_agent.config import SKILLS_DIR, Settings, build_model
from customer_service_agent.hooks.rate_limiter import RateLimiterHook
from customer_service_agent.prompts import CUSTOMER_SERVICE_SYSTEM_PROMPT
from customer_service_agent.session import build_session_manager
from customer_service_agent.steering.handlers import RefundWorkflowHandler, tone_handler
from customer_service_agent.tools.customer_service import CUSTOMER_SERVICE_TOOLS


def build_agent(
    settings: Settings | None = None,
    *,
    model=None,
    session_manager=None,
) -> Agent:
    """Build a customer service agent.

    Capabilities are toggled through :class:`Settings`: workflow skills,
    steering handlers, per-tool rate limiting, multi-agent delegation, and
    persistent session memory.
    """
    settings = settings or Settings.from_env()

    if model is None:
        model = build_model(settings)

    tools = list(CUSTOMER_SERVICE_TOOLS)
    plugins = []
    hooks = []

    if settings.enable_skills:
        from strands import AgentSkills

        plugins.append(AgentSkills(skills=[str(SKILLS_DIR)]))

    if settings.enable_steering:
        plugins.extend([RefundWorkflowHandler(), tone_handler])

    if settings.enable_multi_agent:
        tools.append(create_tech_support_tool(model=model))

    if settings.enable_rate_limit:
        hooks.append(RateLimiterHook(max_calls=settings.max_tool_calls))

    if session_manager is None and settings.use_session_persistence:
        session_manager = build_session_manager(settings)

    kwargs = {
        "tools": tools,
        "system_prompt": CUSTOMER_SERVICE_SYSTEM_PROMPT,
        "context_manager": "auto",
    }
    if model is not None:
        kwargs["model"] = model
    if plugins:
        kwargs["plugins"] = plugins
    if hooks:
        kwargs["hooks"] = hooks
    if session_manager is not None:
        kwargs["session_manager"] = session_manager

    return Agent(**kwargs)
