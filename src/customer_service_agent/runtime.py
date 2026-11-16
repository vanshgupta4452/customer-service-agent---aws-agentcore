"""Amazon Bedrock AgentCore Runtime entrypoint.

Deploy this module as the agent's handler. AgentCore manages session state, so
local session persistence is disabled here. A steering handler can pause a
refund for human approval; the caller resumes the same invocation by sending
``{"interrupt_responses": [{"interruptId": "...", "response": true}]}``.
"""

from __future__ import annotations

import json
import logging
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from customer_service_agent.agents.customer_service import build_agent
from customer_service_agent.config import Settings

logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

_settings = Settings.from_env().with_overrides(use_session_persistence=False)
_agent = None
_pending_interrupts = []


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent(_settings)
    return _agent


def _interrupt_response(interrupts) -> dict:
    return {
        "status": "interrupted",
        "interrupts": [
            {"interruptId": interrupt.id, "name": interrupt.name, "reason": interrupt.reason}
            for interrupt in interrupts
        ],
    }


def _extract_prompt(raw_prompt) -> str:
    try:
        parsed = json.loads(raw_prompt)
        prompt = parsed.get("prompt", raw_prompt)
    except (TypeError, json.JSONDecodeError):
        prompt = raw_prompt

    if not prompt:
        raise ValueError("Missing required field: prompt")
    return prompt


def invoke(payload, context, api_key=None):
    global _pending_interrupts, _settings, _agent

    if api_key and _settings.gemini_api_key != api_key:
        _settings = _settings.with_overrides(gemini_api_key=api_key)
        _agent = None

    agent = get_agent()

    interrupt_responses = payload.get("interrupt_responses")
    if interrupt_responses:
        result = agent(
            [{"interruptResponse": response} for response in interrupt_responses]
        )
    else:
        prompt = _extract_prompt(payload.get("prompt"))

        if _pending_interrupts:
            return _interrupt_response(_pending_interrupts)

        result = agent(prompt)

    if result.stop_reason == "interrupt":
        _pending_interrupts = list(result.interrupts)
        return _interrupt_response(_pending_interrupts)

    _pending_interrupts = []
    return str(result).strip()


_credential_provider = os.getenv("CREDENTIAL_GEMINI_NAME")
if (
    _credential_provider
    and not os.getenv("GEMINI_API_KEY")
    and os.getenv("LOCAL_DEV") != "1"
):
    from bedrock_agentcore.identity import requires_api_key

    invoke = requires_api_key(provider_name=_credential_provider)(invoke)

app.entrypoint(invoke)


if __name__ == "__main__":
    app.run()
