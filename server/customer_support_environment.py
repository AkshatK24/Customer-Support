"""
Customer Service Multi-Agent Environment.

Implements MCPEnvironment with 5 FastMCP tools that simulate real customer
support backend systems:

    get_order_status(order_id)          — CRM / Order Management
    check_payment(transaction_id)       — Payment Gateway
    search_kb(query)                    — Internal Knowledge Base
    reply_customer(response_text)       — Ends episode, triggers grading
    escalate_ticket()                   — Escalates to human, ends episode

Reward shaping (continuous, per ADR-003):
    +0.2  retrieving relevant data (correct tool call)
    +0.3  identifying root issue
    +0.4  correct resolution
    -0.1  invalid/unknown parameter
    -0.2  irrelevant or empty response
    -0.5  unnecessary escalation
    -0.1  repeated same tool call (loop detection)
"""

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import uuid4

try:
    from openenv.core.env_server.mcp_environment import MCPEnvironment
    from openenv.core.env_server.types import Action, Observation, State
except ImportError:
    from openenv.core.env_server.mcp_environment import MCPEnvironment
    from openenv.core.env_server.types import Action, Observation, State

from fastmcp import FastMCP

from .data import (
    get_order,
    get_payment,
    get_customer,
    search_knowledge_base,
    SUPPORT_POLICIES,
)
from .tasks import TASK_REGISTRY
from .graders import GRADER_REGISTRY


