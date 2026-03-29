"""
Rich mock data layer for the Customer Service Environment.

Simulates real-world backend systems:
- Orders DB: full lifecycle data with tracking, shipping carrier, ETA
- Payments DB: gateway logs, response codes, failure reasons
- Knowledge Base: ranked articles by category
- Customers DB: profiles with account tiers and order history
- Support Policies: refund windows, escalation rules

All data is in-memory and deterministic — no external dependencies.
"""

from __future__ import annotations
from typing import Any

# ---------------------------------------------------------------------------
# ORDERS DATABASE
# Simulates a CRM / Order Management System
# Lifecycle: pending → confirmed → processing → shipped → in_transit → delivered
# ---------------------------------------------------------------------------

ORDERS_DB: dict[str, dict[str, Any]] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "CUST-101",
        "items": [
            {"name": "Wireless Headphones", "sku": "WH-BT500", "qty": 1, "price": 79.99},
        ],
        "total": 79.99,
        "status": "in_transit",
        "shipping_carrier": "FedEx",
        "tracking_number": "FX123456789",
        "shipping_status": "Out for delivery",
        "estimated_delivery": "2026-03-30",
        "order_date": "2026-03-25",
        "last_updated": "2026-03-29T07:00:00Z",
        "payment_transaction_id": "TXN-5001",
        "cancellable": False,  # Already shipped
        "returnable": False,   # Not yet delivered
        "return_window_days": 30,
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_id": "CUST-102",
        "items": [
            {"name": "Standing Desk Mat", "sku": "DM-ANTI36", "qty": 1, "price": 45.00},
            {"name": "Cable Management Kit", "sku": "CMK-20", "qty": 2, "price": 12.00},
        ],
        "total": 69.00,
        "status": "processing",
        "shipping_carrier": None,
        "tracking_number": None,
        "shipping_status": "Preparing for shipment",
        "estimated_delivery": "2026-04-02",
        "order_date": "2026-03-28",
        "last_updated": "2026-03-29T05:00:00Z",
        "payment_transaction_id": "TXN-5002",
        "cancellable": True,   # Not yet shipped
        "returnable": False,
        "return_window_days": 30,
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_id": "CUST-103",
        "items": [
            {"name": "Mechanical Keyboard", "sku": "KB-MX1000", "qty": 1, "price": 149.99},
        ],
        "total": 149.99,
        "status": "delivered",
        "shipping_carrier": "UPS",
        "tracking_number": "UPS998877665",
        "shipping_status": "Delivered on 2026-03-20",
        "estimated_delivery": "2026-03-20",
        "order_date": "2026-03-15",
        "last_updated": "2026-03-20T14:30:00Z",
        "payment_transaction_id": "TXN-5003",
        "cancellable": False,
        "returnable": True,   # Still within 30-day return window
        "return_window_days": 30,
        "return_window_expires": "2026-04-19",
    },
    "ORD-1004": {
        "order_id": "ORD-1004",
        "customer_id": "CUST-104",
        "items": [
            {"name": "USB-C Hub", "sku": "HUB-7PT", "qty": 1, "price": 39.99},
        ],
        "total": 39.99,
        "status": "pending",
        "shipping_carrier": None,
        "tracking_number": None,
        "shipping_status": "Payment being verified",
        "estimated_delivery": "2026-04-04",
        "order_date": "2026-03-29",
        "last_updated": "2026-03-29T10:00:00Z",
        "payment_transaction_id": "TXN-5004",
        "cancellable": True,
        "returnable": False,
        "return_window_days": 30,
    },
    "ORD-1005": {
        "order_id": "ORD-1005",
        "customer_id": "CUST-101",
        "items": [
            {"name": "Laptop Stand", "sku": "LS-ALU", "qty": 1, "price": 59.99},
        ],
        "total": 59.99,
        "status": "shipped",
        "shipping_carrier": "DHL",
        "tracking_number": "DHL44556677",
        "shipping_status": "In transit — arrived at regional hub",
        "estimated_delivery": "2026-03-31",
        "order_date": "2026-03-26",
        "last_updated": "2026-03-28T22:00:00Z",
        "payment_transaction_id": "TXN-5005",
        "cancellable": False,
        "returnable": False,
        "return_window_days": 30,
    },
    "ORD-1006": {
        "order_id": "ORD-1006",
        "customer_id": "CUST-103",
        "items": [
            {"name": "Monitor Light Bar", "sku": "MLB-PRO", "qty": 1, "price": 35.00},
        ],
        "total": 35.00,
        "status": "confirmed",
        "shipping_carrier": None,
        "tracking_number": None,
        "shipping_status": "Order confirmed — awaiting warehouse pickup",
        "estimated_delivery": "2026-04-01",
        "order_date": "2026-03-29",
        "last_updated": "2026-03-29T09:30:00Z",
        "payment_transaction_id": "TXN-5006",
        "cancellable": True,
        "returnable": False,
        "return_window_days": 30,
    },
}

