"""
FastAPI application — OpenEnv HTTP interface.
Endpoints:
  POST /reset          — start new episode
  POST /step           — take action, get observation + reward
  GET  /state          — get full current state
  GET  /tasks          — list available tasks
  POST /grade          — run grader on current state
  GET  /health         — health check
  GET  /openenv.yaml   — serve spec file
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Make sure env package is importable regardless of cwd
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from env.models import Action, EpisodeState, Observation, Reward
from env.simulation import SupplyChainSimulation
from env.tasks import TASKS, get_task
from env.graders import grade

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Supply Chain Disruption Management — OpenEnv",
    description=(
        "An OpenEnv-compliant reinforcement learning environment where an AI agent "
        "acts as a supply chain coordinator managing disruptions in real time."
    ),
    version="1.0.0",
)

# Global simulation instance (single-session; extend to multi-session with dict)
_sim: Optional[SupplyChainSimulation] = None
_current_task_id: str = "task_1_easy"


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "task_1_easy"


class StepRequest(BaseModel):
    action: Action


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]


class GradeResponse(BaseModel):
    task_id: str
    score: float
    breakdown: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_sim() -> SupplyChainSimulation:
    if _sim is None:
        raise HTTPException(status_code=400, detail="Call /reset first to start an episode.")
    return _sim


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "environment": "supply-chain-disruption-management"}


@app.get("/tasks")
def list_tasks():
    return {
        tid: {
            "name": t["name"],
            "description": t["description"],
            "difficulty": t["difficulty"],
            "max_steps": t["max_steps"],
            "num_orders": len(t["orders"]),
            "num_suppliers": len(t["suppliers"]),
            "budget": t["budget"],
        }
        for tid, t in TASKS.items()
    }


@app.post("/reset", response_model=Observation)
def reset(req: Optional[ResetRequest] = Body(default=None)):
    global _sim, _current_task_id
    if req is None:
        req = ResetRequest()
    try:
        scenario = get_task(req.task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    _current_task_id = req.task_id
    _sim = SupplyChainSimulation(
        scenario=scenario,
        task_id=req.task_id,
        max_steps=scenario["max_steps"],
    )
    obs = _sim.reset()
    return obs


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    sim = _require_sim()
    obs, reward, done, info = sim.step(req.action)
    return StepResponse(observation=obs, reward=reward, done=done, info=info)


@app.get("/state", response_model=EpisodeState)
def state():
    sim = _require_sim()
    return sim.state()


@app.post("/grade", response_model=GradeResponse)
def grade_episode():
    sim = _require_sim()
    ep_state = sim.state()
    result = grade(_current_task_id, ep_state)
    return GradeResponse(
        task_id=_current_task_id,
        score=result["score"],
        breakdown=result["breakdown"],
    )


@app.get("/openenv.yaml")
def serve_yaml():
    yaml_path = ROOT / "openenv.yaml"
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail="openenv.yaml not found")
    return FileResponse(str(yaml_path), media_type="text/yaml")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("api.app:app", host="0.0.0.0", port=port, reload=False)
