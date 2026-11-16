"""Customer service AI agent built on Strands Agents and Amazon Bedrock AgentCore."""

from customer_service_agent.agents import build_agent, build_tech_support_agent
from customer_service_agent.config import Settings

__all__ = ["Settings", "build_agent", "build_tech_support_agent"]
__version__ = "0.1.0"
