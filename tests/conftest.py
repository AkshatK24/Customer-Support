"""
Shared pytest fixtures for Customer Support Environment tests.

Strategy:
  - Grader/unit tests: import grader functions directly (pure functions, no Pydantic)
  - API tests: spin up a subprocess server and hit it with `requests`
"""

import subprocess
import sys
import time
import pytest
import requests

# Where the server runs during tests
TEST_PORT = 7862
TEST_SERVER_URL = f"http://localhost:{TEST_PORT}"


@pytest.fixture(scope="session")
def server():
    """
    Start a fresh server subprocess for the test session, then shut it down.
    Uses port 7862 to avoid conflicts with the dev server on 7860/7861.
    """
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "server.app:app",
            "--host", "0.0.0.0",
            "--port", str(TEST_PORT),
        ],
        cwd=str(__file__).replace("\\tests\\conftest.py", ""),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for server to start (max 10s)
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            requests.get(f"{TEST_SERVER_URL}/health", timeout=1)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.3)
    else:
        proc.kill()
        pytest.fail("Test server did not start within 10 seconds.")

    yield TEST_SERVER_URL

    proc.kill()
    proc.wait()


@pytest.fixture()
def api(server):
    """
    Resets the environment to 'easy' task before each test, then returns
    a helper dictionary with `url` and a convenience `step()` function.
    """
    requests.post(f"{server}/reset", json={"task": "easy"}, timeout=5)

    def step(tool_name: str, arguments: dict) -> dict:
        payload = {
            "action": {
                "type": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments,
            }
        }
        return requests.post(f"{server}/step", json=payload, timeout=5).json()

    return {"url": server, "step": step}
