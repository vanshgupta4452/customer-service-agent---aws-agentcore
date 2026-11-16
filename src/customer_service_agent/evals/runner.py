"""Run one or both evaluation suites."""

from __future__ import annotations


def run(which: str = "all") -> int:
    try:
        import nest_asyncio

        nest_asyncio.apply()
    except ImportError:
        pass

    if which in {"output", "all"}:
        from customer_service_agent.evals.output_eval import run_output_eval

        run_output_eval()

    if which in {"trajectory", "all"}:
        from customer_service_agent.evals.trajectory_eval import run_trajectory_eval

        run_trajectory_eval()

    return 0
