---
title: Supply Chain Env
emoji: 🚢
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - supply-chain
---

<div align="center">

# 🚢 Supply Chain Disruption Management

### An OpenEnv-compliant Reinforcement Learning Environment

*An AI agent acts as a supply chain coordinator, managing real-world disruptions in real time*

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-blue?style=for-the-badge)](https://openenv.ai)
[![HuggingFace](https://img.shields.io/badge/🤗-Live%20on%20HF%20Spaces-yellow?style=for-the-badge)](https://huggingface.co/spaces/manav716/supply-chain-env)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)](https://python.org)

**[🌐 Live API](https://manav716-supply-chain-env.hf.space) · [📖 API Docs](https://manav716-supply-chain-env.hf.space/docs) · [💻 GitHub](https://github.com/Manav716/supply-chain-env)**

</div>

---

## 🌍 Why This Environment?

Supply chain disruptions cost the global economy **$4+ trillion annually**. When a typhoon hits Southeast Asia, a port goes on strike, or a key supplier goes bankrupt — human coordinators must make dozens of fast, high-stakes decisions under pressure.

This environment puts an AI agent in that exact role. It must:

- 🔄 Reroute orders when suppliers go offline
- 💰 Manage tight budgets across competing priorities
- ⏰ Meet deadlines while minimising cost
- 🎯 Triage orders by value and priority under scarcity
- 🌊 Handle cascading failures with partial information

**This is a real problem. Fortune 500 companies spend billions solving it every year.**

---

## 🏗️ Architecture

```
supply-chain-env/
├── env/
│   ├── models.py       # Pydantic typed models (Observation, Action, Reward)
│   ├── simulation.py   # Core simulation engine
│   ├── tasks.py        # 3 task scenarios (easy → medium → hard)
│   └── graders.py      # Deterministic graders, strictly 0.01–0.99
├── api/
│   └── app.py          # FastAPI — OpenEnv HTTP interface
├── inference.py        # Baseline inference script (OpenAI client)
├── openenv.yaml        # OpenEnv spec
├── Dockerfile
└── requirements.txt
```

---

## 🎮 Tasks

### 🟢 Task 1 — Single Supplier Failure `(Easy)`

> *A factory fire in Taiwan takes out your primary electronics supplier. Reroute 5 orders before deadlines expire.*

| Property | Value |
|----------|-------|
| Orders | 5 |
| Suppliers | 3 (1 disrupted, 2 active) |
| Budget | $50,000 (generous) |
| Max Steps | 15 |
| Baseline Score | **0.9587** |

**Grader:** Fulfillment 60% · Priority orders 25% · Budget efficiency 15%

---

### 🟡 Task 2 — Port Closure Under Budget Pressure `(Medium)`

> *The Port of Shanghai is closed due to a labour strike. 15 orders need rerouting — but the budget won't cover air-freighting everything.*

| Property | Value |
|----------|-------|
| Orders | 15 |
| Suppliers | 4 (1 limited, 3 active) |
| Budget | $85,000 (tight) |
| Max Steps | 20 |
| Baseline Score | **0.7146** |

**Grader:** Fulfillment 40% · Priority value 30% · Budget 20% · Disruptions handled 10%

---

### 🔴 Task 3 — Cascading Triple Disruption `(Hard)`

> *Three simultaneous crises: typhoon in Southeast Asia, European supplier bankrupt, US port strike. 30 orders, 8 suppliers, budget insufficient for all. Who gets saved?*

| Property | Value |
|----------|-------|
| Orders | 30 |
| Suppliers | 8 (3 disrupted, 5 available) |
| Budget | $120,000 (not enough for all) |
| Max Steps | 25 |
| Baseline Score | **0.4473** |

**Grader:** Value-weighted fulfillment 35% · Critical survival 30% · Cost efficiency 20% · Triage quality 15%

---

## 📊 Baseline Results

Scores produced by `gpt-4o-mini` running `inference.py`:

| Task | Score | Steps | Difficulty |
|------|-------|-------|------------|
| task_1_easy | **0.9587** | 9 | 🟢 Easy |
| task_2_medium | **0.7146** | 20 | 🟡 Medium |
| task_3_hard | **0.4473** | 25 | 🔴 Hard |
| **Average** | **0.7069** | — | — |

The difficulty progression is meaningful — even frontier models struggle with Task 3.

---

## 🔌 OpenEnv API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/reset` | Start new episode |
| `POST` | `/step` | Take action, receive reward |
| `GET` | `/state` | Full current episode state |
| `POST` | `/grade` | Score episode (0.01–0.99) |
| `GET` | `/docs` | Interactive API documentation |
| `GET` | `/openenv.yaml` | OpenEnv spec file |

---

## 🧠 Observation Space

At every step the agent sees:

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
      "status": "pending",
      "value_usd": 15000.0
    }
  ],
  "suppliers": [
    {
      "id": "SUP-E",
      "name": "VietnamFactory Pro",
      "status": "active",
      "cost_per_unit": 35.0,
      "lead_time_days": 6
    }
  ],
  "active_disruptions": [
    {
      "type": "port_closure",
      "description": "Shanghai port closed due to labour strike.",
      "severity": 0.9,
      "duration_days": 12
    }
  ],
  "days_elapsed": 3,
  "message": "ORD-102 is critical with deadline in 4 days."
}
```

---

## 🎮 Action Space

```json
{
  "action_type": "reroute_order",
  "order_id": "ORD-101",
  "supplier_id": "SUP-E",
  "reason": "Primary supplier disrupted — rerouting to Vietnam backup."
}
```

| Action | Description | Reward |
|--------|-------------|--------|
| `reroute_order` | Assign order to active supplier | +0.15 to +0.25 |
| `split_order` | Split across multiple suppliers | +0.20 |
| `upgrade_shipping` | Air freight (faster, costly) | +0.04 to +0.12 |
| `activate_backup_supplier` | Bring limited supplier online | +0.10 |
| `hold_order` | Hold for reassignment | 0.00 |
| `cancel_order` | Cancel — heavy penalty | -0.05 to -0.35 |
| `noop` | Do nothing — penalised | -0.01 to -0.10 |

---

## 💰 Reward Function

Reward is **shaped** — every action gets a signal, never sparse.

```
✅ Reroute success          +0.15 – +0.25  (priority bonus)
✅ Deadline bonus           +0.05          (acting before deadline)
✅ Activate backup          +0.10
✅ Upgrade (critical)       +0.12
⚠️  Hold order              0.00
❌ Noop with pending orders -0.01 – -0.10
❌ Cancel low priority      -0.05
❌ Cancel critical          -0.35
❌ Assign to disrupted sup  -0.10
```

All final scores clamped to **(0.01, 0.99)** — never exactly 0 or 1.

---

## 🚀 Quick Start

### Test the Live API

```bash
# Health check
curl https://manav716-supply-chain-env.hf.space/health

# List tasks
curl https://manav716-supply-chain-env.hf.space/tasks

# Start episode
curl -X POST https://manav716-supply-chain-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_1_easy"}'

# Take action
curl -X POST https://manav716-supply-chain-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "reroute_order",
      "order_id": "ORD-001",
      "supplier_id": "SUP-B",
      "reason": "SUP-A is disrupted"
    }
  }'

# Grade episode
curl -X POST https://manav716-supply-chain-env.hf.space/grade
```

### Run Locally with Docker

```bash
git clone https://github.com/Manav716/supply-chain-env
cd supply-chain-env

docker build -t supply-chain-env .

docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="sk-your-openai-key" \
  supply-chain-env
```

### Run Baseline Inference

```bash
pip install -r requirements.txt

export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="sk-your-openai-key"
export ENV_BASE_URL="https://manav716-supply-chain-env.hf.space"

python3 inference.py
```

---

## 🧪 Run Tests

```bash
python3 test_local.py
# Expected: 26 passed | 0 failed
```

---

## 📋 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model identifier | `gpt-4o-mini` |
| `HF_TOKEN` | OpenAI or compatible API key | — |
| `ENV_BASE_URL` | Supply chain env URL | `http://localhost:7860` |
| `PORT` | Server port | `7860` |

---

## 📄 License

MIT License — open for research and commercial use.

---

<div align="center">

Built for the **Meta x HuggingFace OpenEnv Hackathon** 🏆

*Real problem. Real stakes. Real RL.*

</div>
