"""
Supply Chain Simulation Engine.
Manages state: suppliers, orders, routes, disruptions, budget.
"""

from __future__ import annotations
import copy
import random
from typing import Any, Dict, List, Optional, Tuple

from env.models import (
    Action, Disruption, EpisodeState, Observation,
    Order, Reward, Route, Supplier,
)


# ---------------------------------------------------------------------------
# Simulation Engine
# ---------------------------------------------------------------------------

class SupplyChainSimulation:
    """
    Core stateful simulation.  Consumed by the task layer which injects
    the scenario (suppliers, orders, disruptions) before reset().
    """

    def __init__(self, scenario: Dict[str, Any], task_id: str, max_steps: int = 20):
        self.scenario = copy.deepcopy(scenario)
        self.task_id = task_id
        self.max_steps = max_steps
        self._reset_state()

    # ------------------------------------------------------------------
    # Public OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Observation:
        self._reset_state()
        return self._build_observation("Episode started. Assess disruptions and reroute orders.")

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        if self.done:
            obs = self._build_observation("Episode already done. Call reset().")
            reward = self._build_reward(0.0, "Episode already finished.")
            return obs, reward, True, {}

        self.step_count += 1
        step_reward, penalty, msg = self._apply_action(action)

        # Advance simulation clock — disruptions may resolve/appear
        self._tick()

        done = self._check_done()
        if done:
            self.done = True

        cumulative = sum(self.reward_history) + step_reward
        self.reward_history.append(step_reward)
        self.cumulative_reward = cumulative

        obs = self._build_observation(msg)
        reward = self._build_reward(step_reward, msg, penalty, done)
        info = {
            "step": self.step_count,
            "action_applied": action.action_type,
            "orders_fulfilled": self._count_status("fulfilled"),
            "orders_failed": self._count_status("failed"),
            "budget_remaining": self.budget_remaining,
        }
        return obs, reward, done, info

    def state(self) -> EpisodeState:
        total = len(self.orders)
        fulfilled = self._count_status("fulfilled")
        failed = self._count_status("failed")
        pending = self._count_status("pending") + self._count_status("assigned")
        score = self._compute_final_score()
        return EpisodeState(
            task_id=self.task_id,
            step=self.step_count,
            max_steps=self.max_steps,
            done=self.done,
            observation=self._build_observation(""),
            total_reward=self.cumulative_reward,
            orders_fulfilled=fulfilled,
            orders_failed=failed,
            orders_pending=pending,
            budget_spent=self.budget_total - self.budget_remaining,
            budget_total=self.budget_total,
            disruptions_handled=self.disruptions_handled,
            score=score,
        )

    # ------------------------------------------------------------------
    # Internal state management
    # ------------------------------------------------------------------

    def _reset_state(self):
        sc = self.scenario
        self.suppliers: List[Supplier] = [Supplier(**s) for s in sc["suppliers"]]
        self.orders: List[Order] = [Order(**o) for o in sc["orders"]]
        self.routes: List[Route] = [Route(**r) for r in sc["routes"]]
        self.disruptions: List[Disruption] = [Disruption(**d) for d in sc["disruptions"]]
        self.budget_total: float = sc["budget"]
        self.budget_remaining: float = sc["budget"]
        self.step_count: int = 0
        self.days_elapsed: int = 0
        self.done: bool = False
        self.reward_history: List[float] = []
        self.cumulative_reward: float = 0.0
        self.disruptions_handled: int = 0
        self._disruption_remaining: Dict[str, int] = {
            d["id"]: d["duration_days"] for d in sc["disruptions"]
        }

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _apply_action(self, action: Action) -> Tuple[float, float, str]:
        """Dispatch action and return (step_reward, penalty, message)."""
        t = action.action_type

        if t == "noop":
            return self._handle_noop()
        elif t == "reroute_order":
            return self._handle_reroute(action)
        elif t == "split_order":
            return self._handle_split(action)
        elif t == "upgrade_shipping":
            return self._handle_upgrade(action)
        elif t == "hold_order":
            return self._handle_hold(action)
        elif t == "cancel_order":
            return self._handle_cancel(action)
        elif t == "activate_backup_supplier":
            return self._handle_activate_backup(action)
        else:
            return 0.0, -0.05, f"Unknown action type: {t}"

    def _handle_noop(self) -> Tuple[float, float, str]:
        pending = self._count_status("pending")
        penalty = -0.02 * pending   # penalise inaction when orders wait
        return -0.01 + penalty, abs(penalty), "No action taken."

    def _handle_reroute(self, action: Action) -> Tuple[float, float, str]:
        order = self._find_order(action.order_id)
        if order is None:
            return 0.0, -0.05, f"Order {action.order_id} not found."

        supplier = self._find_supplier(action.supplier_id)
        if supplier is None:
            return 0.0, -0.05, f"Supplier {action.supplier_id} not found."

        if supplier.status == "disrupted":
            return 0.0, -0.1, f"Supplier {supplier.id} is disrupted — cannot assign."

        # Cost check
        cost = supplier.cost_per_unit * order.quantity
        if cost > self.budget_remaining:
            return 0.0, -0.1, "Insufficient budget for reroute."

        # Apply
        self.budget_remaining -= cost
        order.assigned_supplier = supplier.id
        order.status = "assigned"

        # Reward: partial progress + priority bonus
        base = 0.15
        priority_bonus = {"low": 0.0, "medium": 0.02, "high": 0.05, "critical": 0.1}
        reward = base + priority_bonus.get(order.priority, 0.0)

        # Deadline bonus — reward acting early
        if order.deadline_days > supplier.lead_time_days + self.days_elapsed:
            reward += 0.05

        return reward, 0.0, f"Order {order.id} rerouted to {supplier.name}."

    def _handle_split(self, action: Action) -> Tuple[float, float, str]:
        order = self._find_order(action.order_id)
        if order is None or not action.split_quantities:
            return 0.0, -0.05, "Invalid split action."

        total_qty = sum(action.split_quantities.values())
        if total_qty != order.quantity:
            return 0.0, -0.08, f"Split quantities {total_qty} != order qty {order.quantity}."

        total_cost = 0.0
        for sid, qty in action.split_quantities.items():
            sup = self._find_supplier(sid)
            if sup is None or sup.status == "disrupted":
                return 0.0, -0.1, f"Supplier {sid} unavailable for split."
            total_cost += sup.cost_per_unit * qty

        if total_cost > self.budget_remaining:
            return 0.0, -0.1, "Insufficient budget for split."

        self.budget_remaining -= total_cost
        order.status = "assigned"
        order.assigned_supplier = ",".join(action.split_quantities.keys())
        return 0.2, 0.0, f"Order {order.id} split across {list(action.split_quantities.keys())}."

    def _handle_upgrade(self, action: Action) -> Tuple[float, float, str]:
        order = self._find_order(action.order_id)
        if order is None:
            return 0.0, -0.05, f"Order {action.order_id} not found."

        # Air freight: costs 3× but halves lead time
        supplier = self._find_supplier(order.assigned_supplier)
        if supplier is None:
            return 0.0, -0.05, "Order must be assigned before upgrading shipping."

        extra_cost = supplier.cost_per_unit * order.quantity * 2  # premium
        if extra_cost > self.budget_remaining:
            return 0.0, -0.08, "Budget insufficient for air freight upgrade."

        self.budget_remaining -= extra_cost
        # Reward only if order is critical/high priority
        if order.priority in ("critical", "high"):
            return 0.12, 0.0, f"Order {order.id} upgraded to air freight."
        return 0.04, 0.0, f"Order {order.id} upgraded (low priority — marginal gain)."

    def _handle_hold(self, action: Action) -> Tuple[float, float, str]:
        order = self._find_order(action.order_id)
        if order is None:
            return 0.0, -0.05, f"Order {action.order_id} not found."
        # Holding is fine short-term but penalised if deadline passes
        order.status = "pending"
        order.assigned_supplier = None
        return 0.0, 0.0, f"Order {order.id} held for reassignment."

    def _handle_cancel(self, action: Action) -> Tuple[float, float, str]:
        order = self._find_order(action.order_id)
        if order is None:
            return 0.0, -0.05, f"Order {action.order_id} not found."
        order.status = "failed"
        penalty = {"low": 0.05, "medium": 0.1, "high": 0.2, "critical": 0.35}
        p = penalty.get(order.priority, 0.1)
        return -p, p, f"Order {order.id} cancelled (priority={order.priority})."

    def _handle_activate_backup(self, action: Action) -> Tuple[float, float, str]:
        supplier = self._find_supplier(action.supplier_id)
        if supplier is None:
            return 0.0, -0.05, f"Supplier {action.supplier_id} not found."
        if supplier.status == "active":
            return 0.0, -0.02, f"Supplier {supplier.id} already active."
        supplier.status = "active"
        self.disruptions_handled += 1
        return 0.1, 0.0, f"Backup supplier {supplier.name} activated."

    # ------------------------------------------------------------------
    # Simulation tick — advance time, resolve disruptions, check deadlines
    # ------------------------------------------------------------------

    def _tick(self):
        self.days_elapsed += 1

        # Resolve disruptions that expire
        for d in self.disruptions:
            if d.affected_entity in self._disruption_remaining:
                self._disruption_remaining[d.affected_entity] -= 1
                if self._disruption_remaining[d.affected_entity] <= 0:
                    # Restore supplier
                    sup = self._find_supplier(d.affected_entity)
                    if sup and sup.status == "disrupted":
                        sup.status = "limited"

        # Mark assigned orders as fulfilled if lead time passed
        for order in self.orders:
            if order.status == "assigned":
                sup = self._find_supplier(order.assigned_supplier.split(",")[0])
                if sup and self.days_elapsed >= sup.lead_time_days:
                    order.status = "fulfilled"

        # Mark overdue pending orders as failed
        for order in self.orders:
            if order.status in ("pending", "assigned"):
                if self.days_elapsed > order.deadline_days:
                    order.status = "failed"

    # ------------------------------------------------------------------
    # Episode boundary
    # ------------------------------------------------------------------

    def _check_done(self) -> bool:
        if self.step_count >= self.max_steps:
            return True
        if self.budget_remaining <= 0:
            return True
        active = [o for o in self.orders if o.status in ("pending", "assigned")]
        if not active:
            return True
        return False

    # ------------------------------------------------------------------
    # Score & reward helpers
    # ------------------------------------------------------------------

    def _compute_final_score(self) -> float:
        """Compute a score strictly in (0.01, 0.99) — never exactly 0.0 or 1.0."""
        total = len(self.orders)
        if total == 0:
            return 0.01

        fulfilled = self._count_status("fulfilled")
        failed = self._count_status("failed")

        fulfillment = fulfilled / total
        cost_efficiency = max(0.0, self.budget_remaining / max(self.budget_total, 1.0))
        failure_penalty = failed / total

        score = (fulfillment * 0.6) + (cost_efficiency * 0.25) - (failure_penalty * 0.15)
        return round(max(0.01, min(0.99, score)), 4)

    def _build_reward(self, step_reward: float, msg: str,
                      penalty: float = 0.0, done: bool = False) -> Reward:
        total = len(self.orders)
        fulfilled = self._count_status("fulfilled")
        return Reward(
            step_reward=round(step_reward, 4),
            cumulative_reward=round(self.cumulative_reward, 4),
            fulfillment_score=round(fulfilled / max(total, 1), 4),
            cost_score=round(self.budget_remaining / max(self.budget_total, 1), 4),
            time_score=round(self._time_score(), 4),
            penalty=round(penalty, 4),
            done=done,
            info={"message": msg},
        )

    def _time_score(self) -> float:
        on_time = sum(
            1 for o in self.orders
            if o.status == "fulfilled" and self.days_elapsed <= o.deadline_days
        )
        total = len(self.orders)
        return on_time / max(total, 1)

    def _build_observation(self, message: str) -> Observation:
        return Observation(
            step=self.step_count,
            task_id=self.task_id,
            budget_remaining=round(self.budget_remaining, 2),
            budget_total=self.budget_total,
            orders=self.orders,
            suppliers=self.suppliers,
            routes=self.routes,
            active_disruptions=[
                d for d in self.disruptions
                if self._disruption_remaining.get(d.affected_entity, 0) > 0
            ],
            days_elapsed=self.days_elapsed,
            max_days=self.max_steps,
            message=message,
        )

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def _find_order(self, order_id: Optional[str]) -> Optional[Order]:
        if not order_id:
            return None
        return next((o for o in self.orders if o.id == order_id), None)

    def _find_supplier(self, supplier_id: Optional[str]) -> Optional[Supplier]:
        if not supplier_id:
            return None
        return next((s for s in self.suppliers if s.id == supplier_id), None)

    def _count_status(self, status: str) -> int:
        return sum(1 for o in self.orders if o.status == status)
