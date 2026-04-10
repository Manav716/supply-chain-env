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

# 🚢 Supply Chain Disruption Management — OpenEnv

An OpenEnv-compliant RL environment where an AI agent manages real-world supply chain disruptions.

## Quick Start

```bash
# Health check
curl https://manav716-supply-chain-env.hf.space/health

# Reset episode
curl -X POST https://manav716-supply-chain-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_1_easy"}'
```

## Tasks
- 🟢 task_1_easy — Single supplier failure, 5 orders
- 🟡 task_2_medium — Port closure + budget pressure, 15 orders
- 🔴 task_3_hard — Cascading triple disruption, 30 orders

## API Endpoints
- POST /reset — start episode
- POST /step — take action
- GET /state — current state
- POST /grade — score episode
- GET /health — health check
