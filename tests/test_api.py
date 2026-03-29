"""
Black-box API integration tests for Customer Support Environment.

These tests call the HTTP API using `requests` against a live server
subprocess started by conftest.py (port 7862).  No internal imports needed.
"""

import requests


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────

def test_health_check(server):
    """Server /health endpoint must return 200 and healthy status."""
    resp = requests.get(f"{server}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"


# ─────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────

class TestReset:

    def test_reset_default_is_easy(self, server):
        """Reset with no args should default to easy task."""
        resp = requests.post(f"{server}/reset", json={}, timeout=5)
        assert resp.status_code == 200
        obs = resp.json()["observation"]
        meta = obs.get("metadata", {})
        assert meta.get("difficulty") == "easy"
        assert "ORD-1001" in str(meta)

    def test_reset_easy_explicit(self, server):
        """Reset with task='easy' should return easy metadata."""
        resp = requests.post(f"{server}/reset", json={"task": "easy"}, timeout=5)
        assert resp.status_code == 200
        meta = resp.json()["observation"]["metadata"]
        assert meta["difficulty"] == "easy"
        assert meta["support_tier"] == "L1"

    def test_reset_medium(self, server):
        """Reset with task='medium' should load medium task."""
        resp = requests.post(f"{server}/reset", json={"task": "medium"}, timeout=5)
        assert resp.status_code == 200
        meta = resp.json()["observation"]["metadata"]
        assert meta["difficulty"] == "medium"
        assert meta["support_tier"] == "L2"

    def test_reset_hard(self, server):
        """Reset with task='hard' should load hard task."""
        resp = requests.post(f"{server}/reset", json={"task": "hard"}, timeout=5)
        assert resp.status_code == 200
        meta = resp.json()["observation"]["metadata"]
        assert meta["difficulty"] == "hard"
        assert meta["support_tier"] == "L3"

    def test_reset_clears_state(self, server):
        """A fresh reset should have step_count=0 and reward=0."""
        resp = requests.post(f"{server}/reset", json={"task": "easy"}, timeout=5)
        data = resp.json()
        assert data["observation"]["reward"] == 0.0
        assert data["observation"]["done"] is False


# ─────────────────────────────────────────────
# STEP — TOOL CALLS
# ─────────────────────────────────────────────

class TestStepTools:

    def test_get_order_status_valid(self, api):
        """get_order_status with valid ID should return order data + positive reward."""
        result = api["step"]("get_order_status", {"order_id": "ORD-1001"})
        assert result["reward"] > 0.0
        assert result["observation"]["done"] is False
        obs_result = result["observation"].get("result", {})
        assert obs_result.get("status") == "in_transit"
        assert obs_result.get("shipping_carrier") == "FedEx"

    def test_get_order_status_invalid_id(self, api):
        """get_order_status with invalid ID → negative reward + error."""
        result = api["step"]("get_order_status", {"order_id": "FAKE-9999"})
        assert result["reward"] < 0.0
        assert "error" in result["observation"].get("result", {})

    def test_check_payment_valid(self, api):
        """check_payment with valid TXN → payment data returned."""
        result = api["step"]("check_payment", {"transaction_id": "TXN-5001"})
        obs_result = result["observation"].get("result", {})
        assert obs_result.get("transaction_id") == "TXN-5001"
        assert "status" in obs_result

    def test_search_kb_valid_query(self, api):
        """search_kb with a valid query → articles returned + positive reward."""
        result = api["step"]("search_kb", {"query": "refund PayPal cancelled"})
        assert result["reward"] > 0.0
        obs_result = result["observation"].get("result", {})
        assert "articles" in obs_result
        assert obs_result["count"] > 0

    def test_search_kb_short_query(self, api):
        """search_kb with a too-short query → negative reward + error."""
        result = api["step"]("search_kb", {"query": "a"})
        assert result["reward"] < 0.0
        obs_result = result["observation"].get("result", {})
        assert "error" in obs_result

    def test_unknown_tool_name(self, api):
        """Calling a non-existent tool → negative reward, episode continues."""
        result = api["step"]("hack_the_system", {})
        assert result["reward"] <= 0.0
        assert result["observation"]["done"] is False


# ─────────────────────────────────────────────
# STEP — EPISODE TERMINATION
# ─────────────────────────────────────────────

class TestEpisodeTermination:

    def test_reply_customer_ends_episode(self, api):
        """reply_customer should end the episode (done=True)."""
        # First gather data so grader has context
        api["step"]("get_order_status", {"order_id": "ORD-1001"})
        result = api["step"]("reply_customer", {
            "response_text": (
                "Hi Alex! Your order ORD-1001 is currently in_transit via FedEx "
                "and will arrive on 2026-03-30. Tracking: FX123456789."
            )
        })
        assert result["observation"]["done"] is True

    def test_reply_customer_perfect_response_high_reward(self, api):
        """A response with all required keywords should produce a high final reward."""
        api["step"]("get_order_status", {"order_id": "ORD-1001"})
        result = api["step"]("reply_customer", {
            "response_text": (
                "Hi Alex! Your order ORD-1001 is currently in_transit via FedEx "
                "and will arrive on 2026-03-30. Tracking: FX123456789."
            )
        })
        total_reward = result["observation"]["metadata"].get("total_reward", result["reward"])
        assert total_reward > 0.4, f"Expected positive total reward, got {total_reward}"

    def test_reply_customer_short_response_penalized(self, api):
        """A one-word response should be penalized."""
        result = api["step"]("reply_customer", {"response_text": "ok"})
        assert result["reward"] < 0.0

    def test_escalate_ticket_ends_episode(self, api):
        """escalate_ticket should end the episode with a penalty."""
        result = api["step"]("escalate_ticket", {})
        assert result["observation"]["done"] is True
        assert result["reward"] < 0.0


# ─────────────────────────────────────────────
# FULL EPISODE — END-TO-END FLOWS
# ─────────────────────────────────────────────

class TestFullEpisodes:

    def test_easy_optimal_path(self, server):
        """
        Simulate a perfect Easy episode:
        1. Reset to easy
        2. get_order_status(ORD-1001) → +reward
        3. reply_customer(with FedEx/date keywords) → done=True, high score
        """
        requests.post(f"{server}/reset", json={"task": "easy"}, timeout=5)

        def step(tool, args):
            return requests.post(f"{server}/step", json={
                "action": {"type": "call_tool", "tool_name": tool, "arguments": args}
            }, timeout=5).json()

        r1 = step("get_order_status", {"order_id": "ORD-1001"})
        assert r1["reward"] > 0.0

        r2 = step("reply_customer", {
            "response_text": (
                "Hi! Your order ORD-1001 is in_transit via FedEx "
                "and arrives on 2026-03-30."
            )
        })
        assert r2["observation"]["done"] is True
        meta = r2["observation"].get("metadata", {})
        grade = meta.get("grade_score", meta.get("total_reward", 0.0))
        assert grade >= 0.4, f"Expected grade ≥0.4, got {grade}"

    def test_medium_optimal_path(self, server):
        """
        Simulate a perfect Medium episode:
        1. get_order_status(ORD-1002) + check_payment(TXN-5002) + reply_customer
        """
        requests.post(f"{server}/reset", json={"task": "medium"}, timeout=5)

        def step(tool, args):
            return requests.post(f"{server}/step", json={
                "action": {"type": "call_tool", "name": tool, "arguments": args}
            }, timeout=5).json()

        r1 = step("get_order_status", {"order_id": "ORD-1002"})
        assert not r1["observation"]["done"]

        r2 = step("check_payment", {"transaction_id": "TXN-5002"})
        assert not r2["observation"]["done"]

        r3 = step("reply_customer", {
            "response_text": (
                "Your order ORD-1002 has been cancelled. "
                "A PayPal refund will be processed within 24 hours. "
                "Typically takes 3-5 business days to appear."
            )
        })
        assert r3["observation"]["done"] is True

    def test_hard_optimal_path(self, server):
        """
        Simulate a near-optimal Hard episode:
        1. check_payment(TXN-5004) + get_order_status(ORD-1004) + search_kb + reply_customer
        """
        requests.post(f"{server}/reset", json={"task": "hard"}, timeout=5)

        def step(tool, args):
            return requests.post(f"{server}/step", json={
                "action": {"type": "call_tool", "name": tool, "arguments": args}
            }, timeout=5).json()

        step("check_payment", {"transaction_id": "TXN-5004"})
        step("get_order_status", {"order_id": "ORD-1004"})
        step("search_kb", {"query": "payment failed gateway timeout"})

        r4 = step("reply_customer", {
            "response_text": (
                "Our gateway experienced a timeout. Your bank has debited $39.99 "
                "but the charge will be reversed within 3-5 business days. "
                "Reference: KB-003 Gateway Timeout Policy."
            )
        })
        assert r4["observation"]["done"] is True
