"""
Task Medium: L2 Refund Request

Scenario:
    Customer asks to cancel order ORD-1002 and get a refund.
    Order is in "processing" status (cancellable).
    Payment TXN-5002 is via PayPal (refund_eligible=True).

Expected agent workflow:
    1. get_order_status(order_id="ORD-1002") — verify it's cancellable
    2. check_payment(transaction_id="TXN-5002") — verify refund eligibility
    3. reply_customer(response_text="...order cancelled, refund in 24 hours...")

Optimal steps: 3
Success criteria: agent verifies cancellability + refund eligibility + responds correctly
"""

from __future__ import annotations
from typing import Any

TASK_MEDIUM_CONFIG: dict[str, Any] = {
    "task_id": "medium_refund_request",
    "difficulty": "medium",
    "support_tier": "L2",
    "description": "Cancellation and Refund Request",
    "customer_id": "CUST-102",
    "order_id": "ORD-1002",
    "transaction_id": "TXN-5002",

    "customer_query": (
        "I changed my mind and want to cancel my order ORD-1002 (Standing Desk Mat "
        "and Cable Kit). I paid via PayPal. Can you cancel it and process a refund? "
        "How long will it take to get my money back?"
    ),

    # Agent MUST call these tools in a logical order
    "required_actions": ["get_order_status", "check_payment"],
    "required_action_params": {
        "get_order_status": {"order_id": "ORD-1002"},
        "check_payment": {"transaction_id": "TXN-5002"},
    },

    # Response must confirm cancellation + refund window
    "required_response_keywords": ["cancel", "refund", "24 hours", "PayPal"],
    "required_response_keywords_count": 2,

    "optimal_steps": 3,

    "solution": {
        "order_cancellable": True,
        "refund_eligible": True,
        "refund_method": "PayPal",
        "refund_eta_days": 1,  # 24 hours
    },
}
