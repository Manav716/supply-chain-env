"""
Task definitions for Supply Chain Disruption Management.
Each task is a complete scenario dict fed into SupplyChainSimulation.

Task 1 (Easy)   — Single supplier failure, 5 orders, 1 backup
Task 2 (Medium) — Port closure + budget pressure, 15 orders, 3 backups
Task 3 (Hard)   — Cascading triple disruption, 30 orders, dynamic pricing
"""

from __future__ import annotations
from typing import Any, Dict

# ---------------------------------------------------------------------------
# TASK 1 — EASY
# One supplier goes down. Clear backup. 5 orders. Generous budget.
# ---------------------------------------------------------------------------

TASK_1: Dict[str, Any] = {
    "id": "task_1_easy",
    "name": "Single Supplier Failure",
    "description": (
        "Supplier SUP-A (electronics components from Taiwan) has gone offline "
        "due to a factory fire. Reroute 5 pending orders to available backup "
        "suppliers before deadlines expire. Budget is generous."
    ),
    "difficulty": "easy",
    "max_steps": 15,
    "budget": 50000.0,
    "suppliers": [
        {
            "id": "SUP-A",
            "name": "TaiwanTech Components",
            "location": "Taiwan",
            "status": "disrupted",
            "capacity": 500,
            "cost_per_unit": 45.0,
            "lead_time_days": 3,
            "reliability_score": 0.95,
        },
        {
            "id": "SUP-B",
            "name": "KoreaElec Supply",
            "location": "South Korea",
            "status": "active",
            "capacity": 400,
            "cost_per_unit": 52.0,
            "lead_time_days": 4,
            "reliability_score": 0.90,
        },
        {
            "id": "SUP-C",
            "name": "JapanParts Co.",
            "location": "Japan",
            "status": "active",
            "capacity": 300,
            "cost_per_unit": 58.0,
            "lead_time_days": 3,
            "reliability_score": 0.93,
        },
    ],
    "orders": [
        {"id": "ORD-001", "product": "Microchips A100",  "quantity": 100, "priority": "high",     "deadline_days": 8,  "value_usd": 8000.0,  "status": "pending"},
        {"id": "ORD-002", "product": "Circuit Boards",   "quantity": 80,  "priority": "medium",   "deadline_days": 10, "value_usd": 5000.0,  "status": "pending"},
        {"id": "ORD-003", "product": "Power Units",      "quantity": 60,  "priority": "critical", "deadline_days": 6,  "value_usd": 9000.0,  "status": "pending"},
        {"id": "ORD-004", "product": "Capacitors Bulk",  "quantity": 200, "priority": "low",      "deadline_days": 14, "value_usd": 3000.0,  "status": "pending"},
        {"id": "ORD-005", "product": "GPU Modules",      "quantity": 50,  "priority": "high",     "deadline_days": 7,  "value_usd": 12000.0, "status": "pending"},
    ],
    "routes": [
        {"id": "RT-001", "origin": "Taiwan",      "destination": "USA", "mode": "sea",  "transit_days": 14, "cost_per_unit": 2.5, "status": "active"},
        {"id": "RT-002", "origin": "South Korea", "destination": "USA", "mode": "sea",  "transit_days": 12, "cost_per_unit": 3.0, "status": "active"},
        {"id": "RT-003", "origin": "Japan",       "destination": "USA", "mode": "air",  "transit_days": 2,  "cost_per_unit": 8.0, "status": "active"},
    ],
    "disruptions": [
        {
            "id": "DIS-001",
            "type": "supplier_down",
            "affected_entity": "SUP-A",
            "severity": 1.0,
            "description": "Factory fire at TaiwanTech. Full shutdown for 10 days.",
            "duration_days": 10,
        }
    ],
}


# ---------------------------------------------------------------------------
# TASK 2 — MEDIUM
# Port closure blocks main route. Budget is tight. 15 orders. 3 backup options.
# Agent must balance cost vs. speed, prioritise critical orders.
# ---------------------------------------------------------------------------

