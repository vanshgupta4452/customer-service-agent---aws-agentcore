"""AgentCore Runtime entrypoint.

The AgentCore CLI (and container deploys) start the agent from ``main.py``.
This thin wrapper re-exports the ``app`` defined in
``customer_service_agent.runtime``.
"""

from customer_service_agent.runtime import app

if __name__ == "__main__":
    app.run()
