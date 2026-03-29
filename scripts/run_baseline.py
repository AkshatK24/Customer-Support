"""
Baseline evaluation script.

Runs the rule-based baseline agent against all 3 tasks and prints
a summary score table. This produces the baseline scores for the
hackathon submission.

Usage:
    python scripts/run_baseline.py
    python scripts/run_baseline.py --url http://localhost:8000
    python scripts/run_baseline.py --llm   # uses OpenAI API if key is set
"""

from __future__ import annotations

import sys
import os
import argparse
import time

# Add parent dir so we can import the agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.baseline_agent import run_task


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run baseline agent on all Customer Support Env tasks"
    )
    parser.add_argument("--url", default="http://localhost:8000", help="Environment server URL")
    parser.add_argument("--llm", action="store_true", help="Use LLM agent (requires OPENAI_API_KEY)")
    args = parser.parse_args()

    tasks = ["easy", "medium", "hard"]
    scores: dict[str, float] = {}

    print("=" * 60)
    print("Customer Service OpenEnv — Baseline Evaluation")
    print("=" * 60)
    print(f"Server: {args.url}")
    print(f"Mode:   {'LLM (OpenAI)' if args.llm else 'Rule-Based (Deterministic)'}")
    print()

    for task in tasks:
        try:
            score = run_task(task, base_url=args.url, use_llm=args.llm)
            scores[task] = score
        except Exception as exc:
            print(f"\n  ❌ Task '{task}' failed: {exc}")
            scores[task] = 0.0
        time.sleep(0.3)  # small delay between tasks

    # Print summary
    print()
    print("=" * 60)
    print("BASELINE RESULTS")
    print("=" * 60)
    for task, score in scores.items():
        bar_len = int(score * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        label = task.upper()
        print(f"  {label:8s}  {score:.3f}  |{bar}|")

    avg = sum(scores.values()) / len(scores) if scores else 0.0
    print(f"\n  {'AVERAGE':8s}  {avg:.3f}")
    print("=" * 60)
    print("\nBaseline evaluation complete.")
    print("These scores serve as the ground-truth baseline for the hackathon submission.")


if __name__ == "__main__":
    main()
