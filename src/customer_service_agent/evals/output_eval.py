"""Output evaluation: does the agent produce correct, helpful responses?"""

from __future__ import annotations

from strands import Agent
from strands_evals import Case, Experiment, eval_task
from strands_evals.evaluators import OutputEvaluator

from customer_service_agent.prompts import EVAL_SYSTEM_PROMPT
from customer_service_agent.tools.customer_service import CUSTOMER_SERVICE_TOOLS

OUTPUT_RUBRIC = """
Evaluate the customer service response against the expected output:
1. Accuracy — Does it contain the correct order/tracking details? Invented or
   missing details (e.g. a made-up tracking number) must score low.
2. Tone — Is it professional and empathetic?
3. Completeness — Does it fully address the customer's concern?

Score 1.0 only if accuracy is correct AND tone and completeness are met.
Score 0.5 if partially met (e.g. right tone but wrong/missing facts).
Score 0.0 if the information is inadequate, invented, or incorrect.
"""

OUTPUT_CASES = [
    Case[str, str](
        name="order-status-check",
        input="I'm customer C-1001. Where is my USB-C Hub order?",
        expected_output=(
            "The USB-C Hub is shipped with tracking TRK-887766, "
            "estimated delivery 2025-05-06."
        ),
    ),
    Case[str, str](
        name="delayed-order-empathy",
        input="I'm customer C-1002. My keyboard order is delayed and I'm frustrated!",
        expected_output=(
            "Acknowledge frustration, provide order status for the delayed "
            "mechanical keyboard with tracking info."
        ),
    ),
    Case[str, str](
        name="unknown-customer",
        input="I'm customer C-9999. What are my orders?",
        expected_output=(
            "Inform the customer that no account was found with that ID and ask "
            "them to verify."
        ),
    ),
]


def print_reasons(report) -> None:
    for i, score in enumerate(report.scores):
        name = report.cases[i].get("name", f"case-{i}")
        mark = "PASS" if report.test_passes[i] else "FAIL"
        reason = report.reasons[i] if i < len(report.reasons) else "(no reason returned)"
        print(f"\n[{mark}] {name}  (score {score:.2f})")
        print(f"   {reason}")


@eval_task()
def weak_agent():
    """No tools — it can't look up real data, so it guesses. Expect LOW scores."""
    return Agent(
        system_prompt="You are a customer service agent. Answer as best you can.",
        callback_handler=None,
    )


@eval_task()
def good_agent():
    """Has tools — it looks up the real data. Expect HIGH scores."""
    return Agent(
        tools=CUSTOMER_SERVICE_TOOLS,
        system_prompt=EVAL_SYSTEM_PROMPT,
        callback_handler=None,
    )


def run_output_eval():
    evaluator = OutputEvaluator(rubric=OUTPUT_RUBRIC, include_inputs=True)

    print("Weak agent (no tools) — expect LOW scores:")
    weak_report = Experiment[str, str](
        cases=OUTPUT_CASES, evaluators=[evaluator]
    ).run_evaluations(weak_agent)
    weak_report.display(include_actual_output=True)
    print_reasons(weak_report)

    print("\nReal agent (with tools) — expect HIGH scores:")
    good_report = Experiment[str, str](
        cases=OUTPUT_CASES, evaluators=[evaluator]
    ).run_evaluations(good_agent)
    good_report.display(include_actual_output=True)
    print_reasons(good_report)

    print(
        f"\nNo-tools agent: {weak_report.overall_score:.2f}"
        f"  vs  with-tools agent: {good_report.overall_score:.2f}"
    )
    print("The gap is the eval doing its job — it catches the agent that guesses.")
    return weak_report, good_report