TASK_2: Dict[str, Any] = {
    "id": "task_2_medium",
    "name": "Port Closure Under Budget Pressure",
    "description": (
        "The Port of Shanghai has been closed due to a labour strike. "
        "15 orders from 3 suppliers must be rerouted through alternative ports "
        "or upgraded to air freight. Budget is $85,000 — not enough to air-freight "
        "everything. Prioritise critical and high-priority orders."
    ),
    "difficulty": "medium",
    "max_steps": 20,
    "budget": 85000.0,
    "suppliers": [
        {
            "id": "SUP-D",
            "name": "ShanghaiMfg Ltd",
            "location": "China",
            "status": "limited",
            "capacity": 800,
            "cost_per_unit": 30.0,
            "lead_time_days": 5,
            "reliability_score": 0.88,
        },
        {
            "id": "SUP-E",
            "name": "VietnamFactory Pro",
            "location": "Vietnam",
            "status": "active",
            "capacity": 600,
            "cost_per_unit": 35.0,
            "lead_time_days": 6,
            "reliability_score": 0.85,
        },
        {
            "id": "SUP-F",
            "name": "IndiaMake Corp",
            "location": "India",
            "status": "active",
            "capacity": 500,
            "cost_per_unit": 28.0,
            "lead_time_days": 7,
            "reliability_score": 0.82,
        },
        {
            "id": "SUP-G",
            "name": "ThaiSupply Hub",
            "location": "Thailand",
            "status": "active",
            "capacity": 400,
            "cost_per_unit": 33.0,
            "lead_time_days": 5,
            "reliability_score": 0.87,
        },
    ],
    "orders": [
        {"id": "ORD-101", "product": "Textile Rolls",      "quantity": 300, "priority": "high",     "deadline_days": 10, "value_usd": 15000.0, "status": "pending"},
        {"id": "ORD-102", "product": "Plastic Molds",      "quantity": 150, "priority": "critical", "deadline_days": 7,  "value_usd": 20000.0, "status": "pending"},
        {"id": "ORD-103", "product": "Steel Brackets",     "quantity": 400, "priority": "medium",   "deadline_days": 14, "value_usd": 8000.0,  "status": "pending"},
        {"id": "ORD-104", "product": "Rubber Gaskets",     "quantity": 200, "priority": "low",      "deadline_days": 18, "value_usd": 4000.0,  "status": "pending"},
        {"id": "ORD-105", "product": "Copper Wire Spool",  "quantity": 500, "priority": "high",     "deadline_days": 9,  "value_usd": 18000.0, "status": "pending"},
        {"id": "ORD-106", "product": "Foam Insulation",    "quantity": 250, "priority": "medium",   "deadline_days": 16, "value_usd": 6000.0,  "status": "pending"},
        {"id": "ORD-107", "product": "Aluminium Sheets",   "quantity": 180, "priority": "critical", "deadline_days": 6,  "value_usd": 22000.0, "status": "pending"},
        {"id": "ORD-108", "product": "PVC Pipes",          "quantity": 600, "priority": "low",      "deadline_days": 20, "value_usd": 5000.0,  "status": "pending"},
        {"id": "ORD-109", "product": "Glass Panels",       "quantity": 100, "priority": "high",     "deadline_days": 11, "value_usd": 17000.0, "status": "pending"},
        {"id": "ORD-110", "product": "Bearings Assorted",  "quantity": 800, "priority": "medium",   "deadline_days": 13, "value_usd": 9000.0,  "status": "pending"},
        {"id": "ORD-111", "product": "LED Strips",         "quantity": 1000,"priority": "low",      "deadline_days": 22, "value_usd": 3000.0,  "status": "pending"},
        {"id": "ORD-112", "product": "Motor Drives",       "quantity": 75,  "priority": "critical", "deadline_days": 8,  "value_usd": 25000.0, "status": "pending"},
        {"id": "ORD-113", "product": "Filters HEPA",       "quantity": 200, "priority": "high",     "deadline_days": 12, "value_usd": 11000.0, "status": "pending"},
        {"id": "ORD-114", "product": "Conveyor Belts",     "quantity": 50,  "priority": "medium",   "deadline_days": 15, "value_usd": 7000.0,  "status": "pending"},
        {"id": "ORD-115", "product": "Chemical Solvents",  "quantity": 300, "priority": "high",     "deadline_days": 10, "value_usd": 14000.0, "status": "pending"},
    ],
    "routes": [
        {"id": "RT-010", "origin": "China",    "destination": "USA", "mode": "sea",  "transit_days": 18, "cost_per_unit": 2.0, "status": "blocked"},
        {"id": "RT-011", "origin": "China",    "destination": "USA", "mode": "air",  "transit_days": 3,  "cost_per_unit": 9.0, "status": "active"},
        {"id": "RT-012", "origin": "Vietnam",  "destination": "USA", "mode": "sea",  "transit_days": 16, "cost_per_unit": 2.5, "status": "active"},
        {"id": "RT-013", "origin": "India",    "destination": "USA", "mode": "sea",  "transit_days": 20, "cost_per_unit": 2.2, "status": "active"},
        {"id": "RT-014", "origin": "Thailand", "destination": "USA", "mode": "sea",  "transit_days": 15, "cost_per_unit": 2.8, "status": "active"},
        {"id": "RT-015", "origin": "Vietnam",  "destination": "USA", "mode": "air",  "transit_days": 2,  "cost_per_unit": 8.5, "status": "active"},
    ],
    "disruptions": [
        {
            "id": "DIS-010",
            "type": "port_closure",
            "affected_entity": "RT-010",
            "severity": 0.9,
            "description": "Shanghai port closed due to labour strike. All sea freight blocked.",
            "duration_days": 12,
        },
        {
            "id": "DIS-011",
            "type": "supplier_down",
            "affected_entity": "SUP-D",
            "severity": 0.4,
            "description": "ShanghaiMfg operating at 40% capacity due to worker shortage.",
            "duration_days": 8,
        },
    ],
}


