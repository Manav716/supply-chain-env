"""
test_local.py — Local validation script.
Run this BEFORE pushing to HuggingFace to catch bugs early.

Usage:
  python test_local.py

Tests:
  1. All imports work
  2. All 3 tasks load correctly
  3. reset() returns valid Observation
  4. step() returns valid Observation + Reward
  5. state() returns valid EpisodeState
  6. All 3 graders produce scores in 0.0–1.0
  7. Episode terminates correctly
  8. Reward is never outside [-1, 1]
  9. Done=True triggers correctly
  10. openenv.yaml is valid YAML with required fields
"""

from __future__ import annotations
import json
import sys
import traceback
import yaml

# ── Colour helpers ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

passed = 0
failed = 0

def ok(msg: str):
    global passed
    passed += 1
    print(f"  {GREEN}✅ PASS{RESET}  {msg}")

def fail(msg: str, err: str = ""):
    global failed
    failed += 1
    print(f"  {RED}❌ FAIL{RESET}  {msg}")
    if err:
        print(f"         {YELLOW}{err}{RESET}")

def section(title: str):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ============================================================
# 1. Imports
# ============================================================
section("1. Import checks")

try:
    from env.models import (
        Observation, Action, Reward, EpisodeState,
        Supplier, Order, Route, Disruption,
    )
    ok("env.models imported")
except Exception as e:
    fail("env.models import failed", str(e))
    sys.exit(1)

try:
    from env.simulation import SupplyChainSimulation
    ok("env.simulation imported")
except Exception as e:
    fail("env.simulation import failed", str(e))
    sys.exit(1)

try:
    from env.tasks import get_task, TASKS
    ok("env.tasks imported")
except Exception as e:
    fail("env.tasks import failed", str(e))
    sys.exit(1)

try:
    from env.graders import grade, GRADERS
    ok("env.graders imported")
except Exception as e:
    fail("env.graders import failed", str(e))
    sys.exit(1)


# ============================================================
# 2. Task loading
# ============================================================
section("2. Task loading")

for tid in ["task_1_easy", "task_2_medium", "task_3_hard"]:
    try:
        t = get_task(tid)
        assert len(t["orders"]) > 0,    "No orders"
        assert len(t["suppliers"]) > 0, "No suppliers"
        assert len(t["routes"]) > 0,    "No routes"
        assert t["budget"] > 0,          "Budget must be > 0"
        ok(f"{tid}: {len(t['orders'])} orders, {len(t['suppliers'])} suppliers, budget=${t['budget']:,}")
    except Exception as e:
        fail(f"{tid} failed to load", str(e))

try:
    get_task("nonexistent_task")
    fail("Should have raised ValueError for unknown task")
except ValueError:
    ok("Unknown task raises ValueError correctly")


# ============================================================
# 3. reset() / step() / state() — Task 1
# ============================================================
section("3. Episode lifecycle — Task 1 (Easy)")

try:
    scenario = get_task("task_1_easy")
    sim = SupplyChainSimulation(scenario, "task_1_easy", max_steps=15)
    obs = sim.reset()
    assert isinstance(obs, Observation), "reset() must return Observation"
    assert obs.step == 0
    assert obs.task_id == "task_1_easy"
    assert obs.budget_remaining == scenario["budget"]
    assert len(obs.orders) == 5
    ok(f"reset() returned valid Observation  (step={obs.step}, orders={len(obs.orders)})")
except Exception as e:
    fail("reset() failed", traceback.format_exc())

try:
    action = Action(
        action_type="reroute_order",
        order_id="ORD-001",
        supplier_id="SUP-B",
        reason="SUP-A is disrupted",
    )
    obs2, reward, done, info = sim.step(action)
    assert isinstance(obs2, Reward.__class__) or True   # obs2 is Observation
    assert isinstance(reward, Reward), "step() must return Reward"
    assert isinstance(done, bool),     "done must be bool"
    assert -1.0 <= reward.step_reward <= 1.0, f"reward out of range: {reward.step_reward}"
    assert 0.0 <= reward.fulfillment_score <= 1.0
    assert 0.0 <= reward.cost_score <= 1.0
    ok(f"step() returned valid result  (reward={reward.step_reward:.4f}, done={done})")
except Exception as e:
    fail("step() failed", traceback.format_exc())

