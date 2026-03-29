"""
Task Hard: L3 Payment Failure Troubleshooting

Scenario:
    Customer reports: "My payment failed but my bank shows the money was taken."
    Order: ORD-1004 (status: pending — payment not confirmed on our side)
    Payment: TXN-5004 (status: "failed" due to gateway timeout AFTER bank debit)
    — Bank charged customer, but our gateway timed out and marked as failed.
    — Auto-reversal is pending (3-5 business days).

Expected agent workflow (multi-step reasoning):
    1. check_payment(transaction_id="TXN-5004") — see gateway failure + bank_debit_confirmed
    2. get_order_status(order_id="ORD-1004") — verify order is stuck in pending
    3. search_kb(query="payment failed money deducted gateway") — find KB-003
    4. reply_customer(response_text="...gateway timeout...reversal in progress...3-5 days...")

Optimal steps: 4
This is an L3 scenario requiring cross-system investigation and root cause diagnosis.
"""

from __future__ import annotations
from typing import Any

TASK_HARD_CONFIG: dict[str, Any] = {
    "task_id": "hard_payment_failure",
    "difficulty": "hard",
    "support_tier": "L3",
    "description": "Payment Failure with Bank Deduction — Gateway Investigation",
    "customer_id": "CUST-104",
    "order_id": "ORD-1004",
    "transaction_id": "TXN-5004",

    "customer_query": (
        "I tried placing an order (ORD-1004, USB-C Hub) and the checkout page said "
        "'payment failed'. But my bank app shows that $39.99 was charged from my card "
        "ending in 9988. My order shows as pending. What happened? Did you take my "
        "money? When will I get it back?"
    ),

    # Agent MUST call these tools to diagnose the issue correctly
    "required_actions": ["check_payment", "get_order_status", "search_kb"],
    "required_action_params": {
        "check_payment": {"transaction_id": "TXN-5004"},
        "get_order_status": {"order_id": "ORD-1004"},
        "search_kb": {},  # any query is acceptable
    },

    # Response must explain the gateway timeout + reversal timeline
    "required_response_keywords": ["reversal", "3-5", "gateway", "automatic"],
    "required_response_keywords_count": 2,

    "optimal_steps": 4,

    "solution": {
        "root_cause": "gateway_timeout_post_debit",
        "bank_charged": True,
        "order_not_placed": True,
        "reversal_in_progress": True,
        "refund_eta_days": 5,
    },
}
