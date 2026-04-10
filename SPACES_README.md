---
title: Supply Chain Disruption Management OpenEnv
emoji: 🚢
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - supply-chain
  - logistics
  - real-world
  - decision-making
app_port: 7860
---

# 🚢 Supply Chain Disruption Management — OpenEnv

> An OpenEnv-compliant RL environment where an AI agent manages real-world supply chain disruptions.

## Quick Start

```bash
# Reset an episode
curl -X POST https://<your-space>.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_1_easy"}'

# Take a step
curl -X POST https://<your-space>.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "reroute_order",
      "order_id": "ORD-001",
      "supplier_id": "SUP-B",
      "reason": "Primary supplier disrupted"
    }
  }'

# Grade the episode
curl -X POST https://<your-space>.hf.space/grade
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/tasks` | List all tasks |
| `POST` | `/reset` | Start new episode |
| `POST` | `/step` | Take action |
| `GET`  | `/state` | Current state |
| `POST` | `/grade` | Score episode |

## Tasks

- 🟢 `task_1_easy` — Single supplier failure, 5 orders
- 🟡 `task_2_medium` — Port closure + budget pressure, 15 orders  
- 🔴 `task_3_hard` — Cascading triple disruption, 30 orders

See full [README](README.md) for complete documentation.
