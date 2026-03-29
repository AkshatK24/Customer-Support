"""
Unit tests for the grader functions.

These call grader.grade() directly since graders are pure functions
with no Pydantic / OpenEnv dependencies — they just take dicts and return floats.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.graders.grader_easy import grade as grade_easy
from server.graders.grader_medium import grade as grade_medium
from server.graders.grader_hard import grade as grade_hard
from server.tasks.task_easy import TASK_EASY_CONFIG
from server.tasks.task_medium import TASK_MEDIUM_CONFIG
from server.tasks.task_hard import TASK_HARD_CONFIG


# ─────────────────────────────────────────────
# EASY GRADER
# ─────────────────────────────────────────────

class TestEasyGrader:

    def test_perfect_score(self):
        """Optimal path: correct tool + keywords in response → ~1.0."""
        actions = [
            {"step": 1, "tool": "get_order_status",
             "params": {"order_id": "ORD-1001"}, "result": {"status": "in_transit"}}
        ]
        response = (
            "Hi Alex! Your order ORD-1001 is currently in_transit "
            "via FedEx and will arrive on 2026-03-30."
        )
        score = grade_easy(actions, response, steps_used=2, task_config=TASK_EASY_CONFIG)
        assert score >= 0.9, f"Expected ≥0.9 for perfect path, got {score}"
        assert score <= 1.0

    def test_correct_tool_wrong_keywords(self):
        """Correct tool, vague response → mid-range score."""
        actions = [
            {"step": 1, "tool": "get_order_status",
             "params": {"order_id": "ORD-1001"}, "result": {"status": "in_transit"}}
        ]
        response = "Your order is on its way."  # Missing FedEx / date keywords
        score = grade_easy(actions, response, steps_used=2, task_config=TASK_EASY_CONFIG)
        assert 0.5 < score < 0.95, f"Expected mid-range, got {score}"

    def test_no_tools_called(self):
        """No tools used → very low accuracy score."""
        score = grade_easy([], "I think your order is fine.", steps_used=1, task_config=TASK_EASY_CONFIG)
        # Grader still gives +0.2 bonus for "no escalation" even without tool calls
        assert score < 0.45, f"Expected <0.45 for no tools, got {score}"
        # And must be much lower than a correct solution
        perfect_score = grade_easy(
            [{"step": 1, "tool": "get_order_status", "params": {"order_id": "ORD-1001"}, "result": {}}],
            "Your order ORD-1001 via FedEx arrives 2026-03-30.", 2, TASK_EASY_CONFIG
        )
        assert score < perfect_score

    def test_wrong_order_id(self):
        """Used wrong order ID → reduced accuracy."""
        actions = [
            {"step": 1, "tool": "get_order_status",
             "params": {"order_id": "ORD-9999"}, "result": {"error": "not found"}}
        ]
        response = "I couldn't find your order, sorry."
        score = grade_easy(actions, response, steps_used=2, task_config=TASK_EASY_CONFIG)
        assert score < 0.7, f"Expected <0.7 for wrong order_id, got {score}"

    def test_escalation_penalty(self):
        """Escalating without investigation → heavy penalty."""
        actions = [
            {"step": 1, "tool": "escalate_ticket", "params": {}, "result": {"escalated": True}}
        ]
        score = grade_easy(actions, "Escalated to L2.", steps_used=1, task_config=TASK_EASY_CONFIG)
        assert score < 0.5, f"Expected <0.5 for unnecessary escalation, got {score}"

    def test_over_steps_efficiency_penalty(self):
        """Taking 10 steps where 2 is optimal → efficiency penalty."""
        actions = [
            {"step": i, "tool": "get_order_status",
             "params": {"order_id": "ORD-1001"}, "result": {"status": "in_transit"}}
            for i in range(1, 11)
        ]
        response = "Your order ORD-1001 is via FedEx arriving 2026-03-30."
        score = grade_easy(actions, response, steps_used=10, task_config=TASK_EASY_CONFIG)
        # Still has accuracy & quality, but efficiency should drag it down
        optimal_score = grade_easy(actions[:1], response, steps_used=2, task_config=TASK_EASY_CONFIG)
        assert score < optimal_score, "Over-stepping should score lower than optimal"

    def test_score_bounds(self):
        """Score must always be between 0.0 and 1.0."""
        for response_text in ["", "ok", "Your order ORD-1001 via FedEx 2026-03-30"]:
            score = grade_easy([], response_text, steps_used=0, task_config=TASK_EASY_CONFIG)
            assert 0.0 <= score <= 1.0, f"Score out of bounds: {score}"


# ─────────────────────────────────────────────
# MEDIUM GRADER
# ─────────────────────────────────────────────

class TestMediumGrader:

    def test_perfect_path(self):
        """Optimal 3-step path → high score."""
        actions = [
            {"step": 1, "tool": "get_order_status",
             "params": {"order_id": "ORD-1002"}, "result": {"status": "processing"}},
            {"step": 2, "tool": "check_payment",
             "params": {"transaction_id": "TXN-5002"}, "result": {"status": "confirmed"}},
        ]
        response = (
            "Your order ORD-1002 has been cancelled. "
            "A PayPal refund will be processed within 24 hours."
        )
        score = grade_medium(actions, response, steps_used=3, task_config=TASK_MEDIUM_CONFIG)
        assert score >= 0.8, f"Expected ≥0.8 for medium perfect path, got {score}"

    def test_missing_payment_check(self):
        """Skipped payment check → lower accuracy."""
        actions = [
            {"step": 1, "tool": "get_order_status",
             "params": {"order_id": "ORD-1002"}, "result": {"status": "processing"}},
        ]
        response = "Your order will be cancelled."
        score = grade_medium(actions, response, steps_used=2, task_config=TASK_MEDIUM_CONFIG)
        # Compare to perfect path
        perfect_score = grade_medium(
            [{"step": 1, "tool": "get_order_status", "params": {"order_id": "ORD-1002"}, "result": {}},
             {"step": 2, "tool": "check_payment", "params": {"transaction_id": "TXN-5002"}, "result": {}}],
            response, steps_used=3, task_config=TASK_MEDIUM_CONFIG
        )
        assert score < perfect_score, "Missing tools should score worse"

    def test_score_bounds(self):
        """Score must always be between 0.0 and 1.0."""
        score = grade_medium([], "", steps_used=0, task_config=TASK_MEDIUM_CONFIG)
        assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────
# HARD GRADER
# ─────────────────────────────────────────────

class TestHardGrader:

    def test_perfect_path(self):
        """Optimal 4-step path → high score."""
        actions = [
            {"step": 1, "tool": "check_payment",
             "params": {"transaction_id": "TXN-5004"}, "result": {"status": "failed"}},
            {"step": 2, "tool": "get_order_status",
             "params": {"order_id": "ORD-1004"}, "result": {"status": "pending"}},
            {"step": 3, "tool": "search_kb",
             "params": {"query": "payment failed gateway timeout"}, "result": {"count": 2}},
        ]
        response = (
            "There was a gateway timeout causing the charge. "
            "Your bank will reverse the debit within 3-5 business days. "
            "Reference KB-003 for more details."
        )
        score = grade_hard(actions, response, steps_used=4, task_config=TASK_HARD_CONFIG)
        assert score >= 0.7, f"Expected ≥0.7 for hard perfect path, got {score}"

    def test_score_bounds(self):
        """Score must always be between 0.0 and 1.0."""
        score = grade_hard([], "", steps_used=0, task_config=TASK_HARD_CONFIG)
        assert 0.0 <= score <= 1.0
