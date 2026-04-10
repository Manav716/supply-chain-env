# 🚢 Supply Chain Disruption Management — OpenEnv

> An OpenEnv-compliant reinforcement learning environment where an AI agent acts as a **supply chain coordinator**, managing real-world disruptions in real time.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue)](https://openenv.ai)
[![HF Space](https://img.shields.io/badge/🤗-Hugging%20Face%20Space-yellow)](https://huggingface.co/spaces)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🌍 Why This Environment?

Supply chain disruptions cost the global economy **$4+ trillion annually**. When a typhoon hits Southeast Asia, a port goes on strike, or a key supplier goes bankrupt, human coordinators must make dozens of fast, constrained decisions — rerouting orders, activating backup suppliers, managing budgets, and prioritising high-value customers.

This environment puts an AI agent in that role. It must learn to:
- Triage orders by priority and value under resource constraints
- Navigate cascading failures with incomplete information
- Balance cost vs. speed vs. deadline adherence
- Make decisions with partial-progress reward at every step

**This is a real problem. Fortune 500 companies spend billions solving it.**

---

## 📁 Project Structure

```
supply-chain-env/
├── env/
│   ├── models.py       # Pydantic typed models (Observation, Action, Reward)
│   ├── simulation.py   # Core simulation engine
│   ├── tasks.py        # 3 task scenarios (easy → medium → hard)
│   └── graders.py      # Deterministic graders, 0.0–1.0
├── api/
│   └── app.py          # FastAPI — step() / reset() / state() endpoints
├── inference.py        # Baseline inference script (OpenAI client)
├── openenv.yaml        # OpenEnv spec
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔌 OpenEnv API

All endpoints follow the OpenEnv spec.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start new episode `{"task_id": "task_1_easy"}` |
| `POST` | `/step` | Take action, receive observation + reward |
| `GET`  | `/state` | Full current episode state |
| `POST` | `/grade` | Run grader on current state → score 0.0–1.0 |
| `GET`  | `/tasks` | List all available tasks |
| `GET`  | `/health` | Health check |
| `GET`  | `/openenv.yaml` | Spec file |

---

## 🧠 Observation Space

```json
{
  "step": 3,
  "task_id": "task_2_medium",
  "budget_remaining": 62000.0,
  "budget_total": 85000.0,
  "orders": [
    {
      "id": "ORD-101",
      "product": "Textile Rolls",
      "quantity": 300,
      "priority": "high",
      "deadline_days": 10,
      "assigned_supplier": null,
      "status": "pending",
      "value_usd": 15000.0
    }
  ],
  "suppliers": [
    {
      "id": "SUP-E",
      "name": "VietnamFactory Pro",
      "location": "Vietnam",
      "status": "active",
      "capacity": 600,
      "cost_per_unit": 35.0,
      "lead_time_days": 6,
      "reliability_score": 0.85
    }
  ],
  "routes": [...],
  "active_disruptions": [
    {
      "id": "DIS-010",
      "type": "port_closure",
      "affected_entity": "RT-010",
      "severity": 0.9,
      "description": "Shanghai port closed due to labour strike.",
      "duration_days": 12
    }
  ],
  "days_elapsed": 3,
  "max_days": 20,
  "message": "Order ORD-102 is critical and deadline is in 4 days."
}
```

---

## 🎮 Action Space

```json
{
  "action_type": "reroute_order",
  "order_id": "ORD-101",
  "supplier_id": "SUP-E",
  "reason": "Primary supplier disrupted; rerouting to Vietnam backup within deadline."
}
```

**Valid action types:**

| Action | Description |
|--------|-------------|
| `reroute_order` | Assign a pending order to a different active supplier |
| `split_order` | Split one order across multiple suppliers |
| `upgrade_shipping` | Upgrade to air freight (faster, costly) |
| `hold_order` | Hold for reassignment (resets assignment) |
| `cancel_order` | Cancel order — heavy penalty for critical/high |
| `activate_backup_supplier` | Bring a limited supplier online |
| `noop` | Do nothing — penalised if orders remain pending |

---

## 🏆 Tasks

### Task 1 — Easy: Single Supplier Failure
| Property | Value |
|----------|-------|
| Difficulty | 🟢 Easy |
| Orders | 5 |
| Suppliers | 3 (1 disrupted, 2 active backups) |
| Budget | $50,000 (generous) |
| Max Steps | 15 |
| Key challenge | Correctly identify disrupted supplier and reroute |

**Grader weights:** Fulfillment 60% · Priority orders 25% · Budget efficiency 15%

---

### Task 2 — Medium: Port Closure Under Budget Pressure
| Property | Value |
|----------|-------|
| Difficulty | 🟡 Medium |
| Orders | 15 |
| Suppliers | 4 (1 limited, 3 active) |
| Budget | $85,000 (tight — can't air-freight everything) |
| Max Steps | 20 |
| Key challenge | Balance cost vs. speed, prioritise critical orders |

**Grader weights:** Fulfillment 40% · Priority value 30% · Budget 20% · Disruptions handled 10%

---

### Task 3 — Hard: Cascading Triple Disruption
| Property | Value |
|----------|-------|
| Difficulty | 🔴 Hard |
| Orders | 30 |
| Suppliers | 8 (3 disrupted, 5 available) |
| Budget | $120,000 (insufficient for all orders) |
| Max Steps | 25 |
| Key challenge | Triage under scarcity — budget forces sacrifice of low-priority orders |

**Grader weights:** Value-weighted fulfillment 35% · Critical survival 30% · Cost efficiency 20% · Triage quality 15%

---

## 💰 Reward Function

Reward is **shaped** — not sparse. Every action gets a signal.

```
reroute_order (success)       +0.15 to +0.25   (priority bonus)
deadline bonus                +0.05             (if within deadline)
activate_backup_supplier      +0.10
upgrade_shipping (critical)   +0.12
upgrade_shipping (low)        +0.04
hold_order                    0.00
noop                          -0.01 to -0.10   (scales with pending orders)
cancel_order (low)            -0.05
cancel_order (medium)         -0.10
cancel_order (high)           -0.20
cancel_order (critical)       -0.35
assign to disrupted supplier  -0.10
budget exceeded               episode ends
```

---

## 📊 Baseline Scores

Scores produced by `gpt-4o-mini` running `inference.py`:

| Task | Score | Notes |
|------|-------|-------|
| task_1_easy | ~0.75 | Handles basic rerouting well |
| task_2_medium | ~0.55 | Struggles with budget optimisation |
| task_3_hard | ~0.35 | Triage under scarcity is genuinely hard |

---

## 🚀 Setup & Usage

### Option 1 — Docker (recommended)

```bash
git clone https://huggingface.co/spaces/<your-username>/supply-chain-env
cd supply-chain-env

# Build
docker build -t supply-chain-env .

# Run environment server
docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="your-openai-api-key" \
  supply-chain-env
```

### Option 2 — Local Python

```bash
pip install -r requirements.txt

# Start server
uvicorn api.app:app --host 0.0.0.0 --port 7860

# In another terminal — run baseline
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="sk-your-openai-key"
export ENV_BASE_URL="http://localhost:7860"

python inference.py
```

### Quick API test

```bash
# Reset episode
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_1_easy"}'

# Take an action
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "reroute_order",
      "order_id": "ORD-001",
      "supplier_id": "SUP-B",
      "reason": "SUP-A is disrupted"
    }
  }'

# Get current state
curl http://localhost:7860/state

# Grade episode
curl -X POST http://localhost:7860/grade
```

---

## 📋 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model identifier | `gpt-4o-mini` |
| `HF_TOKEN` | API key (OpenAI or compatible) | — |
| `ENV_BASE_URL` | Supply chain env API URL | `http://localhost:7860` |
| `PORT` | Server port | `7860` |

---

## 🧪 Validate

```bash
# OpenEnv validator
openenv validate openenv.yaml

# Manual health check
curl http://localhost:7860/health
# → {"status": "ok", "environment": "supply-chain-disruption-management"}
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
