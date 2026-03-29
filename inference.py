"""
Inference Script for Customer Service Multi-Agent Environment
=============================================================

MANDATORY VARIABLES (provided by evaluation harness):
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Hugging Face / API key.

This script runs the baseline generic LLM agent against the three specific
customer support tasks (easy, medium, hard).
"""

import os
import json
from typing import Any, Dict

from openai import OpenAI
from openenv.core.mcp_client import MCPToolClient

# ---------------------------------------------------------------------------
# Organizer-Mandated Variables
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")  # Default if not provided
SERVER_URL = os.getenv("OPENENV_SERVER_URL", "http://localhost:8000")

MAX_ITERATIONS = 15
TEMPERATURE = 0.2
MAX_TOKENS = 500


def run_llm_agent(env: MCPToolClient, client: OpenAI, task_list: list[str]) -> Dict[str, float]:
    """
    Runs the OpenAI-compatible LLM against the environment tasks.
    
    Args:
        env: Active MCPToolClient
        client: Configured OpenAI client
        task_list: List of tasks to evaluate
    """
    scores = {}

    for task in task_list:
        print(f"\n{'='*60}\nEvaluating Task: {task.upper()}\n{'='*60}")
        
        # Reset the environment for the specific task
        obs = env.reset(task=task)
        meta = getattr(obs, "metadata", {}) or {}
        
        system_msg = meta.get("system_message", "You are a customer support agent. Resolve the issue using available tools.")
        customer_query = meta.get("customer_query", "")

        print(f"[Agent] Processing query: {customer_query[:80]}...")

        # 1. Discover tools dynamically
        tools_raw = env.list_tools()
        openai_tools = []
        for t in tools_raw:
            # Python SDK uses `input_schema` natively
            schema = getattr(t, "input_schema", {})
            props = schema.get("properties", {}) if isinstance(schema, dict) else getattr(schema, "properties", {})
            reqs = schema.get("required", []) if isinstance(schema, dict) else getattr(schema, "required", [])
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or t.name,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            p_name: {"type": "string", "description": str(p_name)}
                            for p_name in props
                        },
                        "required": list(reqs),
                    },
                },
            })

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": customer_query},
        ]

        grade_score = 0.0

        # 2. Agent Interaction Loop
        for iteration in range(MAX_ITERATIONS):
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=openai_tools if openai_tools else None,
                    tool_choice="auto" if openai_tools else None,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
            except Exception as e:
                print(f"[Error] API Call Failed: {e}")
                break

            msg = completion.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            # If the model does not attempt to use a tool, force end episode
            if not getattr(msg, "tool_calls", None):
                print("[Agent] Reached a natural response without tools. Wrapping up.")
                
                # Attempt to reply to customer as fallback
                result = env.call_tool("reply_customer", response_text=msg.content or "Ending interaction.")
                grade_score = result.get("grade_score", 0.0)
                break

            # Process tool calls
            episode_ended = False
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"  -> Calling Tool: {fn_name}({fn_args})")
                
                try:
                    tool_result = env.call_tool(fn_name, **fn_args)
                except Exception as e:
                    tool_result = {"error": f"Tool execution failed: {e}"}

                if fn_name == "reply_customer":
                    grade_score = tool_result.get("grade_score", 0.0)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": json.dumps(tool_result),
                })

                if fn_name in ("reply_customer", "escalate_ticket"):
                    episode_ended = True
                    break
            
            if episode_ended:
                print("[Agent] Episode complete.")
                break
        
        else:
            print(f"[Agent] Hit sequence limit ({MAX_ITERATIONS}). Ending task.")

        print(f"✅ Final Grade ({task.upper()}): {grade_score:.3f}")
        scores[task] = grade_score

    return scores


def main() -> None:
    print(f"Starting Inference Evaluation...")
    print(f"API_BASE_URL: {API_BASE_URL}")
    print(f"MODEL_NAME: {MODEL_NAME}")
    
    if not API_KEY:
        print("WARNING: HF_TOKEN or API_KEY is not set. API calls will fail if auth is required.")

    # Initialize OpenAI client 
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY or "dummy-key-for-local-testing")

    # Initialize connection to OpenEnv
    print(f"Connecting to environment at {SERVER_URL}...")
    try:
        with MCPToolClient(base_url=SERVER_URL).sync() as env:
            scores = run_llm_agent(
                env=env,
                client=client, 
                task_list=["easy", "medium", "hard"]
            )
            
            # Print evaluation summary
            print(f"\n{'='*60}\nINFERENCE EVALUATION RESULTS\n{'='*60}")
            total_score = 0
            for t, s in scores.items():
                print(f"  {t.upper():8s}  |  {s:.3f}")
                total_score += s

            avg = total_score / len(scores) if scores else 0
            print(f"{'-'*30}\n  AVERAGE   |  {avg:.3f}")
            print(f"{'='*60}\n")
    except Exception as e:
        print(f"\n[FATAL] Could not complete environment interaction: {e}")
        print("Please ensure the OpenEnv uvicorn server is running locally.")


if __name__ == "__main__":
    main()