# ---------------------------------------------------------------------------
# PAYMENTS DATABASE
# Simulates a Payment Gateway / Finance System with realistic gateway data
# ---------------------------------------------------------------------------

PAYMENTS_DB: dict[str, dict[str, Any]] = {
    "TXN-5001": {
        "transaction_id": "TXN-5001",
        "order_id": "ORD-1001",
        "customer_id": "CUST-101",
        "amount": 79.99,
        "currency": "USD",
        "status": "completed",           # completed | pending | failed | refunded | disputed
        "payment_method": "credit_card",
        "card_last4": "4242",
        "processor": "Stripe",
        "gateway_response_code": "00",   # 00 = approved
        "gateway_message": "Transaction approved",
        "failure_reason": None,
        "created_at": "2026-03-25T10:05:00Z",
        "refund_eligible": False,        # Order in transit, can't auto-refund
        "refund_status": None,
        "refund_policy": "Refund available after delivery + return initiated",
    },
    "TXN-5002": {
        "transaction_id": "TXN-5002",
        "order_id": "ORD-1002",
        "customer_id": "CUST-102",
        "amount": 69.00,
        "currency": "USD",
        "status": "completed",
        "payment_method": "paypal",
        "card_last4": None,
        "processor": "PayPal",
        "gateway_response_code": "00",
        "gateway_message": "Transaction approved",
        "failure_reason": None,
        "created_at": "2026-03-28T14:22:00Z",
        "refund_eligible": True,         # Order cancellable, full refund available
        "refund_status": None,
        "refund_policy": "Full refund within 24 hours of cancellation",
    },
    "TXN-5003": {
        "transaction_id": "TXN-5003",
        "order_id": "ORD-1003",
        "customer_id": "CUST-103",
        "amount": 149.99,
        "currency": "USD",
        "status": "completed",
        "payment_method": "credit_card",
        "card_last4": "1234",
        "processor": "Stripe",
        "gateway_response_code": "00",
        "gateway_message": "Transaction approved",
        "failure_reason": None,
        "created_at": "2026-03-15T09:15:00Z",
        "refund_eligible": True,         # Delivered, within return window
        "refund_status": None,
        "refund_policy": "Refund within 5-7 business days after return received",
    },
    "TXN-5004": {
        # Hard task: payment failed but gateway shows debit
        "transaction_id": "TXN-5004",
        "order_id": "ORD-1004",
        "customer_id": "CUST-104",
        "amount": 39.99,
        "currency": "USD",
        "status": "failed",              # Our system shows failed
        "payment_method": "credit_card",
        "card_last4": "9988",
        "processor": "Stripe",
        "gateway_response_code": "51",   # 51 = Insufficient funds (but bank debited)
        "gateway_message": "Card declined — insufficient funds",
        "failure_reason": "gateway_timeout_post_debit",  # Key detail: bank was charged
        "bank_debit_confirmed": True,    # Bank side shows debit
        "gateway_settlement_status": "pending_reversal",
        "created_at": "2026-03-29T10:00:00Z",
        "refund_eligible": True,
        "refund_status": "pending",      # Automatic reversal in progress
        "refund_eta": "2026-04-01",      # 3-5 business days
        "refund_policy": "Automatic reversal initiated — 3-5 business days",
        "notes": "Gateway timed out after bank authorization. Reversal auto-triggered.",
    },
    "TXN-5005": {
        "transaction_id": "TXN-5005",
        "order_id": "ORD-1005",
        "customer_id": "CUST-101",
        "amount": 59.99,
        "currency": "USD",
        "status": "completed",
        "payment_method": "credit_card",
        "card_last4": "4242",
        "processor": "Stripe",
        "gateway_response_code": "00",
        "gateway_message": "Transaction approved",
        "failure_reason": None,
        "created_at": "2026-03-26T11:00:00Z",
        "refund_eligible": False,
        "refund_status": None,
        "refund_policy": "Refund available after delivery + return initiated",
    },
    "TXN-5006": {
        "transaction_id": "TXN-5006",
        "order_id": "ORD-1006",
        "customer_id": "CUST-103",
        "amount": 35.00,
        "currency": "USD",
        "status": "completed",
        "payment_method": "credit_card",
        "card_last4": "5678",
        "processor": "Stripe",
        "gateway_response_code": "00",
        "gateway_message": "Transaction approved",
        "failure_reason": None,
        "created_at": "2026-03-29T09:30:00Z",
        "refund_eligible": True,
        "refund_status": None,
        "refund_policy": "Full refund if order cancelled before shipment",
    },
}