class CustomerSupportEnvironment(MCPEnvironment):
    """
    OpenEnv environment simulating customer support workflows.

    Agents interact through 5 MCP tools to resolve customer tickets
    across 3 difficulty levels (L1 / L2 / L3 support tiers).
    """

    def __init__(self) -> None:
        """Initialize environment with FastMCP tools and reset state."""
        mcp = FastMCP("customer_support_env")

        # ---------------------------------------------------------------
        # TOOL 1: get_order_status
        # ---------------------------------------------------------------
        @mcp.tool
        def get_order_status(order_id: str) -> dict:
            """
            Retrieve the current status and details of a customer order.

            Args:
                order_id: The order identifier (e.g. "ORD-1001")

            Returns:
                Order details including status, carrier, tracking number,
                estimated delivery, and cancellation/return eligibility.
            """
            order = get_order(order_id)
            if not order:
                self._step_reward -= 0.1  # Penalty: invalid parameter
                self._record_action("get_order_status", {"order_id": order_id}, {"error": f"Order {order_id} not found"})
                return {"error": f"Order '{order_id}' not found. Please verify the order ID."}

            # Check for relevance to current task
            if self._current_task and order_id == self._current_task.get("order_id"):
                self._step_reward += 0.2   # Reward: retrieved relevant data

            self._retrieved_data["order"] = order
            self._record_action("get_order_status", {"order_id": order_id}, order)

            return {
                "order_id": order["order_id"],
                "customer_id": order["customer_id"],
                "status": order["status"],
                "items": order["items"],
                "total": order["total"],
                "order_date": order["order_date"],
                "shipping_carrier": order["shipping_carrier"],
                "tracking_number": order["tracking_number"],
                "shipping_status": order["shipping_status"],
                "estimated_delivery": order["estimated_delivery"],
                "cancellable": order["cancellable"],
                "returnable": order.get("returnable", False),
                "return_window_expires": order.get("return_window_expires"),
                "last_updated": order["last_updated"],
            }

        # ---------------------------------------------------------------
        # TOOL 2: check_payment
        # ---------------------------------------------------------------
        @mcp.tool
        def check_payment(transaction_id: str) -> dict:
            """
            Retrieve payment details and refund eligibility for a transaction.

            Args:
                transaction_id: The payment transaction ID (e.g. "TXN-5001")

            Returns:
                Payment status, gateway response, failure reason (if any),
                refund eligibility, and refund policy.
            """
            payment = get_payment(transaction_id)
            if not payment:
                self._step_reward -= 0.1  # Penalty: invalid parameter
                self._record_action("check_payment", {"transaction_id": transaction_id}, {"error": f"Transaction {transaction_id} not found"})
                return {"error": f"Transaction '{transaction_id}' not found."}

            if self._current_task and transaction_id == self._current_task.get("transaction_id"):
                self._step_reward += 0.2  # Reward: retrieved relevant data

            self._retrieved_data["payment"] = payment
            self._record_action("check_payment", {"transaction_id": transaction_id}, payment)

            result = {
                "transaction_id": payment["transaction_id"],
                "order_id": payment["order_id"],
                "amount": payment["amount"],
                "currency": payment["currency"],
                "status": payment["status"],
                "payment_method": payment["payment_method"],
                "processor": payment["processor"],
                "gateway_response_code": payment["gateway_response_code"],
                "gateway_message": payment["gateway_message"],
                "failure_reason": payment["failure_reason"],
                "created_at": payment["created_at"],
                "refund_eligible": payment["refund_eligible"],
                "refund_status": payment["refund_status"],
                "refund_policy": payment["refund_policy"],
            }

            # Include extra gateway details for hard task (bank_debit_confirmed)
            if "bank_debit_confirmed" in payment:
                result["bank_debit_confirmed"] = payment["bank_debit_confirmed"]
                result["gateway_settlement_status"] = payment["gateway_settlement_status"]
                result["refund_eta"] = payment.get("refund_eta")
                result["notes"] = payment.get("notes")

            return result

        # ---------------------------------------------------------------
        # TOOL 3: search_kb
        # ---------------------------------------------------------------
        @mcp.tool
        def search_kb(query: str) -> dict:
            """
            Search the internal knowledge base for articles matching a query.

            Args:
                query: A natural language search query (e.g. "payment failed money deducted")

            Returns:
                List of up to 3 most relevant knowledge base articles with
                title, category, relevance score, and content.
            """
            if not query or len(query.strip()) < 3:
                self._step_reward -= 0.1  # Penalty: empty/trivial query
                self._record_action("search_kb", {"query": query}, {"error": "Query too short"})
                return {"error": "Query must be at least 3 characters long."}

            results = search_knowledge_base(query, top_k=3)
            self._retrieved_data["kb_results"] = results
            self._step_reward += 0.1  # Small reward for using KB (shows initiative)
            self._record_action("search_kb", {"query": query}, results)

            if not results:
                return {"message": "No relevant articles found.", "articles": []}

            return {"articles": results, "count": len(results)}

        # ---------------------------------------------------------------
        # TOOL 4: reply_customer
        # ---------------------------------------------------------------
        @mcp.tool
        def reply_customer(response_text: str) -> dict:
            """
            Send a response to the customer and resolve the ticket.
            Calling this tool ends the episode and triggers final grading.

            Args:
                response_text: The message to send to the customer

            Returns:
                Confirmation that the response was sent and grading result.
            """
            if not response_text or len(response_text.strip()) < 10:
                self._step_reward -= 0.2  # Penalty: empty/irrelevant response
                self._record_action("reply_customer", {"response_text": response_text}, {"error": "Response too short"})
                return {"error": "Response must be at least 10 characters long."}

            self._final_response = response_text
            self._record_action("reply_customer", {"response_text": response_text}, {"sent": True})

            # Grade the episode
            grade_score = self._compute_final_grade()
            self._done = True

            # Bonus reward for correct resolution
            if grade_score >= 0.8:
                self._step_reward += 0.4   # Correct resolution reward
            elif grade_score >= 0.5:
                self._step_reward += 0.2   # Partial resolution reward
            else:
                self._step_reward -= 0.2   # Penalty: irrelevant/wrong response

            return {
                "sent": True,
                "message": "Response delivered to customer. Episode complete.",
                "grade_score": grade_score,
                "steps_used": self._state.step_count,
            }

        # ---------------------------------------------------------------
        # TOOL 5: escalate_ticket
        # ---------------------------------------------------------------
        @mcp.tool
        def escalate_ticket() -> dict:
            """
            Escalate the support ticket to a human agent.
            Use ONLY when the issue is genuinely beyond automated resolution.
            Unnecessary escalation will result in a penalty.

            Returns:
                Escalation confirmation and scoring impact.
            """
            self._record_action("escalate_ticket", {}, {"escalated": True})
            self._done = True

            # Determine if escalation was warranted (e.g., after many steps)
            max_steps = SUPPORT_POLICIES["max_steps_per_episode"]
            escalation_threshold = SUPPORT_POLICIES["escalation_threshold_steps"]

            if self._state.step_count >= escalation_threshold:
                # Warranted — agent tried hard and escalated appropriately
                self._step_reward += 0.1
                return {
                    "escalated": True,
                    "verdict": "Escalation accepted — issue forwarded to human specialist.",
                    "note": "Episode ended. Partial credit awarded for investigation effort.",
                }
            else:
                # Unnecessary escalation penalty
                self._step_reward -= 0.5
                return {
                    "escalated": True,
                    "verdict": "Escalation recorded — but many self-service options remained.",
                    "note": "Episode ended. Penalty applied for premature escalation.",
                }

        # Initialize base class with our FastMCP server
        super().__init__(mcp)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task: dict[str, Any] | None = None
        self._actions_taken: list[dict[str, Any]] = []
        self._retrieved_data: dict[str, Any] = {}
        self._final_response: str = ""
        self._done: bool = False
        self._step_reward: float = 0.0
        self._total_reward: float = 0.0

    # -------------------------------------------------------------------
    # reset()
    # -------------------------------------------------------------------
    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task: str = "easy",
        **kwargs: Any,
    ) -> Observation:
        """
        Reset the environment and initialize a new support ticket episode.

        Args:
            seed: Optional random seed (unused — environment is deterministic)
            episode_id: Optional episode ID to use
            task: Difficulty level — "easy", "medium", or "hard"

        Returns:
            Initial observation containing the customer query and context
        """
        # Default to 'easy' for predictable testing in the dashboard
        if task is None or task not in TASK_REGISTRY:
            task = "easy"

        self._current_task = TASK_REGISTRY[task]
        self._actions_taken = []
        self._retrieved_data = {}
        self._final_response = ""
        self._done = False
        self._step_reward = 0.0
        self._total_reward = 0.0

        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )

        # Build the initial observation for the agent
        task_cfg = self._current_task
        customer = get_customer(task_cfg["customer_id"]) or {}

        metadata = {
            "status": "ready",
            "task_id": task_cfg["task_id"],
            "difficulty": task_cfg["difficulty"],
            "support_tier": task_cfg["support_tier"],
            "customer_query": task_cfg["customer_query"],
            "customer_id": task_cfg["customer_id"],
            "customer_name": customer.get("name", "Customer"),
            "customer_tier": customer.get("account_tier", "basic"),
            "available_tools": [
                "get_order_status(order_id)",
                "check_payment(transaction_id)",
                "search_kb(query)",
                "reply_customer(response_text)",
                "escalate_ticket()",
            ],
            "max_steps": SUPPORT_POLICIES["max_steps_per_episode"],
            "system_message": (
                "You are a customer support agent. Resolve the customer's issue "
                "by using the available tools, then reply_customer() to close the ticket. "
                "Use escalate_ticket() only if the issue is beyond your capabilities."
            ),
        }

        from openenv.core.env_server.mcp_types import CallToolObservation
        return CallToolObservation(
            done=False,
            reward=0.0,
            metadata=metadata,
            result=metadata  # Put everything in result so it's visible in the dashboard box
        )

    # -------------------------------------------------------------------
    # step()
    # -------------------------------------------------------------------
    def step(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        """Execute a step and delegate to MCPEnvironment for MCP tool routing."""
        self._state.step_count += 1
        self._step_reward = 0.0  # Reset per-step reward accumulator

        # Max steps enforcement
        if self._state.step_count >= SUPPORT_POLICIES["max_steps_per_episode"]:
            self._done = True
            from openenv.core.env_server.mcp_types import CallToolObservation
            return CallToolObservation(
                done=True,
                reward=-0.1,
                metadata={
                    "status": "timeout",
                    "message": "Maximum steps reached. Episode terminated.",
                    "total_reward": self._total_reward,
                    "steps_used": self._state.step_count,
                },
                result="Maximum steps reached. Episode terminated."
            )

        obs = super().step(action, timeout_s=timeout_s, **kwargs)

        # Accumulate reward
        self._total_reward += self._step_reward

        # Update the observation in-place to preserve 'result' and other MCP fields
        obs.done = self._done
        obs.reward = self._step_reward
        obs.metadata.update({
            "step": self._state.step_count,
            "cumulative_reward": round(self._total_reward, 3),
            "done": self._done,
        })

        return obs

    async def step_async(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        """Async step for WebSocket handler."""
        self._state.step_count += 1
        self._step_reward = 0.0
        obs = await super().step_async(action, timeout_s=timeout_s, **kwargs)
        self._total_reward += self._step_reward
        
        # Consistent with synchronous step
        obs.done = self._done
        obs.reward = self._step_reward
        return obs

    def _step_impl(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        """
        Handle non-MCP actions (required by MCPEnvironment base class).
        """
        from openenv.core.env_server.mcp_types import CallToolObservation
        return CallToolObservation(
            done=False,
            reward=-0.1,
            metadata={
                "error": (
                    f"Unknown action type: {type(action).__name__}. "
                    "Use CallToolAction with one of: get_order_status, "
                    "check_payment, search_kb, reply_customer, escalate_ticket."
                )
            },
            result=f"Error: Unknown action type {type(action).__name__}"
        )


    @property
    def state(self) -> State:
        """Return current environment state."""
        return self._state

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------
    def _record_action(
        self,
        tool: str,
        params: dict[str, Any],
        result: Any,
    ) -> None:
        """Log an action to the episode history."""
        self._actions_taken.append({
            "step": self._state.step_count,
            "tool": tool,
            "params": params,
            "result": result,
        })

    def _compute_final_grade(self) -> float:
        """Grade the completed episode using the appropriate task grader."""
        if not self._current_task:
            return 0.0

        difficulty = self._current_task["difficulty"]
        grader_fn = GRADER_REGISTRY.get(difficulty)
        if not grader_fn:
            return 0.0

        return grader_fn(
            actions_taken=self._actions_taken,
            final_response=self._final_response,
            steps_used=self._state.step_count,
            task_config=self._current_task,
        )
