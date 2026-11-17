"""The six-month review. It adds approved answers to the library and reports what the team changed, won and lost.
No AI is used here, and no model is retrained: the agent gets better because its library gets better."""
from __future__ import annotations

import datetime as dt
import difflib

from . import guardrails as g
from .common import APPROVED, DATA, OUT, audit, read_json, write_json, write_text


def review(label: str | None = None) -> dict:
    lib = read_json(DATA / "library.json")
    packs = [read_json(p) for p in sorted(APPROVED.glob("*/pack.json"))]
    new = [p for p in packs if p["outcome"] and p["rfp_id"] not in lib["learned_packs"]]
    waiting = [p["rfp_id"] for p in packs if not p["outcome"]]
    n = len(lib["answers"])
    rows, added = [], 0
    for p in new:
        lib["bids"].append(dict(bid=p["rfp_id"], customer=p["customer"], industry="", date=p["created"][:10], outcome=p["outcome"]))
        for a in p["answers"]:
            change = 1 - difflib.SequenceMatcher(None, a["draft"], a["final"]).ratio()
            rows.append(dict(rfp=p["rfp_id"], outcome=p["outcome"], category=a["category"], label=a["label"], fit=a["fit"],
                             edited=a["edited"], change=change, reused=any(s["id"] in a["draft"] for s in a["sources"])))
            n, added = n + 1, added + 1
            lib["answers"].append(dict(id=f"L-{n:03d}", bid=p["rfp_id"], category=a["category"], question=a["requirement"], answer=g.strip_tags(a["final"])))
        lib["learned_packs"].append(p["rfp_id"])
    if new:
        lib["version"] += 1
        write_json(DATA / "library.json", lib)
    label = label or dt.date.today().strftime("%Y-%m")
    bids = lib["bids"]
    won = sum(b["outcome"] == "won" for b in bids)
    L = [f"# Six-month review: {label}", "", "Built by code from approved submissions. No AI wrote this report.", "",
         f"- Submissions learned from in this review: {len(new)}" + (f" ({', '.join(p['rfp_id'] for p in new)})" if new else ""),
         f"- Approved submissions still waiting for a result: {len(waiting)}" + (f" ({', '.join(waiting)})" if waiting else ""),
         f"- Answers added to the library: {added}. The library is now version {lib['version']} with {len(lib['answers'])} answers.",
         f"- All bids on record: {len(bids)}, of which {won} won.", ""]
    if rows:
        edited = [r for r in rows if r["edited"]]
        L += ["## What the team changed", "", f"- Answers the team edited before approving: {len(edited)} of {len(rows)}.",
              f"- Drafts that reused a past answer: {sum(r['reused'] for r in rows)} of {len(rows)}.", ""]
        if edited:
            L += ["| Topic | Submission | How much changed |", "|---|---|---|"]
            L += [f"| {r['label']} | {r['rfp']} | {round(r['change'] * 100)}% |" for r in sorted(edited, key=lambda r: -r["change"])]
            L += ["", "Topics the team rewrites heavily are the library answers to improve first.", ""]
        gaps = sorted({(r["label"], r["rfp"], r["outcome"]) for r in rows if r["fit"] == "GAP"})
        L += ["## Requirements we could not meet", ""] + ([f"- {a} ({b}, {c})" for a, b, c in gaps] or ["- None."])
        L += ["", "Gaps that keep appearing, above all in bids we lost, are worth raising with the product team.", ""]
    else:
        L += ["Nothing new to learn from yet. Approve a submission and record whether it was won or lost, then run this again.", ""]
    L += ["## A caution", "", "With only a few submissions these figures are a guide, not proof. A lost bid has many causes, and most are not in the document."]
    report = "\n".join(L) + "\n"
    write_text(OUT / f"learning_review_{label}.md", report)
    audit("review", label=label, learned=len(new), answers_added=added, library_version=lib["version"])
    return dict(label=label, learned=len(new), added=added, version=lib["version"], report=report)
