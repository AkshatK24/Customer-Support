"""
Customer Service Multi-Agent Environment for OpenEnv.

Simulates real-world customer support workflows (L1/L2/L3) where AI agents
interact with backend APIs to resolve customer tickets.

Exported for use as a client package:
    from customer_support_env import CustomerSupportEnv, CallToolAction, ListToolsAction
"""

from openenv.core.env_server.mcp_types import CallToolAction, ListToolsAction

from .client import CustomerSupportEnv

__all__ = ["CustomerSupportEnv", "CallToolAction", "ListToolsAction"]
