#!/usr/bin/env python3
"""A simple, honest time model. Every input is in assumptions.toml. Nothing here is a measured result."""
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
a = tomllib.load(open(ROOT / "assumptions.toml", "rb"))
year1_hours = a["setup_hours"] + a["upkeep_hours_per_year"] + a["review_hours_per_year"]
out = {}
print(f"{'':28}{'Low':>12}{'Base':>12}{'High':>12}")
rows = {"RFPs a year": [], "Hours saved a year": [], "Value of hours saved ($)": [], "Year-1 cost of own time ($)": [], "Net, year 1 ($)": []}
for case in ("low", "base", "high"):
    c = a[case]
    saved = c["rfps_per_year"] * a["hours_per_rfp"] * c["share_of_hours_spent_drafting"] * c["share_of_drafting_saved"]
    value, cost = saved * a["hourly_cost"], year1_hours * a["hourly_cost"]
    out[case] = dict(rfps=c["rfps_per_year"], hours_saved=round(saved), value=round(value), cost=round(cost), net=round(value - cost))
    for k, v in zip(rows, [c["rfps_per_year"], round(saved), round(value), round(cost), round(value - cost)]):
        rows[k].append(v)
for k, v in rows.items():
    print(f"{k:28}" + "".join(f"{x:>12,}" for x in v))
b = a["base"]
per_rfp = a["hours_per_rfp"] * b["share_of_hours_spent_drafting"] * b["share_of_drafting_saved"]
out["hours_saved_per_rfp_base"] = round(per_rfp, 1)
out["break_even_rfps_per_year_base"] = round(year1_hours / per_rfp, 1)
print(f"\nAt base assumptions the agent saves about {per_rfp:.1f} hours per RFP and covers its year-1 time at about {year1_hours / per_rfp:.0f} RFPs a year.")
print("Licence cost is nil (open-source tools). The cost is people's time and a workstation you already own.")
(ROOT / "output").mkdir(exist_ok=True)
json.dump(out, open(ROOT / "output" / "value_model.json", "w"), indent=2)
