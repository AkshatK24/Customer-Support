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

class LenientCallToolAction(CallToolAction):
    """
    A more flexible version of CallToolAction for the Web UI.
    - Accepts both 'call' and 'call_tool' types.
    - Automatically parses JSON string arguments into dictionaries.
    """
    type: Literal["call", "call_tool"] = "call_tool"
    arguments: Dict[str, Any]

    @field_validator("arguments", mode="before")
    @classmethod
    def parse_json_string(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

    @field_validator("type", mode="before")
    @classmethod
    def handle_call_type(cls, v: Any) -> Any:
        if v == "call":
            return "call_tool"
        return v

# Pass the class (not instance) so each WebSocket session gets a fresh env
app = create_app(
    CustomerSupportEnvironment,
    LenientCallToolAction,
    CallToolObservation,
    env_name="customer_support_env",
)


# The built-in OpenEnv dashboard will be served at the root (/) if available.


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
