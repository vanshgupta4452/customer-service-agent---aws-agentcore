"""Deterministic rate limiting for tool calls."""

from __future__ import annotations

from strands.hooks import (
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    HookProvider,
    HookRegistry,
)


class RateLimiterHook(HookProvider):
    """Caps each tool at ``max_calls`` per agent invocation."""

    def __init__(self, max_calls: int = 3):
        self.max_calls = max_calls
        self.counts: dict[str, int] = {}

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset)
        registry.add_callback(BeforeToolCallEvent, self.check)

    def reset(self, event: BeforeInvocationEvent) -> None:
        """Reset counts at the start of each invocation."""
        self.counts = {}
        print("[HOOK] Rate limiter reset")

    def check(self, event: BeforeToolCallEvent) -> None:
        """Check and enforce the rate limit before each tool call."""
        name = event.tool_use["name"]
        self.counts[name] = self.counts.get(name, 0) + 1
        print(f"[HOOK] {name}: call {self.counts[name]}/{self.max_calls}")

        if self.counts[name] > self.max_calls:
            event.cancel_tool = (
                f"'{name}' hit the {self.max_calls}-call limit. "
                "Do NOT call this tool again."
            )
            print(f"[HOOK] BLOCKED: {name} exceeded limit!")