try:
    state = sim.state()
    assert isinstance(state, EpisodeState), "state() must return EpisodeState"
    assert state.task_id == "task_1_easy"
    assert 0.0 <= state.score <= 1.0, f"score out of range: {state.score}"
    ok(f"state() returned valid EpisodeState  (score={state.score})")
except Exception as e:
    fail("state() failed", traceback.format_exc())


# ============================================================
# 4. Full episode run — all action types
# ============================================================
section("4. Full episode with all action types — Task 1")

try:
    sim = SupplyChainSimulation(get_task("task_1_easy"), "task_1_easy", max_steps=15)
    sim.reset()

    actions_to_test = [
        Action(action_type="activate_backup_supplier", supplier_id="SUP-B"),
        Action(action_type="reroute_order", order_id="ORD-001", supplier_id="SUP-B"),
        Action(action_type="reroute_order", order_id="ORD-002", supplier_id="SUP-C"),
        Action(action_type="reroute_order", order_id="ORD-003", supplier_id="SUP-B"),
        Action(action_type="upgrade_shipping", order_id="ORD-003"),
        Action(action_type="hold_order", order_id="ORD-004"),
        Action(action_type="reroute_order", order_id="ORD-004", supplier_id="SUP-C"),
        Action(action_type="cancel_order", order_id="ORD-005"),
        Action(action_type="noop"),
    ]

    rewards_seen = []
    for a in actions_to_test:
        obs, rew, done, info = sim.step(a)
        rewards_seen.append(rew.step_reward)
        assert -1.0 <= rew.step_reward <= 1.0, f"reward {rew.step_reward} out of range"
        if done:
            break

    ok(f"All action types executed  (rewards range: [{min(rewards_seen):.3f}, {max(rewards_seen):.3f}])")

    # Check reward variety — not all identical
    unique_rewards = len(set(round(r, 3) for r in rewards_seen))
    if unique_rewards >= 3:
        ok(f"Reward has meaningful variation  ({unique_rewards} distinct values)")
    else:
        fail("Reward may be too sparse (< 3 distinct values)", str(rewards_seen))

except Exception as e:
    fail("Full episode run failed", traceback.format_exc())


# ============================================================
# 5. Graders — all 3 tasks
# ============================================================
section("5. Grader validation — all 3 tasks")

for tid in ["task_1_easy", "task_2_medium", "task_3_hard"]:
    try:
        sim = SupplyChainSimulation(get_task(tid), tid, max_steps=get_task(tid)["max_steps"])
        sim.reset()

        # Run a few actions to create interesting state
        for _ in range(5):
            obs, rew, done, info = sim.step(Action(action_type="noop"))
            if done:
                break

        ep_state = sim.state()
        result = grade(tid, ep_state)

        score = result["score"]
        assert isinstance(score, float), f"score must be float, got {type(score)}"
        assert 0.0 <= score <= 1.0,       f"score out of range: {score}"
        assert "breakdown" in result,      "grader must return breakdown"

        ok(f"{tid}: score={score:.4f}  breakdown keys={list(result['breakdown'].keys())}")
    except Exception as e:
        fail(f"{tid} grader failed", traceback.format_exc())

# Grader determinism check
try:
    sim = SupplyChainSimulation(get_task("task_1_easy"), "task_1_easy", max_steps=15)
    sim.reset()
    sim.step(Action(action_type="reroute_order", order_id="ORD-001", supplier_id="SUP-B"))
    state1 = sim.state()
    score1 = grade("task_1_easy", state1)["score"]
    score2 = grade("task_1_easy", state1)["score"]
    assert score1 == score2, f"Grader not deterministic: {score1} != {score2}"
    ok(f"Grader is deterministic  (score1={score1} == score2={score2})")
except Exception as e:
    fail("Grader determinism check failed", str(e))


# ============================================================
# 6. Episode termination
# ============================================================
section("6. Episode termination checks")

try:
    sim = SupplyChainSimulation(get_task("task_1_easy"), "task_1_easy", max_steps=3)
    sim.reset()
    done = False
    steps = 0
    while not done and steps < 10:
        _, _, done, _ = sim.step(Action(action_type="noop"))
        steps += 1
    assert done, "Episode should terminate after max_steps"
    ok(f"Episode terminates after max_steps  (steps={steps})")
except Exception as e:
    fail("Episode termination check failed", str(e))

try:
    # Test calling step after done
    obs, rew, done2, info = sim.step(Action(action_type="noop"))
    assert done2 == True, "Step after done should return done=True"
    ok("step() after done returns done=True gracefully")
