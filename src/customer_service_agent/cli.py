"""Command-line entry point for the customer service agent."""

from __future__ import annotations

import argparse
import sys

from customer_service_agent.agents.customer_service import build_agent
from customer_service_agent.config import Settings


def _add_common_settings(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--model-provider",
        choices=["bedrock", "nova", "ollama", "gemini", "llama", "openai"],
        help="Model provider (default: from CS_AGENT_MODEL_PROVIDER or bedrock).",
    )
    parser.add_argument("--model-id", help="Explicit model id to use.")
    parser.add_argument(
        "--base-url",
        help="Base URL for an OpenAI-compatible endpoint (e.g. the Llama API).",
    )
    parser.add_argument("--session-id", help="Session id to persist/resume.")
    parser.add_argument("--session-dir", help="Directory for local session files.")
    parser.add_argument(
        "--max-tool-calls",
        type=int,
        help="Per-invocation tool-call limit (default: from CS_AGENT_MAX_TOOL_CALLS or 5).",
    )
    parser.add_argument("--no-skills", action="store_true", help="Disable workflow skills.")
    parser.add_argument(
        "--no-steering", action="store_true", help="Disable steering handlers."
    )
    parser.add_argument(
        "--no-rate-limit", action="store_true", help="Disable the tool rate limiter."
    )
    parser.add_argument(
        "--no-multi-agent", action="store_true", help="Disable specialist delegation."
    )
    parser.add_argument(
        "--no-session",
        action="store_true",
        help="Do not persist the conversation between runs.",
    )


def _settings_from_args(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env()
    overrides: dict = {}

    if args.model_provider:
        overrides["model_provider"] = args.model_provider
    if args.model_id:
        overrides["model_id"] = args.model_id
    if args.base_url:
        overrides["base_url"] = args.base_url
    if args.session_id:
        overrides["session_id"] = args.session_id
    if args.session_dir:
        from pathlib import Path

        overrides["session_dir"] = Path(args.session_dir)
    if args.max_tool_calls is not None:
        overrides["max_tool_calls"] = args.max_tool_calls
    if args.no_skills:
        overrides["enable_skills"] = False
    if args.no_steering:
        overrides["enable_steering"] = False
    if args.no_rate_limit:
        overrides["enable_rate_limit"] = False
    if args.no_multi_agent:
        overrides["enable_multi_agent"] = False
    if args.no_session:
        overrides["use_session_persistence"] = False

    return settings.with_overrides(**overrides) if overrides else settings


def _resolve_interrupts(agent, result) -> None:
    """Ask the operator to approve paused tool calls, then resume the agent."""
    while getattr(result, "stop_reason", None) == "interrupt":
        responses = []
        for interrupt in result.interrupts:
            answer = input(
                f"\n\nApproval needed ({interrupt.name}): {interrupt.reason}\n"
                "Approve? (y/N): "
            )
            responses.append(
                {
                    "interruptResponse": {
                        "interruptId": interrupt.id,
                        "response": answer.strip().lower() == "y",
                    }
                }
            )
        print("\nAgent: ", end="")
        result = agent(responses)


def _chat(args: argparse.Namespace) -> int:
    settings = _settings_from_args(args)
    agent = build_agent(settings)

    restored = len(agent.messages)
    print(
        f"Customer service agent (session: {settings.session_id}) - "
        "type 'quit' to exit."
    )
    if restored:
        print(f"Restored {restored} message(s) from a previous session.")
    print('Try: "Hi, I\'m customer C-1001. What are my recent orders?"\n')

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break
        if not user_input:
            continue

        print("\nAgent: ", end="")
        result = agent(user_input)
        _resolve_interrupts(agent, result)
        print()

    return 0


def _eval(args: argparse.Namespace) -> int:
    try:
        from customer_service_agent.evals.runner import run
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        print(
            "Evaluation dependencies are not installed. "
            "Install them with: pip install 'customer-service-agent[evals]'",
            file=sys.stderr,
        )
        print(f"({exc})", file=sys.stderr)
        return 1
    return run(args.which)


def _serve(args: argparse.Namespace) -> int:
    try:
        from customer_service_agent.runtime import app
    except ImportError as exc:  # pragma: no cover - depends on optional runtime deps
        print(
            "AgentCore runtime dependencies are not installed. "
            "Install them with: pip install bedrock-agentcore",
            file=sys.stderr,
        )
        print(f"({exc})", file=sys.stderr)
        return 1
    app.run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csa",
        description="Customer service AI agent (Strands Agents + Amazon Bedrock AgentCore).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("chat", help="Start an interactive multi-turn chat.")
    _add_common_settings(chat)
    chat.set_defaults(func=_chat)

    evals = sub.add_parser("eval", help="Run automated evaluations (needs the evals extra).")
    evals.add_argument(
        "--which",
        choices=["output", "trajectory", "all"],
        default="all",
        help="Which evaluation suite to run (default: all).",
    )
    evals.set_defaults(func=_eval)

    serve = sub.add_parser("serve", help="Run the AgentCore Runtime HTTP entrypoint.")
    serve.set_defaults(func=_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
