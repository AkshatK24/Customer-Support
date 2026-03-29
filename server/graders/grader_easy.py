"""
Grader for Easy Task: Order Status Inquiry

Evaluates agent performance on a 0.0-1.0 scale:
    accuracy   (0.7): Did agent call get_order_status with correct order_id?
                      Does response contain required info (carrier, delivery date)?
    efficiency (0.2): How close was agent to the optimal 2-step path?
    quality    (0.1): Does response contain required keywords?
"""

from __future__ import annotations
from typing import Any


def grade(
    actions_taken: list[dict[str, Any]],
    final_response: str,
    steps_used: int,
    task_config: dict[str, Any],
) -> float:
    """
    Grade a completed Easy task episode.

    Args:
        actions_taken: List of {tool, params, result} dicts from the episode
        final_response: The text of the reply_customer call
        steps_used: Total steps the agent took
        task_config: The task configuration dict (TASK_EASY_CONFIG)

    Returns:
        Normalized score between 0.0 and 1.0
    """
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
    """Check if the agent retrieved the order with the correct order_id."""
    score = 0.0
    tool_names = [a["tool"] for a in actions_taken]
    tool_params = {a["tool"]: a.get("params", {}) for a in actions_taken}

    # +0.5: Called get_order_status
    if "get_order_status" in tool_names:
        score += 0.5
        # +0.3: Used the correct order_id
        params = tool_params.get("get_order_status", {})
        if params.get("order_id") == task_config["required_action_params"]["get_order_status"]["order_id"]:
            score += 0.3

    # +0.2: Did NOT escalate unnecessarily (penalize over-escalation)
    if "escalate_ticket" not in tool_names:
        score += 0.2

    return min(score, 1.0)


def _grade_efficiency(steps_used: int, optimal_steps: int) -> float:
    """Grade efficiency: how close was the agent to the optimal step count?"""
    if steps_used <= 0:
        return 0.0
    # Ratio capped at 1.0 — using fewer steps can't score above optimal
    return min(optimal_steps / steps_used, 1.0)


def _grade_response_quality(response: str, task_config: dict) -> float:
    """Check if final response contains required keywords."""
    if not response:
        return 0.0
    response_lower = response.lower()
    keywords = task_config["required_response_keywords"]
    threshold = task_config["required_response_keywords_count"]
    matches = sum(1 for kw in keywords if kw.lower() in response_lower)
    return 1.0 if matches >= threshold else matches / threshold
