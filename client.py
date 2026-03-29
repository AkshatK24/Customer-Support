"""
Customer Service Environment Client.

Provides MCPToolClient subclass for connecting to the running environment server.

Example (sync):
    with CustomerSupportEnv(base_url="http://localhost:8000").sync() as env:
        env.reset()
        tools = env.list_tools()
        result = env.call_tool("get_order_status", order_id="ORD-1001")
        print(result)

Example (async):
    async with CustomerSupportEnv(base_url="http://localhost:8000") as env:
        await env.reset()
        result = await env.call_tool("get_order_status", order_id="ORD-1001")
"""

from openenv.core.mcp_client import MCPToolClient


class CustomerSupportEnv(MCPToolClient):
    """
    Client for the Customer Service Multi-Agent Environment.

    Inherits all tool-calling functionality from MCPToolClient:
    - list_tools()          — discover available support actions
    - call_tool(name, **kw) — execute a support action
    - reset(**kwargs)       — start a new support ticket episode
    - step(action)          — low-level action execution

    Convenience methods mirror real support workflows:
        env.call_tool("get_order_status", order_id="ORD-1001")
        env.call_tool("check_payment", transaction_id="TXN-5001")
        env.call_tool("search_kb", query="How do I return an item?")
        env.call_tool("reply_customer", response_text="Your order is on its way!")
        env.call_tool("escalate_ticket")
    """

    pass  # MCPToolClient provides all required functionality
