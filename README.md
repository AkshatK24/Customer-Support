---
title: Customer Support Env
emoji: 🎧
colorFrom: pink
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# Customer Service Multi-Agent Environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> A production-fidelity RL environment simulating real-world customer support workflows — built for the Meta PyTorch Hackathon.

## Environment Description

This environment simulates a **three-tier customer support system** (L1/L2/L3) where AI agents interact with realistic backend services to resolve customer tickets:

- **L1 (Easy)**: Order status inquiries — simple lookup and response
- **L2 (Medium)**: Cancellation and refund workflows — multi-step eligibility verification
- **L3 (Hard)**: Payment failure investigation — cross-system diagnosis with multi-step reasoning

The environment models real-world support architectures used by companies like Amazon, Shopify, and Zendesk.

## Motivation

Customer support is one of the most common real-world AI agent applications. This environment provides a controlled benchmark for evaluating:

- **Tool usage**: agents call backend APIs rather than generating from training data
- **Multi-step reasoning**: complex issues require investigating multiple systems
- **Decision making**: when to resolve vs. escalate
- **Communication quality**: responses must be accurate and informative

## Observation Space

Each `reset()` call returns an observation with:

```json
{
  "task_id": "easy_order_status",
  "difficulty": "easy",
  "support_tier": "L1",
  "customer_query": "Hi, I placed an order...",
  "customer_id": "CUST-101",
  "customer_name": "Alex Johnson",
  "customer_tier": "premium",
  "available_tools": ["get_order_status(order_id)", "..."],
  "max_steps": 15,
  "system_message": "You are a customer support agent..."
}
```

## Action Space

Agents interact via **5 MCP tools**:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_order_status` | `order_id: str` | Retrieve order status, carrier, tracking, ETA |
| `check_payment` | `transaction_id: str` | Payment details, gateway logs, refund eligibility |
| `search_kb` | `query: str` | Search internal knowledge base (ranked articles) |
| `reply_customer` | `response_text: str` | Send response — **ends episode, triggers grading** |
| `escalate_ticket` | _(none)_ | Escalate to human — ends episode |

## Reward Function

Continuous rewards per step (not binary):

| Event | Reward |
|-------|--------|
| Retrieved relevant order data | `+0.2` |
| Retrieved relevant payment data | `+0.2` |
| Used knowledge base | `+0.1` |
| Correct resolution (grade ≥ 0.8) | `+0.4` |
| Partial resolution (grade ≥ 0.5) | `+0.2` |
| Invalid parameter / empty query | `-0.1` |
| Irrelevant / too-short response | `-0.2` |
| Unnecessary escalation | `-0.5` |
| Repeated redundant tool call | `-0.1` |

## Task Descriptions

### Task 1 — Easy (L1): Order Status Inquiry

**Customer query**: *"Where is my order ORD-1001? When will it arrive?"*

**Expected workflow**:
1. `get_order_status(order_id="ORD-1001")` — FedEx, in_transit, ETA 2026-03-30
2. `reply_customer(...)` — inform customer of status and delivery date

**Optimal steps**: 2 | **Grading weight**: Accuracy 70%, Efficiency 20%, Quality 10%

---

### Task 2 — Medium (L2): Refund Request

**Customer query**: *"Cancel my order ORD-1002 (paid via PayPal) and refund me. How long does it take?"*

**Expected workflow**:
1. `get_order_status(order_id="ORD-1002")` — status: processing, cancellable: True
2. `check_payment(transaction_id="TXN-5002")` — PayPal, refund_eligible: True
3. `reply_customer(...)` — confirm cancellation + refund within 24 hours

**Optimal steps**: 3 | **Grading weight**: Accuracy 70%, Efficiency 20%, Quality 10%

---

### Task 3 — Hard (L3): Payment Failure Investigation

**Customer query**: *"My payment failed but my bank shows $39.99 was charged. What happened?"*

**Expected workflow**:
1. `check_payment(transaction_id="TXN-5004")` — failed, gateway timeout, bank_debit_confirmed
2. `get_order_status(order_id="ORD-1004")` — order stuck in pending
3. `search_kb(query="payment failed gateway reversal")` — find KB-003 on gateway timeouts
4. `reply_customer(...)` — explain gateway timeout, reversal in progress, 3-5 days

**Optimal steps**: 4 | **Grading weight**: Accuracy 70%, Efficiency 20%, Quality 10%

## Setup Instructions

### Prerequisites

- Python 3.10+
- Git
- Docker (for containerized deployment)
- Hugging Face CLI (for HF Spaces deployment)

### Local Installation

```bash
# Clone the repository 
git clone <your-repo-url>
cd customer_support_env

