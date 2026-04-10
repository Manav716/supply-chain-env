"""
inference.py — Baseline inference script for Supply Chain Disruption Management.

Uses OpenAI client to run an LLM agent against all 3 tasks.
Reads credentials from environment variables:
  API_BASE_URL  — LLM API endpoint
  MODEL_NAME    — model identifier
  HF_TOKEN      — Hugging Face / API key (used as OpenAI API key)

Emits structured stdout logs in [START] / [STEP] / [END] format.
Runtime target: < 20 minutes total.
Runs on: 2 vCPU / 8 GB RAM.
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration — read from environment
# ---------------------------------------------------------------------------

API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME:   str = os.environ.get("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN:     str = os.environ.get("HF_TOKEN",     os.environ.get("OPENAI_API_KEY", ""))

# The supply-chain environment API base (FastAPI server)
ENV_BASE_URL: str = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

TASK_IDS: List[str] = ["task_1_easy", "task_2_medium", "task_3_hard"]

MAX_STEPS_PER_TASK = 25   # hard cap per task regardless of env setting
REQUEST_TIMEOUT    = 30   # seconds per HTTP call

# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------

client = OpenAI(
    api_key=HF_TOKEN or "sk-placeholder",
    base_url=API_BASE_URL,
)

# ---------------------------------------------------------------------------
# Environment HTTP helpers
# ---------------------------------------------------------------------------

def env_reset(task_id: str) -> Dict[str, Any]:
    r = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_id},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def env_step(action: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(
        f"{ENV_BASE_URL}/step",
        json={"action": action},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def env_state() -> Dict[str, Any]:
    r = requests.get(f"{ENV_BASE_URL}/state", timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def env_grade() -> Dict[str, Any]:
    r = requests.post(f"{ENV_BASE_URL}/grade", timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# LLM agent logic
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert supply chain coordinator AI agent.
You manage supply chain disruptions by taking structured actions.

At each step you receive a JSON observation describing:
- Active orders (id, product, quantity, priority, deadline_days, status)
- Suppliers (id, name, status, cost_per_unit, lead_time_days)
- Active disruptions
- Remaining budget

You must respond with a single JSON action object. Valid action_types:
- "reroute_order":          {"action_type": "reroute_order", "order_id": "ORD-XXX", "supplier_id": "SUP-X", "reason": "..."}
- "split_order":            {"action_type": "split_order", "order_id": "ORD-XXX", "split_quantities": {"SUP-X": qty1, "SUP-Y": qty2}, "reason": "..."}
- "upgrade_shipping":       {"action_type": "upgrade_shipping", "order_id": "ORD-XXX", "reason": "..."}
- "hold_order":             {"action_type": "hold_order", "order_id": "ORD-XXX", "reason": "..."}
- "cancel_order":           {"action_type": "cancel_order", "order_id": "ORD-XXX", "reason": "..."}
- "activate_backup_supplier": {"action_type": "activate_backup_supplier", "supplier_id": "SUP-X", "reason": "..."}
- "noop":                   {"action_type": "noop", "reason": "..."}

Strategy guidelines:
1. NEVER assign to a disrupted supplier.
2. Prioritise critical > high > medium > low orders.
3. Track budget — cost = supplier.cost_per_unit × order.quantity.
4. Prefer suppliers with shorter lead_time_days for urgent orders.
5. Activate backup suppliers before rerouting to them.
6. Only cancel as last resort — heavy penalty for critical cancellations.

Respond ONLY with valid JSON. No prose, no markdown, no explanation outside the JSON."""


def build_user_prompt(obs: Dict[str, Any], step_num: int) -> str:
    return f"""Step {step_num} — Current observation:

{json.dumps(obs, indent=2)}

What is your next action? Respond with a single JSON action object."""


def get_llm_action(obs: Dict[str, Any], step_num: int, conversation_history: List[Dict]) -> Dict[str, Any]:
    """Call LLM, parse action JSON, return action dict."""
    user_msg = build_user_prompt(obs, step_num)
    conversation_history.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
            temperature=0.2,
            max_tokens=512,
            timeout=60,
        )
        content = response.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": content})

        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        action = json.loads(content)
        return action

    except json.JSONDecodeError:
        return {"action_type": "noop", "reason": "LLM returned invalid JSON — defaulting to noop"}
    except Exception as e:
        err = str(e)
        if "429" in err:
            time.sleep(15)
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
                    temperature=0.2,
                    max_tokens=512,
                    timeout=60,
                )
                content = response.choices[0].message.content.strip()
                conversation_history.append({"role": "assistant", "content": content})
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content.strip())
            except Exception:
                pass
        return {"action_type": "noop", "reason": f"LLM error: {err[:100]}"}


# ---------------------------------------------------------------------------
# Single task runner
# ---------------------------------------------------------------------------

