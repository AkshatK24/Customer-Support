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

import os
# Enable the built-in Gradio dashboard/explorer
os.environ["ENABLE_WEB_INTERFACE"] = "true"

try:

    from openenv.core.env_server.http_server import create_app
    from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
    from .customer_support_environment import CustomerSupportEnvironment
except ImportError:
    from openenv.core.env_server.http_server import create_app
    from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
    from server.customer_support_environment import CustomerSupportEnvironment

from pydantic import field_validator
import json
from typing import Any, Dict, Literal

from openenv.core.env_server.serialization import _MCP_ACTION_TYPES

class LenientCallToolAction(CallToolAction):
    """
    A more flexible version of CallToolAction for the Web UI.
    - Automatically parses JSON string arguments into dictionaries.
    - Ignores extra fields like 'type'.
    """
    model_config = {"extra": "ignore"}

    @field_validator("arguments", mode="before")
    @classmethod
    def parse_json_string(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

# Inject into MCP action types so that deserialize_action can correctly fail-over
# to list_tools without validating against LenientCallToolAction falsely.
_MCP_ACTION_TYPES["call_tool"] = LenientCallToolAction


# Pass the class (not instance) so each WebSocket session gets a fresh env
app = create_app(
    CustomerSupportEnvironment,
    LenientCallToolAction,
    CallToolObservation,
    env_name="customer_support_env",
)


# The built-in OpenEnv dashboard will be served at the root (/) if available.
# However, we explicitly define a root handler to ensure Hugging Face
# health checks (which send HEAD /) receive a 200 OK instead of a 405.
@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
def root():
    """Hugging Face health check endpoint."""
    return {"message": "OpenEnv Customer Support environment is running", "dashboard": "/"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# The built-in dashboard will now be visible at the root.



def main() -> None:
    """Entry point for: uv run server"""
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
