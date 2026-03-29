"""
FastAPI application for the Customer Service Environment.

Creates the HTTP/WebSocket server that exposes the environment
to OpenEnv clients over the standard API.

Usage:
    # Development:
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production (or via uv):
    uv run server
"""

try:
    from openenv.core.env_server.http_server import create_app
    from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
    from .customer_support_environment import CustomerSupportEnvironment
except ImportError:
    from openenv.core.env_server.http_server import create_app
    from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
    from server.customer_support_environment import CustomerSupportEnvironment

# Pass the class (not instance) so each WebSocket session gets a fresh env
app = create_app(
    CustomerSupportEnvironment,
    CallToolAction,
    CallToolObservation,
    env_name="customer_support_env",
)


def main() -> None:
    """Entry point for: uv run server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