# ---------------------------------------------------------------------------
# KNOWLEDGE BASE
# Simulates an internal support wiki with relevance scoring
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE: list[dict[str, Any]] = [
    {
        "article_id": "KB-001",
        "category": "shipping",
        "title": "Tracking Your Order",
        "keywords": ["track", "order", "where", "status", "shipping", "delivery", "fedex", "ups", "dhl"],
        "content": (
            "To track your order, visit our Order Status page with your order ID. "
            "Tracking numbers are activated 2-4 hours after shipment. "
            "Delays of 1-2 days are common during peak periods."
        ),
        "applicable_to": ["ORD-1001", "ORD-1005"],
    },
    {
        "article_id": "KB-002",
        "category": "returns",
        "title": "Return & Refund Policy",
        "keywords": ["return", "refund", "cancel", "money back", "policy", "30 day", "exchange"],
        "content": (
            "We offer 30-day hassle-free returns on all items. "
            "For cancellations before shipment, a full refund is issued within 24 hours. "
            "For returns after delivery, refunds are processed within 5-7 business days "
            "after we receive the item. Items must be in original condition."
        ),
        "applicable_to": ["ORD-1002", "ORD-1003"],
    },
    {
        "article_id": "KB-003",
        "category": "payments",
        "title": "Payment Failed — Money Still Deducted",
        "keywords": ["payment failed", "charged", "deducted", "money taken", "still charged", "bank", "gateway", "reversal"],
        "content": (
            "If your payment failed but your bank shows a charge, this is typically a "
            "gateway timeout issue where the bank pre-authorized the amount before our "
            "system received confirmation. In such cases, an automatic reversal is "
            "initiated within 24 hours. The funds appear back in your account within "
            "3-5 business days depending on your bank."
        ),
        "applicable_to": ["TXN-5004"],
    },
    {
        "article_id": "KB-004",
        "category": "account",
        "title": "Resetting Your Password",
        "keywords": ["password", "login", "reset", "forgot", "account", "access"],
        "content": (
            "To reset your password, click 'Forgot Password' on the login page. "
            "A reset link will be sent to your registered email within 5 minutes. "
            "Check your spam folder if not received. Links expire after 1 hour."
        ),
        "applicable_to": [],
    },
    {
        "article_id": "KB-005",
        "category": "shipping",
        "title": "Shipping Delays & Carrier Issues",
        "keywords": ["delayed", "late", "slow", "carrier", "issue", "stuck", "transit"],
        "content": (
            "Delays can occur due to weather, high demand, or carrier issues. "
            "If your shipment hasn't updated in 5+ days, contact the carrier directly "
            "with your tracking number, or escalate to us for a carrier inquiry. "
            "We can file a trace request after 7 business days without movement."
        ),
        "applicable_to": ["ORD-1001", "ORD-1005"],
    },
    {
        "article_id": "KB-006",
        "category": "payments",
        "title": "Payment Processing & Pending Charges",
        "keywords": ["pending", "processing", "authorization", "hold", "charge", "payment"],
        "content": (
            "Payment authorizations appear as 'pending' in your bank before settlement. "
            "Most charges settle within 1-2 business days. "
            "If your order is cancelled, pending charges are released within 3-5 days."
        ),
        "applicable_to": [],
    },
    {
        "article_id": "KB-007",
        "category": "orders",
        "title": "Cancelling an Order",
        "keywords": ["cancel", "stop", "order", "before shipment", "cancel order"],
        "content": (
            "Orders can be cancelled before shipment for a full refund. "
            "Once an order is in 'processing' or 'confirmed' status, cancellation "
            "is possible via your account or by contacting support. "
            "Shipped orders must be returned after delivery."
        ),
        "applicable_to": ["ORD-1002", "ORD-1006"],
    },
    {
        "article_id": "KB-008",
        "category": "payments",
        "title": "Refund Timelines",
        "keywords": ["refund", "when", "how long", "timeline", "days", "return", "processed"],
        "content": (
            "Refund timelines vary by payment method: "
            "Credit/Debit cards: 5-7 business days after approval. "
            "PayPal: 3-5 business days. "
            "Cancellation refunds (before shipment): 24 hours. "
            "Contact your bank if not received after the stated period."
        ),
        "applicable_to": [],
    },
]

