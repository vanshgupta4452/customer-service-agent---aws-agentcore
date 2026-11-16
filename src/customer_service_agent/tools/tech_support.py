"""Mock technical support tools used by the specialist agent."""

from __future__ import annotations

from strands import tool

KNOWN_ISSUES = {
    "Wireless Headphones": (
        "Known Bluetooth 5.0 pairing issue with older devices. "
        "Fix: Reset headphones (hold power 10s), then re-pair."
    ),
    "USB-C Hub": (
        "Some laptops require USB-C alt mode. "
        "Check laptop specs for DisplayPort over USB-C support."
    ),
    "Mechanical Keyboard": (
        "Firmware v2.1 has a key ghosting bug. Update to v2.3 via manufacturer website."
    ),
}


@tool
def check_device_compatibility(device: str, issue: str) -> str:
    """Check if a device has known compatibility issues.

    Args:
        device: The device name or model
        issue: Description of the issue
    """
    for device_name, fix in KNOWN_ISSUES.items():
        if device_name.lower() in device.lower():
            return f"Known issue found for {device_name}: {fix}"
    return (
        f"No known issues found for '{device}'. Recommend standard troubleshooting: "
        "restart device, check connections, update drivers."
    )


@tool
def run_diagnostic(device: str) -> str:
    """Run a remote diagnostic check on a device.

    Args:
        device: The device name or model to diagnose
    """
    return (
        f"Diagnostic results for {device}:\n"
        f"- Firmware: v2.1 (update available: v2.3)\n"
        f"- Connection: Stable\n"
        f"- Battery: 85%\n"
        f"- Last sync: 2 hours ago\n"
        f"Recommendation: Update firmware to resolve known issues."
    )


TECH_SUPPORT_TOOLS = [check_device_compatibility, run_diagnostic]
