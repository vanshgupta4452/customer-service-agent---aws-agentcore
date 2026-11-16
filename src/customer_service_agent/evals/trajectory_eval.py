"""Trajectory evaluation: did the agent call the right tools in the right order?"""

from __future__ import annotations

from strands import Agent
from strands_evals import Case, Experiment
from strands_evals.evaluators import TrajectoryEvaluator
from strands_evals.extractors import tools_use_extractor
from strands_evals.types import TaskOutput

from customer_service_agent.prompts import NAIVE_REFUND_PROMPT, STEERED_REFUND_PROMPT
from customer_service_agent.tools.customer_service import CUSTOMER_SERVICE_TOOLS

TRAJECTORY_RUBRIC = """
Evaluate whether the agent followed the expected tool sequence:
- The expected tools should appear in order (extra tools in between are OK).
- Score 1.0 if the expected sequence is followed correctly.
- Score 0.5 if tools are called but in wrong order.
- Score 0.0 if expected tools are missing entirely.
"""

TRAJECTORY_CASES = [
    Case[str, str](
        name="refund-workflow",
        input="Customer C-1001 wants a refund for order ORD-5521 ($79.99). Process it now.",
        expected_trajectory=["lookup_customer", "get_order_history", "process_refund"],
    ),
    Case[str, str](
        name="info-lookup-only",
        input="Look up customer C-1001 and tell me their order history.",
        expected_trajectory=["lookup_customer", "get_order_history"],
    ),
    Case[str, str](
        name="customer-lookup-only",
        input="Look up customer C-1002's account info.",
        expected_trajectory=["lookup_customer"],
    ),
]


def _print_reasons(report) -> None:
    for i, score in enumerate(report.scores):
        name = report.cases[i].get("name", f"case-{i}")
        mark = "PASS" if report.test_passes[i] else "FAIL"
        reason = report.reasons[i] if i < len(report.reasons) else "(no reason returned)"
        print(f"\n[{mark}] {name}  (score {score:.2f})")
        print(f"   {reason}")


def _run_with(prompt: str):
    def task(case: Case) -> TaskOutput:
        agent = Agent(
            tools=CUSTOMER_SERVICE_TOOLS,
            system_prompt=prompt,
            callback_handler=None,
        )
        response = agent(case.input)
        trajectory = tools_use_extractor.extract_agent_tools_used_from_messages(
            agent.messages
        )
        return TaskOutput(output=str(response), trajectory=trajectory)

    return task


def _build_evaluator() -> TrajectoryEvaluator:
    evaluator = TrajectoryEvaluator(rubric=TRAJECTORY_RUBRIC, include_inputs=True)
    sample_agent = Agent(tools=CUSTOMER_SERVICE_TOOLS)
    tool_descriptions = tools_use_extractor.extract_tools_description(
        sample_agent, is_short=True
    )
    evaluator.update_trajectory_description(tool_descriptions)
    return evaluator


def run_trajectory_eval():
    evaluator = _build_evaluator()

    print("Naive agent (skips verification) — expect a FAILED refund trajectory:")
    naive_report = Experiment[str, str](
        cases=TRAJECTORY_CASES, evaluators=[evaluator]
    ).run_evaluations(_run_with(NAIVE_REFUND_PROMPT))
    naive_report.display(
        include_actual_trajectory=True, include_expected_trajectory=True
    )
    _print_reasons(naive_report)

    print("\nSteered agent (enforced workflow) — expect all trajectories to PASS:")
    steered_report = Experiment[str, str](
        cases=TRAJECTORY_CASES, evaluators=[evaluator]
    ).run_evaluations(_run_with(STEERED_REFUND_PROMPT))
    steered_report.display(
        include_actual_trajectory=True, include_expected_trajectory=True
    )
    _print_reasons(steered_report)

    print(
        f"\nNaive agent: {naive_report.overall_score:.2f}"
        f"  vs  steered agent: {steered_report.overall_score:.2f}"
    )
    print("The steering handlers are what close that gap — and the eval is what proves it.")
    return naive_report, steered_report