# ---------------------------------------------------------------------------
# CUSTOMERS DATABASE
# ---------------------------------------------------------------------------

CUSTOMERS_DB: dict[str, dict[str, Any]] = {
    "CUST-101": {
        "customer_id": "CUST-101",
        "name": "Alex Johnson",
        "email": "alex.johnson@email.com",
        "account_tier": "premium",       # premium gets priority support
        "member_since": "2023-01-15",
        "order_count": 12,
        "order_ids": ["ORD-1001", "ORD-1005"],
        "contact_preference": "email",
        "notes": "Loyal customer — handle with care.",
    },
    "CUST-102": {
        "customer_id": "CUST-102",
        "name": "Priya Sharma",
        "email": "priya.sharma@email.com",
        "account_tier": "basic",
        "member_since": "2025-09-10",
        "order_count": 2,
        "order_ids": ["ORD-1002"],
        "contact_preference": "email",
        "notes": None,
    },
    "CUST-103": {
        "customer_id": "CUST-103",
        "name": "Marcus Chen",
        "email": "marcus.chen@email.com",
        "account_tier": "basic",
        "member_since": "2024-06-20",
        "order_count": 5,
        "order_ids": ["ORD-1003", "ORD-1006"],
        "contact_preference": "chat",
        "notes": None,
    },
    "CUST-104": {
        "customer_id": "CUST-104",
        "name": "Sara Müller",
        "email": "sara.muller@email.com",
        "account_tier": "basic",
        "member_since": "2026-01-05",
        "order_count": 1,
        "order_ids": ["ORD-1004"],
        "contact_preference": "email",
        "notes": "First-time customer.",
    },
}

# ---------------------------------------------------------------------------
# SUPPORT POLICIES
# ---------------------------------------------------------------------------

SUPPORT_POLICIES = {
    "return_window_days": 30,
    "cancellation_allowed_statuses": ["pending", "confirmed", "processing"],
    "refund_sla_days": {
        "pre_shipment_cancellation": 1,  # 24 hours
        "credit_card_return": 7,         # 5-7 business days
        "paypal_return": 5,
        "gateway_reversal": 5,           # 3-5 business days
    },
    "escalation_threshold_steps": 8,     # Escalate if agent uses more than 8 steps
    "max_steps_per_episode": 15,
    "premium_sla_response_hours": 4,
    "basic_sla_response_hours": 24,
}


# ---------------------------------------------------------------------------
# DATA ACCESS HELPERS
# ---------------------------------------------------------------------------

def get_order(order_id: str) -> dict[str, Any] | None:
    """Retrieve an order by ID."""
    return ORDERS_DB.get(order_id)


def get_payment(transaction_id: str) -> dict[str, Any] | None:
    """Retrieve a payment record by transaction ID."""
    return PAYMENTS_DB.get(transaction_id)


def get_customer(customer_id: str) -> dict[str, Any] | None:
    """Retrieve a customer profile by customer ID."""
    return CUSTOMERS_DB.get(customer_id)


def search_knowledge_base(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Search KB articles using keyword relevance scoring.
    Returns top_k articles sorted by match count.
    """
    query_words = set(query.lower().split())
    results: list[tuple[int, dict]] = []

    for article in KNOWLEDGE_BASE:
        score = sum(1 for kw in article["keywords"] if kw in query.lower())
        if score > 0:
            results.append((score, article))

    results.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "article_id": a["article_id"],
            "category": a["category"],
            "title": a["title"],
            "relevance_score": s,
            "content": a["content"],
        }
        for s, a in results[:top_k]
    ]
