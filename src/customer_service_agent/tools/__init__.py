"""Tools available to the customer service agent."""

from customer_service_agent.tools.customer_service import (
    CUSTOMER_SERVICE_TOOLS,
    get_order_history,
    lookup_customer,
    process_refund,
)
from customer_service_agent.tools.tech_support import (
    TECH_SUPPORT_TOOLS,
    check_device_compatibility,
    run_diagnostic,
)

__all__ = [
    "CUSTOMER_SERVICE_TOOLS",
    "TECH_SUPPORT_TOOLS",
    "get_order_history",
    "lookup_customer",
    "process_refund",
    "check_device_compatibility",
    "run_diagnostic",
]
