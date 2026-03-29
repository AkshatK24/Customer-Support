"""
Grader for Hard Task: Payment Failure Troubleshooting

Evaluates:
    accuracy   (0.7): Called all 3 required tools (check_payment, get_order_status, search_kb)?
                      Identified root cause: gateway_timeout_post_debit?
                      Response explains reversal timeline?
    efficiency (0.2): Ratio of optimal (4) to actual steps
    quality    (0.1): Response contains required keywords about reversal/gateway

This task is intentionally harder to score perfectly on — it requires multi-step
investigation and cross-system reasoning.
"""

from __future__ import annotations
from typing import Any
from collections import Counter


def grade(
    actions_taken: list[dict[str, Any]],
    final_response: str,
    steps_used: int,
    task_config: dict[str, Any],
) -> float:
    accuracy_score = _grade_accuracy(actions_taken, final_response, task_config)
    efficiency_score = _grade_efficiency(steps_used, task_config["optimal_steps"])
    quality_score = _grade_response_quality(final_response, task_config)

    total = (
        accuracy_score * 0.7
        + efficiency_score * 0.2
        + quality_score * 0.1
    )
    return round(min(max(total, 0.0), 1.0), 3)


def _grade_accuracy(
    actions_taken: list[dict], final_response: str, task_config: dict
) -> float:
    score = 0.0
    tool_names = [a["tool"] for a in actions_taken]
    tool_params = {a["tool"]: a.get("params", {}) for a in actions_taken}

    required = task_config["required_actions"]  # check_payment, get_order_status, search_kb

    # +0.25: Called check_payment with correct transaction_id (most important — root cause)
    if "check_payment" in tool_names:
        score += 0.15
        params = tool_params.get("check_payment", {})
        if params.get("transaction_id") == task_config["required_action_params"]["check_payment"]["transaction_id"]:
            score += 0.10

    # +0.25: Called get_order_status with correct order_id
    if "get_order_status" in tool_names:
        score += 0.15
        params = tool_params.get("get_order_status", {})
        if params.get("order_id") == task_config["required_action_params"]["get_order_status"]["order_id"]:
            score += 0.10

    # +0.25: Called search_kb (any query is acceptable — tested initiative)
    if "search_kb" in tool_names:
        score += 0.25

    # +0.1: No unnecessary escalation
    if "escalate_ticket" not in tool_names:
        score += 0.1

    # Penalty for redundant calls (> 2 times for same tool)
    counts = Counter(tool_names)
    for tool, count in counts.items():
        if tool not in ("reply_customer",) and count > 2:
            score -= 0.1 * (count - 2)

    return min(max(score, 0.0), 1.0)


def _grade_efficiency(steps_used: int, optimal_steps: int) -> float:
    if steps_used <= 0:
        return 0.0
    return min(optimal_steps / steps_used, 1.0)


def _grade_response_quality(response: str, task_config: dict) -> float:
    if not response:
        return 0.0
    response_lower = response.lower()
    keywords = task_config["required_response_keywords"]
    threshold = task_config["required_response_keywords_count"]
    matches = sum(1 for kw in keywords if kw.lower() in response_lower)
    return 1.0 if matches >= threshold else matches / threshold
