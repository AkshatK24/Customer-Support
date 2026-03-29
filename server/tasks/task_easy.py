"""
Task Easy: L1 Order Status Inquiry

Scenario:
    Customer asks: "Where is my order? It's been a few days."
    Order: ORD-1001 (in_transit via FedEx, estimated delivery tomorrow)

Expected agent workflow:
    1. get_order_status(order_id="ORD-1001")
    2. reply_customer(response_text="...order is in transit, arriving 2026-03-30...")

Optimal steps: 2
Success criteria: agent returns correct delivery date + carrier + tracking number
"""

from __future__ import annotations
from typing import Any

TASK_EASY_CONFIG: dict[str, Any] = {
    "task_id": "easy_order_status",
    "difficulty": "easy",
    "support_tier": "L1",
    "description": "Order Status Inquiry",
    "customer_id": "CUST-101",
    "order_id": "ORD-1001",
    "transaction_id": "TXN-5001",

    # The customer's query presented to the agent
    "customer_query": (
        "Hi, I placed an order a few days ago (order ORD-1001) and I'm wondering "
        "where it is. Can you give me an update on my order status and when I can "
        "expect it to arrive?"
    ),

    # What the agent MUST do to succeed
    "required_actions": ["get_order_status"],             # at minimum
    "required_action_params": {"get_order_status": {"order_id": "ORD-1001"}},

    # Keywords the final response MUST contain to pass response quality check
    "required_response_keywords": ["in_transit", "FedEx", "2026-03-30"],
    # At least 2 of these must appear (case-insensitive)
    "required_response_keywords_count": 2,

    # Optimal step count for efficiency scoring
    "optimal_steps": 2,

    # Fields the grader checks in retrieved order data
    "solution": {
        "order_status": "in_transit",
        "shipping_carrier": "FedEx",
        "estimated_delivery": "2026-03-30",
        "tracking_number": "FX123456789",
    },
}
