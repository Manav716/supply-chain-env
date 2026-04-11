"""
inference.py — Baseline inference script for Supply Chain Disruption Management.
Meta PyTorch Hackathon x Scaler School of Technology — Round 1.

Uses OpenAI-compatible client to run an LLM agent against all 3 tasks.
Reads credentials from environment variables:
  API_BASE_URL  — LLM API endpoint (default: HuggingFace Inference API)
  MODEL_NAME    — model identifier
  HF_TOKEN      — HuggingFace / API key (used as bearer token)
  ENV_BASE_URL  — supply-chain environment base URL

Output format (each line starts with its tag — required by validator):
  [START] {"task": "...", "model": "...", ...}
  [STEP]  {"task": "...", "step": N, "reward": X, "done": false, ...}
  [END]   {"task": "...", "score": X, "steps": N, ...}

Runtime target: < 20 minutes total.
Runs on: 2 vCPU / 8 GB RAM.
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Dict, List

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration — read from environment
# ---------------------------------------------------------------------------

API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME:   str = os.environ.get("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN:     str = os.environ.get("HF_TOKEN",     os.environ.get("OPENAI_API_KEY", ""))
ENV_BASE_URL: str = os.environ.get("ENV_BASE_URL", "http://localhost:7860")

TASK_IDS:          List[str] = ["task_1_easy", "task_2_medium", "task_3_hard"]
MAX_STEPS_PER_TASK: int      = 25   # hard cap — actual task limits are 15/20/25
REQUEST_TIMEOUT:    int      = 30   # seconds per HTTP call to env
LLM_TIMEOUT:        int      = 60   # seconds per LLM call
STEP_SLEEP:         float    = 1.0  # rate-limit pause between steps


# ---------------------------------------------------------------------------
# Structured log helpers  ← lines MUST start with the tag for the validator
# ---------------------------------------------------------------------------

def log_start(task_id: str, timestamp: float) -> None:
    print("[START] " + json.dumps({
        "task":      task_id,
        "task_id":   task_id,
        "model":     MODEL_NAME,
        "timestamp": timestamp,
    }), flush=True)


def log_step(
    task_id: str,
    step_num: int,
    action: Dict[str, Any],
    reward_val: float,
    cumulative_reward: float,
    fulfillment_score: float,
    cost_score: float,
    budget_remaining: float | None,
    done: bool,
    step_time_s: float,
) -> None:
    print("[STEP] " + json.dumps({
        "task":               task_id,
        "task_id":            task_id,
        "step":               step_num,
        "action":             action.get("action_type"),
        "action_type":        action.get("action_type"),
        "order_id":           action.get("order_id"),
        "supplier_id":        action.get("supplier_id"),
        "reason":             str(action.get("reason", ""))[:120],
        "reward":             round(reward_val, 4),
        "step_reward":        round(reward_val, 4),
        "cumulative_reward":  round(cumulative_reward, 4),
        "fulfillment_score":  fulfillment_score,
        "cost_score":         cost_score,
        "budget_remaining":   budget_remaining,
        "done":               done,
        "step_time_s":        round(step_time_s, 2),
    }), flush=True)


def log_end(
    task_id: str,
    step_num: int,
    final_score: float,
    cumulative_reward: float,
    breakdown: Dict[str, Any],
    elapsed: float,
) -> None:
    print("[END] " + json.dumps({
        "task":              task_id,
        "task_id":           task_id,
        "model":             MODEL_NAME,
        "steps":             step_num,
        "total_steps":       step_num,
        "score":             final_score,
        "final_score":       final_score,
        "cumulative_reward": round(cumulative_reward, 4),
        "breakdown":         breakdown,
        "elapsed_seconds":   elapsed,
    }), flush=True)


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


def env_grade() -> Dict[str, Any]:
    r = requests.post(f"{ENV_BASE_URL}/grade", timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# LLM agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert supply chain coordinator AI agent.
You manage supply chain disruptions by taking structured actions.

At each step you receive a JSON observation describing:
- Active orders (id, product, quantity, priority, deadline_days, status)
- Suppliers (id, name, status, cost_per_unit, lead_time_days)
- Active disruptions
- Remaining budget

You must respond with a single JSON action object. Valid action_types:
- "reroute_order":            {"action_type": "reroute_order", "order_id": "ORD-XXX", "supplier_id": "SUP-X", "reason": "..."}
- "split_order":              {"action_type": "split_order", "order_id": "ORD-XXX", "split_quantities": {"SUP-X": qty1, "SUP-Y": qty2}, "reason": "..."}
- "upgrade_shipping":         {"action_type": "upgrade_shipping", "order_id": "ORD-XXX", "reason": "..."}
- "hold_order":               {"action_type": "hold_order", "order_id": "ORD-XXX", "reason": "..."}
- "cancel_order":             {"action_type": "cancel_order", "order_id": "ORD-XXX", "reason": "..."}
- "activate_backup_supplier": {"action_type": "activate_backup_supplier", "supplier_id": "SUP-X", "reason": "..."}
- "noop":                     {"action_type": "noop", "reason": "..."}

Strategy guidelines:
1. NEVER assign orders to a disrupted supplier.
2. Prioritise critical > high > medium > low orders.
3. Track budget — cost = supplier.cost_per_unit × order.quantity.
4. Prefer suppliers with shorter lead_time_days for urgent orders.
5. Activate backup suppliers before rerouting to them.
6. Only cancel as a last resort — heavy penalty for critical cancellations.

Respond ONLY with valid JSON. No prose, no markdown fences, no explanation."""