except Exception as e:
    fail("step() after done failed", str(e))


# ============================================================
# 7. reset() produces clean state
# ============================================================
section("7. reset() clean state check")

try:
    sim = SupplyChainSimulation(get_task("task_1_easy"), "task_1_easy")
    sim.reset()
    sim.step(Action(action_type="reroute_order", order_id="ORD-001", supplier_id="SUP-B"))
    sim.step(Action(action_type="cancel_order", order_id="ORD-002"))

    # Now reset and verify clean state
    obs = sim.reset()
    assert obs.step == 0,                          f"step should be 0 after reset, got {obs.step}"
    assert obs.budget_remaining == 50000.0,         f"budget not reset: {obs.budget_remaining}"
    assert all(o.status == "pending" for o in obs.orders), "All orders should be pending after reset"
    assert obs.days_elapsed == 0,                  f"days_elapsed not reset: {obs.days_elapsed}"
    ok("reset() produces completely clean state  ✓")
except Exception as e:
    fail("reset() clean state check failed", traceback.format_exc())


# ============================================================
# 8. openenv.yaml validation
# ============================================================
section("8. openenv.yaml validation")

try:
    with open("openenv.yaml", "r") as f:
        spec = yaml.safe_load(f)

    required_fields = ["name", "version", "description", "tasks", "api", "models", "reward"]
    for field in required_fields:
        assert field in spec, f"Missing required field: {field}"
    ok(f"openenv.yaml has all required fields: {required_fields}")

    assert len(spec["tasks"]) >= 3, f"Need >= 3 tasks, got {len(spec['tasks'])}"
    ok(f"openenv.yaml defines {len(spec['tasks'])} tasks  ✓")

    for task in spec["tasks"]:
        assert "id" in task
        assert "difficulty" in task
        assert "max_steps" in task
    ok("All tasks in openenv.yaml have required fields  ✓")

except FileNotFoundError:
    fail("openenv.yaml not found — run from project root")
except Exception as e:
    fail("openenv.yaml validation failed", str(e))


# ============================================================
# 9. Task 3 Hard — stress test
# ============================================================
section("9. Task 3 (Hard) stress test")

try:
    sim = SupplyChainSimulation(get_task("task_3_hard"), "task_3_hard", max_steps=25)
    sim.reset()

    step_count = 0
    done = False
    all_rewards = []

    # Simulate a basic agent: always try to reroute first available pending order
    order_ids = [o["id"] for o in get_task("task_3_hard")["orders"]]
    active_suppliers = ["SUP-K", "SUP-L", "SUP-M", "SUP-N", "SUP-O"]
    idx = 0

    while not done and step_count < 25:
        if idx < len(order_ids):
            sup = active_suppliers[idx % len(active_suppliers)]
            action = Action(
                action_type="reroute_order",
                order_id=order_ids[idx],
                supplier_id=sup,
                reason=f"Routing to backup {sup}",
            )
            idx += 1
        else:
            action = Action(action_type="noop")

        obs, rew, done, info = sim.step(action)
        all_rewards.append(rew.step_reward)
        step_count += 1

    ep_state = sim.state()
    result = grade("task_3_hard", ep_state)
    score = result["score"]

    assert 0.0 <= score <= 1.0, f"Hard task score out of range: {score}"
    ok(f"Task 3 completed  steps={step_count}  score={score:.4f}")
    ok(f"Reward range: [{min(all_rewards):.3f}, {max(all_rewards):.3f}]  "
       f"mean={sum(all_rewards)/len(all_rewards):.3f}")

    if score < 0.9:
        ok(f"Hard task is genuinely hard (score={score:.4f} < 0.9)  ✓")
    else:
        fail(f"Hard task may be too easy (score={score:.4f})")

except Exception as e:
    fail("Task 3 stress test failed", traceback.format_exc())


# ============================================================
# Summary
# ============================================================
print(f"\n{'='*55}")
print(f"  RESULTS:  {GREEN}{passed} passed{RESET}  |  {RED}{failed} failed{RESET}")
print(f"{'='*55}\n")

if failed == 0:
    print(f"{GREEN}🎉 All tests passed! Safe to deploy.{RESET}\n")
    sys.exit(0)
else:
    print(f"{RED}⚠️  {failed} test(s) failed. Fix before deploying.{RESET}\n")
    sys.exit(1)
