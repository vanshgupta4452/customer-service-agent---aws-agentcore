"""Technical support specialist agent and its agents-as-tools wrapper."""

from __future__ import annotations

from strands import Agent, tool

from customer_service_agent.prompts import TECH_SUPPORT_SYSTEM_PROMPT
from customer_service_agent.tools.tech_support import TECH_SUPPORT_TOOLS


def build_tech_support_agent(model=None) -> Agent:
    """Build a silent specialist agent for device troubleshooting."""
    kwargs = {
        "tools": TECH_SUPPORT_TOOLS,
        "system_prompt": TECH_SUPPORT_SYSTEM_PROMPT,
        "callback_handler": None,
    }
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)


def create_tech_support_tool(model=None):
    """Create a ``tech_support_specialist`` tool that delegates to a specialist agent.

    This is the agents-as-tools pattern: the orchestrator calls the specialist
    like any other tool and relays its answer to the customer.
    """

    @tool
    def tech_support_specialist(issue_description: str) -> str:
        """Escalate a technical issue to the tech support specialist agent.
        Use this when a customer has a device problem, connectivity issue,
        or needs technical troubleshooting beyond basic order/account help.

        Args:
            issue_description: Detailed description of the technical issue including device name and symptoms
        """
        specialist = build_tech_support_agent(model=model)
        print("\n[DELEGATION] Tech support specialist activated")
        response = specialist(issue_description)
        print("[DELEGATION] Specialist responded")
        return str(response)

    return tech_support_specialist