def _parse_llm_response(content: str) -> Dict[str, Any]:
    """Strip markdown fences and parse JSON from LLM response."""
    content = content.strip()
    if content.startswith("```"):
        parts = content.split("```")
        content = parts[1] if len(parts) > 1 else content
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def get_llm_action(
    obs: Dict[str, Any],
    step_num: int,
    conversation_history: List[Dict],
) -> Dict[str, Any]:
    """Call LLM, parse JSON action, return action dict. Falls back to noop on error."""
    user_msg = (
        f"Step {step_num} — Current observation:\n\n"
        f"{json.dumps(obs, indent=2)}\n\n"
        "What is your next action? Respond with a single JSON action object."
    )
    conversation_history.append({"role": "user", "content": user_msg})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.2,
                max_tokens=512,
                timeout=LLM_TIMEOUT,
            )
            content = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": content})
            return _parse_llm_response(content)

        except json.JSONDecodeError:
            return {"action_type": "noop", "reason": "LLM returned invalid JSON"}
        except Exception as e:
            err = str(e)
            if attempt == 0 and "429" in err:
                time.sleep(15)
                continue
            return {"action_type": "noop", "reason": f"LLM error: {err[:100]}"}

    return {"action_type": "noop", "reason": "LLM failed after retries"}


client = OpenAI(
    api_key=HF_TOKEN or "sk-placeholder",
    base_url=API_BASE_URL,
)


# ---------------------------------------------------------------------------
# Single task runner
# ---------------------------------------------------------------------------

def run_task(task_id: str) -> Dict[str, Any]:
    """Run one full episode; emit [START] / [STEP]... / [END] to stdout."""

    start_time = time.time()
    log_start(task_id, start_time)

    obs = env_reset(task_id)
    conversation_history: List[Dict] = []
    cumulative_reward = 0.0
    step_num = 0

    while step_num < MAX_STEPS_PER_TASK:
        step_num += 1
        step_start = time.time()

        action = get_llm_action(obs, step_num, conversation_history)

        try:
            result = env_step(action)
        except Exception as e:
            # Environment call failed — log the step and abort this task
            log_step(
                task_id=task_id,
                step_num=step_num,
                action=action,
                reward_val=0.0,
                cumulative_reward=cumulative_reward,
                fulfillment_score=0.0,
                cost_score=0.0,
                budget_remaining=None,
                done=True,
                step_time_s=time.time() - step_start,
            )
            break

        reward_val        = result["reward"]["step_reward"]
        cumulative_reward += reward_val
        done              = result["done"]
        new_obs           = result["observation"]

        log_step(
            task_id=task_id,
            step_num=step_num,
            action=action,
            reward_val=reward_val,
            cumulative_reward=cumulative_reward,
            fulfillment_score=result["reward"]["fulfillment_score"],
            cost_score=result["reward"]["cost_score"],
            budget_remaining=new_obs["budget_remaining"],
            done=done,
            step_time_s=time.time() - step_start,
        )

        time.sleep(STEP_SLEEP)
        obs = new_obs
        if done:
            break

    # Grade the completed episode
    try:
        grade_result = env_grade()
        final_score  = grade_result["score"]
        breakdown    = grade_result["breakdown"]
    except Exception as e:
        final_score = 0.0
        breakdown   = {"error": str(e)}

    elapsed = round(time.time() - start_time, 2)
    log_end(task_id, step_num, final_score, cumulative_reward, breakdown, elapsed)

    return {
        "task_id":   task_id,
        "score":     final_score,
        "steps":     step_num,
        "reward":    round(cumulative_reward, 4),
        "elapsed":   elapsed,
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Main — run all tasks
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60, flush=True)
    print("Supply Chain Disruption Management — Baseline Inference", flush=True)
    print(f"Model:    {MODEL_NAME}", flush=True)
    print(f"API Base: {API_BASE_URL}", flush=True)
    print(f"Env URL:  {ENV_BASE_URL}", flush=True)
    print("=" * 60, flush=True)

    results   = []
    total_start = time.time()

    for task_id in TASK_IDS:
        try:
            result = run_task(task_id)
            results.append(result)
        except Exception as e:
            log_end(
                task_id=task_id,
                step_num=0,
                final_score=0.0,
                cumulative_reward=0.0,
                breakdown={"error": str(e)},
                elapsed=0.0,
            )
            results.append({"task_id": task_id, "score": 0.0, "error": str(e)})

        time.sleep(1)

    total_elapsed = round(time.time() - total_start, 2)
    avg_score     = sum(r.get("score", 0.0) for r in results) / max(len(results), 1)

    # Human-readable summary
    print("\n" + "=" * 60, flush=True)
    print("RESULTS SUMMARY", flush=True)
    print("=" * 60, flush=True)
    for r in results:
        score_str = f"{r['score']:.4f}" if isinstance(r.get("score"), float) else "ERROR"
        print(
            f"  {r['task_id']:25s}  score={score_str}"
            f"  steps={r.get('steps', '?'):>3}"
            f"  reward={r.get('reward', '?')}",
            flush=True,
        )
    print(f"\n  Average score : {avg_score:.4f}", flush=True)
    print(f"  Total time    : {total_elapsed}s", flush=True)
    print("=" * 60, flush=True)

    # Machine-readable summary line
    print("[SUMMARY] " + json.dumps({
        "avg_score":  round(avg_score, 4),
        "total_time": total_elapsed,
        "model":      MODEL_NAME,
        "results":    results,
    }), flush=True)


if __name__ == "__main__":
    main()
