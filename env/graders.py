from __future__ import annotations
from typing import Dict, Any
from env.models import EpisodeState


def _clamp(score: float) -> float:
    return round(max(0.01, min(0.99, score)), 4)


def grade_task_1(state: EpisodeState) -> Dict[str, Any]:
    orders = state.observation.orders
    total = len(orders)
    if total == 0:
        return {"score": 0.05, "breakdown": {}}
    fulfilled = [o for o in orders if o.status == "fulfilled"]
    failed = [o for o in orders if o.status == "failed"]
    fulfillment_rate = (len(fulfilled) + 0.05) / (total + 0.05)
    priority_orders = [o for o in orders if o.priority in ("critical", "high")]
    priority_fulfilled = [o for o in fulfilled if o.priority in ("critical", "high")]
    priority_score = (len(priority_fulfilled) + 0.05) / (len(priority_orders) + 0.05) if priority_orders else 0.5
    budget_score = state.budget_spent / max(state.budget_total, 1)
    budget_efficiency = max(0.05, 1.0 - budget_score * 0.5)
    raw = fulfillment_rate * 0.60 + priority_score * 0.25 + budget_efficiency * 0.15
    return {
        "score": _clamp(raw),
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
    orders = state.observation.orders
    total = len(orders)
    if total == 0:
        return {"score": 0.05, "breakdown": {}}
    fulfilled = [o for o in orders if o.status == "fulfilled"]
    fulfillment_rate = (len(fulfilled) + 0.05) / (total + 0.05)
    priority_orders = [o for o in orders if o.priority in ("critical", "high")]
    total_value = sum(o.value_usd for o in priority_orders) or 1.0
    fulfilled_value = sum(o.value_usd for o in fulfilled if o.priority in ("critical", "high"))
    priority_value_score = (fulfilled_value + 1.0) / (total_value + 1.0)
    over_budget = max(0.0, state.budget_spent - state.budget_total)
    budget_score = max(0.05, 1.0 - over_budget / max(state.budget_total, 1))
    disruption_score = _clamp(0.1 + min(0.89, state.disruptions_handled / 2.0))
    raw = fulfillment_rate * 0.40 + priority_value_score * 0.30 + budget_score * 0.20 + disruption_score * 0.10
    return {
        "score": _clamp(raw),
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
    orders = state.observation.orders
    total = len(orders)
    if total == 0:
        return {"score": 0.05, "breakdown": {}}
    fulfilled = [o for o in orders if o.status == "fulfilled"]
    failed = [o for o in orders if o.status == "failed"]
    total_value = sum(o.value_usd for o in orders) or 1.0
    fulfilled_value = sum(o.value_usd for o in fulfilled)
    value_score = (fulfilled_value + 1.0) / (total_value + 1.0)
    critical_orders = [o for o in orders if o.priority == "critical"]
    critical_fulfilled = [o for o in fulfilled if o.priority == "critical"]
    critical_failed = [o for o in failed if o.priority == "critical"]
    critical_score = (len(critical_fulfilled) + 0.05) / (len(critical_orders) + 0.05) if critical_orders else 0.5
    critical_penalty = len(critical_failed) * 0.05
    spend = max(state.budget_spent, 1.0)
    value_per_dollar = fulfilled_value / spend
    cost_efficiency = _clamp(0.05 + min(0.89, value_per_dollar / 5.0))
    triage_penalty = 0.0
    if critical_failed:
        low_fulfilled = sum(1 for o in fulfilled if o.priority == "low")
        triage_penalty = min(0.3, low_fulfilled * 0.05)
    triage_score = max(0.05, 1.0 - triage_penalty)
    raw = value_score * 0.35 + critical_score * 0.30 + cost_efficiency * 0.20 + triage_score * 0.15 - critical_penalty
    return {
        "score": _clamp(raw),
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


GRADERS = {
    "task_1_easy": grade_task_1,
    "task_2_medium": grade_task_2,
    "task_3_hard": grade_task_3,
}


def grade(task_id: str, state: EpisodeState) -> Dict[str, Any]:
    if task_id not in GRADERS:
        raise ValueError(f"No grader for task_id '{task_id}'")
    return GRADERS[task_id](state)