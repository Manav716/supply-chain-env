"""
Deterministic graders for each task.
Each grader receives an EpisodeState and returns a score 0.0–1.0.
All grading logic is pure functions — fully reproducible.
"""

from __future__ import annotations
from typing import Dict, Any
from env.models import EpisodeState


def grade_task_1(state: EpisodeState) -> Dict[str, Any]:
    """
    Task 1 (Easy) Grader.
    Criteria:
      - 60%: Fulfillment rate (orders fulfilled / total orders)
      - 25%: All critical/high orders fulfilled (binary bonus)
      - 15%: Budget efficiency (remaining / total)
    """
    orders = state.observation.orders
    total = len(orders)
    if total == 0:
        return {"score": 0.0, "breakdown": {}}

    fulfilled = [o for o in orders if o.status == "fulfilled"]
    failed    = [o for o in orders if o.status == "failed"]

    fulfillment_rate = len(fulfilled) / total

    # High-priority fulfilment check
    priority_orders = [o for o in orders if o.priority in ("critical", "high")]
    priority_fulfilled = [o for o in fulfilled if o.priority in ("critical", "high")]
    priority_score = (
        len(priority_fulfilled) / len(priority_orders) if priority_orders else 1.0
    )

    budget_score = state.budget_spent / max(state.budget_total, 1)
    budget_efficiency = max(0.0, 1.0 - budget_score * 0.5)  # partial reward for savings

    score = (
        fulfillment_rate    * 0.60 +
        priority_score      * 0.25 +
        budget_efficiency   * 0.15
    )
    score = round(max(0.0, min(1.0, score)), 4)

    return {
        "score": score,
        "breakdown": {
            "fulfillment_rate": round(fulfillment_rate, 4),
            "priority_score": round(priority_score, 4),
            "budget_efficiency": round(budget_efficiency, 4),
            "orders_total": total,
            "orders_fulfilled": len(fulfilled),
            "orders_failed": len(failed),
            "budget_spent": round(state.budget_spent, 2),
            "budget_total": state.budget_total,
        },
    }


def grade_task_2(state: EpisodeState) -> Dict[str, Any]:
    """
    Task 2 (Medium) Grader.
    Criteria:
      - 40%: Fulfillment rate
      - 30%: Critical + high orders fulfilled (weighted by value)
      - 20%: Budget adherence (stayed within budget without over-cancelling)
      - 10%: Disruptions handled (activated backups, found alternatives)
    """
    orders = state.observation.orders
    total = len(orders)
    if total == 0:
        return {"score": 0.0, "breakdown": {}}

    fulfilled = [o for o in orders if o.status == "fulfilled"]
    fulfillment_rate = len(fulfilled) / total

    # Value-weighted priority score
    priority_orders = [o for o in orders if o.priority in ("critical", "high")]
    total_value = sum(o.value_usd for o in priority_orders) or 1.0
    fulfilled_value = sum(
        o.value_usd for o in fulfilled if o.priority in ("critical", "high")
    )
    priority_value_score = fulfilled_value / total_value

    # Budget: penalise if over budget, reward staying within
    over_budget = max(0.0, state.budget_spent - state.budget_total)
    budget_score = max(0.0, 1.0 - over_budget / max(state.budget_total, 1))

    # Disruption handling: proportional to disruptions resolved
    disruption_score = min(1.0, state.disruptions_handled / 2.0)

    score = (
        fulfillment_rate       * 0.40 +
        priority_value_score   * 0.30 +
        budget_score           * 0.20 +
        disruption_score       * 0.10
    )
    score = round(max(0.0, min(1.0, score)), 4)

    return {
        "score": score,
        "breakdown": {
            "fulfillment_rate": round(fulfillment_rate, 4),
            "priority_value_score": round(priority_value_score, 4),
            "budget_score": round(budget_score, 4),
            "disruption_score": round(disruption_score, 4),
            "orders_total": total,
            "orders_fulfilled": len(fulfilled),
            "budget_spent": round(state.budget_spent, 2),
            "disruptions_handled": state.disruptions_handled,
        },
    }


def grade_task_3(state: EpisodeState) -> Dict[str, Any]:
    """
    Task 3 (Hard) Grader.
    Criteria:
      - 35%: Value-weighted fulfillment (high-value orders matter more)
      - 30%: Critical order survival rate (VIP customers — heavy penalty per failure)
      - 20%: Cost efficiency (minimise spend relative to value delivered)
      - 15%: Triage quality (correctly prioritised — fulfilled high > medium > low)
    """
    orders = state.observation.orders
    total = len(orders)
    if total == 0:
        return {"score": 0.0, "breakdown": {}}

    fulfilled = [o for o in orders if o.status == "fulfilled"]
    failed    = [o for o in orders if o.status == "failed"]

    # Value-weighted fulfillment
    total_value    = sum(o.value_usd for o in orders) or 1.0
    fulfilled_value = sum(o.value_usd for o in fulfilled)
    value_score    = fulfilled_value / total_value

    # Critical order survival — each failed critical is heavily penalised
    critical_orders    = [o for o in orders if o.priority == "critical"]
    critical_fulfilled = [o for o in fulfilled if o.priority == "critical"]
    critical_failed    = [o for o in failed if o.priority == "critical"]
    critical_score = (
        len(critical_fulfilled) / len(critical_orders) if critical_orders else 1.0
    )
    # Extra penalty per failed critical
    critical_penalty = len(critical_failed) * 0.05

    # Cost efficiency: value delivered per dollar spent
    spend = max(state.budget_spent, 1.0)
    value_per_dollar = fulfilled_value / spend
    # Normalise: assume 5.0 value/dollar is excellent
    cost_efficiency = min(1.0, value_per_dollar / 5.0)

    # Triage quality: did agent fulfil high-priority before low?
    priority_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    fulfilled_ranks = sorted([priority_rank.get(o.priority, 0) for o in fulfilled], reverse=True)
    failed_ranks    = sorted([priority_rank.get(o.priority, 0) for o in failed], reverse=True)
    # Penalty if any low-priority order fulfilled while critical failed
    triage_penalty = 0.0
    if critical_failed:
        low_fulfilled = sum(1 for o in fulfilled if o.priority == "low")
        triage_penalty = min(0.3, low_fulfilled * 0.05)
    triage_score = max(0.0, 1.0 - triage_penalty)

    score = (
        value_score      * 0.35 +
        critical_score   * 0.30 +
        cost_efficiency  * 0.20 +
        triage_score     * 0.15
    ) - critical_penalty

    score = round(max(0.0, min(1.0, score)), 4)

    return {
        "score": score,
        "breakdown": {
            "value_score": round(value_score, 4),
            "critical_score": round(critical_score, 4),
            "cost_efficiency": round(cost_efficiency, 4),
            "triage_score": round(triage_score, 4),
            "critical_penalty": round(critical_penalty, 4),
            "orders_total": total,
            "orders_fulfilled": len(fulfilled),
            "critical_fulfilled": len(critical_fulfilled),
            "critical_failed": len(critical_failed),
            "value_fulfilled_usd": round(fulfilled_value, 2),
            "budget_spent": round(state.budget_spent, 2),
        },
    }


# ---------------------------------------------------------------------------
# Grader registry
# ---------------------------------------------------------------------------

GRADERS = {
    "task_1_easy":   grade_task_1,
    "task_2_medium": grade_task_2,
    "task_3_hard":   grade_task_3,
}


def grade(task_id: str, state: EpisodeState) -> Dict[str, Any]:
    if task_id not in GRADERS:
        raise ValueError(f"No grader for task_id '{task_id}'")
    return GRADERS[task_id](state)