# ---------------------------------------------------------------------------
# TASK 3 — HARD
# Three simultaneous cascading disruptions. 30 orders. Dynamic supplier
# pricing. VIP customers. Budget is deliberately insufficient for all orders
# — agent must triage. Penalises cancelling critical orders heavily.
# ---------------------------------------------------------------------------

TASK_3: Dict[str, Any] = {
    "id": "task_3_hard",
    "name": "Cascading Triple Disruption",
    "description": (
        "Three simultaneous disruptions: (1) typhoon blocks Southeast Asian suppliers, "
        "(2) US East Coast port strike, (3) key European hub supplier bankrupt. "
        "30 orders, 8 suppliers, tight budget of $120,000. Budget is insufficient "
        "to fulfil all orders — agent must triage by priority and value. "
        "VIP customers (marked critical) incur heavy penalties if failed. "
        "Dynamic pricing: backup suppliers raise costs mid-episode."
    ),
    "difficulty": "hard",
    "max_steps": 25,
    "budget": 120000.0,
    "suppliers": [
        {
            "id": "SUP-H", "name": "AsiaFlex Vietnam",
            "location": "Vietnam", "status": "disrupted",
            "capacity": 1000, "cost_per_unit": 25.0,
            "lead_time_days": 6, "reliability_score": 0.90,
        },
        {
            "id": "SUP-I", "name": "MalayParts Group",
            "location": "Malaysia", "status": "disrupted",
            "capacity": 800, "cost_per_unit": 27.0,
            "lead_time_days": 7, "reliability_score": 0.88,
        },
        {
            "id": "SUP-J", "name": "EuroHub GmbH",
            "location": "Germany", "status": "disrupted",
            "capacity": 600, "cost_per_unit": 55.0,
            "lead_time_days": 5, "reliability_score": 0.95,
        },
        {
            "id": "SUP-K", "name": "MexicoManufactura",
            "location": "Mexico", "status": "active",
            "capacity": 500, "cost_per_unit": 38.0,
            "lead_time_days": 4, "reliability_score": 0.84,
        },
        {
            "id": "SUP-L", "name": "CanadaIndustrial",
            "location": "Canada", "status": "active",
            "capacity": 400, "cost_per_unit": 48.0,
            "lead_time_days": 3, "reliability_score": 0.92,
        },
        {
            "id": "SUP-M", "name": "BrazilSupply SA",
            "location": "Brazil", "status": "active",
            "capacity": 300, "cost_per_unit": 32.0,
            "lead_time_days": 8, "reliability_score": 0.80,
        },
        {
            "id": "SUP-N", "name": "TurkeyMfg Ltd",
            "location": "Turkey", "status": "limited",
            "capacity": 350, "cost_per_unit": 36.0,
            "lead_time_days": 6, "reliability_score": 0.83,
        },
        {
            "id": "SUP-O", "name": "USLocalSource",
            "location": "USA", "status": "active",
            "capacity": 200, "cost_per_unit": 72.0,
            "lead_time_days": 1, "reliability_score": 0.98,
        },
    ],
    "orders": [
        {"id": "ORD-201", "product": "Server Racks",        "quantity": 20,  "priority": "critical", "deadline_days": 5,  "value_usd": 40000.0, "status": "pending"},
        {"id": "ORD-202", "product": "Battery Packs",       "quantity": 150, "priority": "high",     "deadline_days": 8,  "value_usd": 22000.0, "status": "pending"},
        {"id": "ORD-203", "product": "Solar Panels",        "quantity": 80,  "priority": "medium",   "deadline_days": 14, "value_usd": 18000.0, "status": "pending"},
        {"id": "ORD-204", "product": "Hydraulic Pumps",     "quantity": 40,  "priority": "critical", "deadline_days": 6,  "value_usd": 35000.0, "status": "pending"},
        {"id": "ORD-205", "product": "Control Panels",      "quantity": 60,  "priority": "high",     "deadline_days": 9,  "value_usd": 28000.0, "status": "pending"},
        {"id": "ORD-206", "product": "Optical Cables",      "quantity": 500, "priority": "medium",   "deadline_days": 16, "value_usd": 8000.0,  "status": "pending"},
        {"id": "ORD-207", "product": "Cooling Systems",     "quantity": 30,  "priority": "critical", "deadline_days": 7,  "value_usd": 45000.0, "status": "pending"},
        {"id": "ORD-208", "product": "PCB Assemblies",      "quantity": 200, "priority": "high",     "deadline_days": 10, "value_usd": 20000.0, "status": "pending"},
        {"id": "ORD-209", "product": "Transformer Units",   "quantity": 25,  "priority": "medium",   "deadline_days": 18, "value_usd": 12000.0, "status": "pending"},
        {"id": "ORD-210", "product": "Safety Valves",       "quantity": 300, "priority": "high",     "deadline_days": 11, "value_usd": 15000.0, "status": "pending"},
        {"id": "ORD-211", "product": "Diesel Generators",   "quantity": 10,  "priority": "critical", "deadline_days": 8,  "value_usd": 60000.0, "status": "pending"},
        {"id": "ORD-212", "product": "Pneumatic Tools",     "quantity": 100, "priority": "low",      "deadline_days": 22, "value_usd": 5000.0,  "status": "pending"},
        {"id": "ORD-213", "product": "Welding Equipment",   "quantity": 50,  "priority": "medium",   "deadline_days": 15, "value_usd": 10000.0, "status": "pending"},
        {"id": "ORD-214", "product": "Compressor Units",    "quantity": 35,  "priority": "high",     "deadline_days": 9,  "value_usd": 25000.0, "status": "pending"},
        {"id": "ORD-215", "product": "Turbine Blades",      "quantity": 15,  "priority": "critical", "deadline_days": 6,  "value_usd": 55000.0, "status": "pending"},
        {"id": "ORD-216", "product": "Heat Exchangers",     "quantity": 45,  "priority": "medium",   "deadline_days": 17, "value_usd": 14000.0, "status": "pending"},
        {"id": "ORD-217", "product": "Pressure Gauges",     "quantity": 400, "priority": "low",      "deadline_days": 24, "value_usd": 4000.0,  "status": "pending"},
        {"id": "ORD-218", "product": "Flow Meters",         "quantity": 120, "priority": "medium",   "deadline_days": 13, "value_usd": 11000.0, "status": "pending"},
        {"id": "ORD-219", "product": "Industrial Sensors",  "quantity": 600, "priority": "high",     "deadline_days": 12, "value_usd": 16000.0, "status": "pending"},
        {"id": "ORD-220", "product": "CNC Machine Parts",   "quantity": 80,  "priority": "high",     "deadline_days": 10, "value_usd": 30000.0, "status": "pending"},
        {"id": "ORD-221", "product": "Rotary Encoders",     "quantity": 200, "priority": "medium",   "deadline_days": 15, "value_usd": 9000.0,  "status": "pending"},
        {"id": "ORD-222", "product": "Power Converters",    "quantity": 90,  "priority": "high",     "deadline_days": 11, "value_usd": 21000.0, "status": "pending"},
        {"id": "ORD-223", "product": "Cable Harnesses",     "quantity": 350, "priority": "low",      "deadline_days": 20, "value_usd": 6000.0,  "status": "pending"},
        {"id": "ORD-224", "product": "Emergency Lighting",  "quantity": 250, "priority": "medium",   "deadline_days": 16, "value_usd": 7000.0,  "status": "pending"},
        {"id": "ORD-225", "product": "UPS Systems",         "quantity": 40,  "priority": "critical", "deadline_days": 7,  "value_usd": 48000.0, "status": "pending"},
        {"id": "ORD-226", "product": "Frequency Drives",    "quantity": 55,  "priority": "high",     "deadline_days": 10, "value_usd": 23000.0, "status": "pending"},
        {"id": "ORD-227", "product": "Isolation Valves",    "quantity": 180, "priority": "medium",   "deadline_days": 14, "value_usd": 8500.0,  "status": "pending"},
        {"id": "ORD-228", "product": "Servo Motors",        "quantity": 70,  "priority": "high",     "deadline_days": 9,  "value_usd": 27000.0, "status": "pending"},
        {"id": "ORD-229", "product": "Acoustic Panels",     "quantity": 300, "priority": "low",      "deadline_days": 25, "value_usd": 3500.0,  "status": "pending"},
        {"id": "ORD-230", "product": "Fire Suppression",    "quantity": 60,  "priority": "critical", "deadline_days": 6,  "value_usd": 50000.0, "status": "pending"},
    ],
    "routes": [
        {"id": "RT-020", "origin": "Vietnam",  "destination": "USA", "mode": "sea",  "transit_days": 18, "cost_per_unit": 2.0, "status": "blocked"},
        {"id": "RT-021", "origin": "Malaysia", "destination": "USA", "mode": "sea",  "transit_days": 20, "cost_per_unit": 2.2, "status": "blocked"},
        {"id": "RT-022", "origin": "Germany",  "destination": "USA", "mode": "sea",  "transit_days": 14, "cost_per_unit": 3.5, "status": "active"},
        {"id": "RT-023", "origin": "Mexico",   "destination": "USA", "mode": "land", "transit_days": 3,  "cost_per_unit": 1.5, "status": "active"},
        {"id": "RT-024", "origin": "Canada",   "destination": "USA", "mode": "land", "transit_days": 2,  "cost_per_unit": 1.8, "status": "active"},
        {"id": "RT-025", "origin": "Brazil",   "destination": "USA", "mode": "sea",  "transit_days": 12, "cost_per_unit": 2.8, "status": "active"},
        {"id": "RT-026", "origin": "Turkey",   "destination": "USA", "mode": "air",  "transit_days": 2,  "cost_per_unit": 9.5, "status": "active"},
        {"id": "RT-027", "origin": "USA",      "destination": "USA", "mode": "land", "transit_days": 1,  "cost_per_unit": 0.5, "status": "active"},
        {"id": "RT-028", "origin": "Vietnam",  "destination": "USA", "mode": "air",  "transit_days": 2,  "cost_per_unit": 10.0,"status": "active"},
    ],
    "disruptions": [
        {
            "id": "DIS-020",
            "type": "weather",
            "affected_entity": "SUP-H",
            "severity": 1.0,
            "description": "Typhoon Hana: All Vietnam operations suspended for 14 days.",
            "duration_days": 14,
        },
        {
            "id": "DIS-021",
            "type": "weather",
            "affected_entity": "SUP-I",
            "severity": 0.9,
            "description": "Typhoon Hana extends to Malaysia — operations at 10% capacity.",
            "duration_days": 12,
        },
        {
            "id": "DIS-022",
            "type": "supplier_down",
            "affected_entity": "SUP-J",
            "severity": 1.0,
            "description": "EuroHub GmbH declared insolvency. Permanently offline.",
            "duration_days": 99,
        },
        {
            "id": "DIS-023",
            "type": "strike",
            "affected_entity": "RT-020",
            "severity": 0.8,
            "description": "US East Coast dockworkers strike blocks sea freight arrivals.",
            "duration_days": 10,
        },
    ],
}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TASKS = {
    "task_1_easy":   TASK_1,
    "task_2_medium": TASK_2,
    "task_3_hard":   TASK_3,
}


def get_task(task_id: str) -> Dict[str, Any]:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS.keys())}")
    return TASKS[task_id]