# Install in editable mode
pip install -e .

# Or using uv (faster)
uv pip install -e .
```

### Run the Server Locally

```bash
# Using uvicorn directly
uvicorn server.app:app --host 0.0.0.0 --port 8000

# Or using uv project script
uv run server

# Verify it's running
curl http://localhost:8000/health
```

### Validate with OpenEnv CLI

```bash
openenv validate
```

## Usage Instructions

### Python Client (sync)

```python
from customer_support_env import CustomerSupportEnv

with CustomerSupportEnv(base_url="http://localhost:8000").sync() as env:
    # Reset with a specific task
    obs = env.reset(task="easy")
    print(obs.metadata["customer_query"])

    # List available tools
    tools = env.list_tools()

    # Solve the task
    order = env.call_tool("get_order_status", order_id="ORD-1001")
    result = env.call_tool("reply_customer", response_text=f"Your order is {order['status']}!")
    print(f"Grade: {result['grade_score']}")
```

### Python Client (async)

```python
import asyncio
from customer_support_env import CustomerSupportEnv

async def main():
    async with CustomerSupportEnv(base_url="http://localhost:8000") as env:
        obs = await env.reset(task="hard")
        result = await env.call_tool("check_payment", transaction_id="TXN-5004")
        print(result)

asyncio.run(main())
```

### Docker

```bash
# Build
docker build -t customer-support-env ./server

# Run
docker run -p 8000:8000 customer-support-env
```

## Baseline Scores

Run the baseline evaluation script against a live server:

To run it locally:
```bash
# Start server first
uvicorn server.app:app --port 8000 &

# Set evaluation variables
$env:HF_TOKEN="your_huggingface_write_token"
$env:MODEL_NAME="gpt-4o-mini" # or an HF function-calling model

# Run the inference harness
python inference.py
```

## Baseline Validation Scores

The internal deterministic rule-based agent (`scripts/run_baseline.py`) produces the following verified ground-truth scores representing optimal, flawless multi-step tool execution logic without hallucinations:

| Task   | Final Grade Score | Optimal Steps |
|--------|-------------------|---------------|
| EASY   | 1.000             | 2 steps       |
| MEDIUM | 0.930             | 3 steps       |
| HARD   | 0.850             | 4 steps       |
| **AVG**| **0.927**         |               |

*Scores are lower on harder tasks due to efficiency penalties (more tools needed) and tighter grading criteria.*

## Project Structure

```
customer_support_env/
├── openenv.yaml                    # Environment manifest
├── pyproject.toml                  # Dependencies
├── __init__.py                     # Client exports
├── client.py                       # MCPToolClient subclass
├── README.md
│
├── server/
│   ├── app.py                      # FastAPI server
│   ├── customer_support_environment.py  # Core MCPEnvironment
│   ├── data.py                     # Rich mock databases
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tasks/                      # Task configurations (easy/medium/hard)
│   └── graders/                    # Deterministic graders
│
├── agents/
│   └── baseline_agent.py           # Rule-based + LLM baseline agent
│
└── scripts/
    └── run_baseline.py             # Evaluation script
```

## Tags

`openenv` `customer-support` `rl-environment` `multi-agent` `tool-use`
