"""
Grader for Medium Task: Refund Request

Evaluates:
    accuracy   (0.7): Called get_order_status AND check_payment with correct IDs?
                      Successfully established both conditions: cancellable + refund_eligible?
    efficiency (0.2): Ratio of optimal (3) to actual steps
    quality    (0.1): Response mentions cancellation confirmation + refund timeline
"""

from __future__ import annotations
from typing import Any


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

    # +0.3: Called get_order_status with correct order_id
    if "get_order_status" in tool_names:
        score += 0.2
        params = tool_params.get("get_order_status", {})
        if params.get("order_id") == task_config["required_action_params"]["get_order_status"]["order_id"]:
            score += 0.1

    # +0.4: Called check_payment with correct transaction_id
    if "check_payment" in tool_names:
        score += 0.2
        params = tool_params.get("check_payment", {})
        if params.get("transaction_id") == task_config["required_action_params"]["check_payment"]["transaction_id"]:
            score += 0.2

    # +0.2: Did NOT escalate — this task has a straightforward resolution
    if "escalate_ticket" not in tool_names:
        score += 0.2

    # -0.1 penalty per repeated redundant call (if called same tool > 2 times)
    from collections import Counter
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
