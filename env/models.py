"""
OpenEnv typed models for Supply Chain Disruption Management.

Uses Pydantic v2 when available (production/Docker).
Falls back to dataclasses for local testing without pip install.
"""

from __future__ import annotations
import dataclasses
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel
    _PYDANTIC = True

    class _Base(BaseModel):
        def dict(self):
            return self.model_dump()

    class Supplier(_Base):
        id: str
        name: str
        location: str
        status: str
        capacity: int
        cost_per_unit: float
        lead_time_days: int
        reliability_score: float

    class Order(_Base):
        id: str
        product: str
        quantity: int
        priority: str
        deadline_days: int
        assigned_supplier: Optional[str] = None
        status: str = "pending"
        value_usd: float = 0.0

    class Route(_Base):
        id: str
        origin: str
        destination: str
        mode: str
        transit_days: int
        cost_per_unit: float
        status: str = "active"

    class Disruption(_Base):
        id: str
        type: str
        affected_entity: str
        severity: float
        description: str
        duration_days: int

    class Observation(_Base):
        step: int
        task_id: str
        budget_remaining: float
        budget_total: float
        orders: List[Order]
        suppliers: List[Supplier]
        routes: List[Route]
        active_disruptions: List[Disruption]
        days_elapsed: int
        max_days: int
        message: str = ""

    class Action(_Base):
        action_type: str
        order_id: Optional[str] = None
        supplier_id: Optional[str] = None
        route_id: Optional[str] = None
        split_quantities: Optional[Dict[str, int]] = None
        reason: Optional[str] = None

    class Reward(_Base):
        step_reward: float
        cumulative_reward: float
        fulfillment_score: float
        cost_score: float
        time_score: float
        penalty: float
        done: bool
        info: Dict[str, Any] = {}

    class EpisodeState(_Base):
        task_id: str
        step: int
        max_steps: int
        done: bool
        observation: Observation
        total_reward: float
        orders_fulfilled: int
        orders_failed: int
        orders_pending: int
        budget_spent: float
        budget_total: float
        disruptions_handled: int
        score: float

except ImportError:
    _PYDANTIC = False

    # ------------------------------------------------------------------
    # Minimal dataclass shim — used only when Pydantic is not installed
    # Behaviour is identical for our simulation / test code
    # ------------------------------------------------------------------

    class _Base:
        def dict(self):
            return dataclasses.asdict(self)
        def model_dump(self):
            return dataclasses.asdict(self)

    @dataclasses.dataclass
    class Supplier(_Base):
        id: str = ""
        name: str = ""
        location: str = ""
        status: str = "active"
        capacity: int = 0
        cost_per_unit: float = 0.0
        lead_time_days: int = 1
        reliability_score: float = 1.0

    @dataclasses.dataclass
    class Order(_Base):
        id: str = ""
        product: str = ""
        quantity: int = 0
        priority: str = "medium"
        deadline_days: int = 10
        assigned_supplier: Optional[str] = None
        status: str = "pending"
        value_usd: float = 0.0

    @dataclasses.dataclass
    class Route(_Base):
        id: str = ""
        origin: str = ""
        destination: str = ""
        mode: str = "sea"
        transit_days: int = 10
        cost_per_unit: float = 1.0
        status: str = "active"

    @dataclasses.dataclass
    class Disruption(_Base):
        id: str = ""
        type: str = ""
        affected_entity: str = ""
        severity: float = 1.0
        description: str = ""
        duration_days: int = 5

    @dataclasses.dataclass
    class Observation(_Base):
        step: int = 0
        task_id: str = ""
        budget_remaining: float = 0.0
        budget_total: float = 0.0
        orders: List[Any] = dataclasses.field(default_factory=list)
        suppliers: List[Any] = dataclasses.field(default_factory=list)
        routes: List[Any] = dataclasses.field(default_factory=list)
        active_disruptions: List[Any] = dataclasses.field(default_factory=list)
        days_elapsed: int = 0
        max_days: int = 20
        message: str = ""

    @dataclasses.dataclass
    class Action(_Base):
        action_type: str = "noop"
        order_id: Optional[str] = None
        supplier_id: Optional[str] = None
        route_id: Optional[str] = None
        split_quantities: Optional[Dict[str, int]] = None
        reason: Optional[str] = None

    @dataclasses.dataclass
    class Reward(_Base):
        step_reward: float = 0.0
        cumulative_reward: float = 0.0
        fulfillment_score: float = 0.0
        cost_score: float = 0.0
        time_score: float = 0.0
        penalty: float = 0.0
        done: bool = False
        info: Dict[str, Any] = dataclasses.field(default_factory=dict)

    @dataclasses.dataclass
    class EpisodeState(_Base):
        task_id: str = ""
        step: int = 0
        max_steps: int = 20
        done: bool = False
        observation: Any = None
        total_reward: float = 0.0
        orders_fulfilled: int = 0
        orders_failed: int = 0
        orders_pending: int = 0
        budget_spent: float = 0.0
        budget_total: float = 0.0
        disruptions_handled: int = 0
        score: float = 0.0