def run_task(task_id: str) -> Dict[str, Any]:
    """Run one full episode and return results."""

    # ── [START] ────────────────────────────────────────────────────────────
    start_time = time.time()
    print(json.dumps({
        "event":   "[START]",
        "task_id": task_id,
        "model":   MODEL_NAME,
        "timestamp": start_time,
    }))
    sys.stdout.flush()

    # Reset environment
    obs = env_reset(task_id)
    conversation_history: List[Dict] = []
    cumulative_reward = 0.0
    step_num = 0

    while step_num < MAX_STEPS_PER_TASK:
        step_num += 1
        step_start = time.time()

        # Get LLM action
        action = get_llm_action(obs, step_num, conversation_history)

        # Take step in environment
        try:
            result = env_step(action)
        except Exception as e:
            print(json.dumps({
                "event":   "[STEP]",
                "task_id": task_id,
                "step":    step_num,
                "action":  action,
                "error":   str(e),
                "reward":  0.0,
                "cumulative_reward": cumulative_reward,
                "done":    False,
            }))
            sys.stdout.flush()
            break

        reward_val      = result["reward"]["step_reward"]
        cumulative_reward += reward_val
        done            = result["done"]
        new_obs         = result["observation"]
        info            = result.get("info", {})

        # ── [STEP] ─────────────────────────────────────────────────────────
        print(json.dumps({
            "event":              "[STEP]",
            "task_id":            task_id,
            "step":               step_num,
            "action_type":        action.get("action_type"),
            "order_id":           action.get("order_id"),
            "supplier_id":        action.get("supplier_id"),
            "reason":             action.get("reason", "")[:120],
            "step_reward":        round(reward_val, 4),
            "cumulative_reward":  round(cumulative_reward, 4),
            "fulfillment_score":  result["reward"]["fulfillment_score"],
            "cost_score":         result["reward"]["cost_score"],
            "budget_remaining":   new_obs["budget_remaining"],
            "done":               done,
            "step_time_s":        round(time.time() - step_start, 2),
        }))
        sys.stdout.flush()

        time.sleep(3)
        obs = new_obs
        if done:
            break

    # Grade episode
    try:
        grade_result = env_grade()
        final_score  = grade_result["score"]
        breakdown    = grade_result["breakdown"]
    except Exception as e:
        final_score = 0.0
        breakdown   = {"error": str(e)}

    elapsed = round(time.time() - start_time, 2)

    # ── [END] ──────────────────────────────────────────────────────────────
    print(json.dumps({
        "event":             "[END]",
        "task_id":           task_id,
        "model":             MODEL_NAME,
        "total_steps":       step_num,
        "final_score":       final_score,
        "cumulative_reward": round(cumulative_reward, 4),
        "breakdown":         breakdown,
        "elapsed_seconds":   elapsed,
    }))
    sys.stdout.flush()

    return {
        "task_id":     task_id,
        "score":       final_score,
        "steps":       step_num,
        "reward":      round(cumulative_reward, 4),
        "elapsed":     elapsed,
        "breakdown":   breakdown,
    }


# ---------------------------------------------------------------------------
# Main — run all tasks and print summary
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Supply Chain Disruption Management — Baseline Inference")
    print(f"Model:     {MODEL_NAME}")
    print(f"API Base:  {API_BASE_URL}")
    print(f"Env URL:   {ENV_BASE_URL}")
    print("=" * 60)
    sys.stdout.flush()

    results = []
    total_start = time.time()

    for task_id in TASK_IDS:
        try:
            result = run_task(task_id)
            results.append(result)
        except Exception as e:
            print(json.dumps({
                "event":   "[END]",
                "task_id": task_id,
                "error":   str(e),
                "final_score": 0.0,
            }))
            sys.stdout.flush()
            results.append({"task_id": task_id, "score": 0.0, "error": str(e)})

        # Brief pause between tasks
        time.sleep(1)

    total_elapsed = round(time.time() - total_start, 2)

    # ── Final Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("BASELINE RESULTS SUMMARY")
    print("=" * 60)
    for r in results:
        score_str = f"{r['score']:.4f}" if isinstance(r.get('score'), float) else "ERROR"
        print(f"  {r['task_id']:25s}  score={score_str}  steps={r.get('steps','?'):>3}  "
              f"reward={r.get('reward', '?')}")
    avg_score = sum(r.get("score", 0.0) for r in results) / max(len(results), 1)
    print(f"\n  Average score:  {avg_score:.4f}")
    print(f"  Total time:     {total_elapsed}s")
    print("=" * 60)

    # Machine-readable summary
    print(json.dumps({
        "event":       "SUMMARY",
        "results":     results,
        "avg_score":   round(avg_score, 4),
        "total_time":  total_elapsed,
        "model":       MODEL_NAME,
    }))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
