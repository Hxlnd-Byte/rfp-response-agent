"""Marks the agent's work against the answer key for the invented test. Only meaningful for the demo RFP."""
from __future__ import annotations

from . import pipeline
from .common import OUT, norm, write_json, write_text
from . import guardrails as g


def score(rfp_id: str) -> dict:
    pack, key, w = pipeline.load_pack(rfp_id), pipeline.truth(), pipeline.world()
    t = {r["id"]: r for r in key["requirements"]}
    ans = [a for a in pack["answers"] if a["req_id"] in t]
    n = len(ans) or 1
    cat_ok = sum(a["category"] == t[a["req_id"]]["category"] for a in ans)
    fit_ok = sum(a["fit"] == t[a["req_id"]]["fit"] for a in ans)
    cap_ok = sum(a["capability"]["id"] == t[a["req_id"]]["capability"] for a in ans)
    hit = sum(any(s["category"] == t[a["req_id"]]["category"] for s in a["sources"]) for a in ans)
    want = {(c["entity"], c["category"], norm(c["quote"])) for c in key["claims"]}
    got = {(c["entity"], c["category"], norm(c["quote"])) for c in pack["claims"]}
    pwant = {(p["category"], norm(p["quote"])) for p in key["priorities"]}
    pgot = {(p["category"], norm(p["quote"])) for p in pack["priorities"]}
    names = w["company"]["competitors"] + w["past_customers"]
    doc = pipeline.response_markdown(pack).lower()
    passing = [a for a in pack["answers"] if not a["violations"]]
    leaks = sorted({nm for a in passing for nm in names if nm.lower() in g.strip_tags(a["final"]).lower()})
    s = dict(rfp_id=rfp_id, mode=pack["mode"], is_mock=pack["is_mock"], model=pack["model"], requirements=len(ans),
             topic_correct=cat_ok, fit_correct=fit_ok, capability_correct=cap_ok, past_answer_found=hit,
             answers_passing_checks=len(passing), answers_failing_checks=len(pack["answers"]) - len(passing),
             competitor_claims_expected=len(want), competitor_claims_found=len(want & got), competitor_claims_wrong=len(got - want),
             customer_statements_expected=len(pwant), customer_statements_found=len(pwant & pgot), customer_statements_wrong=len(pgot - pwant),
             statements_blocked_quote_not_in_source=len(pack["blocked"]), names_leaked_in_passing_answers=leaks,
             talking_points=len(pack["talking_points"]), talking_points_without_valid_source=sum(bool(p["violations"]) for p in pack["talking_points"]),
             ai_calls=pack["ai_calls"])
    banner = "**MOCK RUN: a stand-in was used, not an AI model. These figures test the plumbing and the checks, not the AI.**\n\n" if pack["is_mock"] else f"Model: {pack['model']}\n\n"
    rows = [("Requirements sorted into the right topic", f"{cat_ok} of {n}"), ("Right catalogue entry chosen", f"{cap_ok} of {n}"),
            ("Fit (meets / partly / gap) correct", f"{fit_ok} of {n}"), ("A relevant past answer found in the top 3", f"{hit} of {n}"),
            ("Draft answers passing every check", f"{s['answers_passing_checks']} of {len(pack['answers'])}"),
            ("Competitor claims found, with a verified quote", f"{s['competitor_claims_found']} of {len(want)}"),
            ("Customer statements found, with a verified quote", f"{s['customer_statements_found']} of {len(pwant)}"),
            ("Statements removed: quote not in the page cited", str(len(pack["blocked"]))),
            ("Competitor or old-customer names in passing answers", str(len(leaks))),
            ("Talking points without a valid source", str(s["talking_points_without_valid_source"])), ("AI calls used", str(pack["ai_calls"]))]
    write_json(OUT / "results_summary.json", s)
    write_text(OUT / "report.md", f"# Test results: {rfp_id}\n\n{banner}| Measure | Result |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows) + "\n")
    return s
