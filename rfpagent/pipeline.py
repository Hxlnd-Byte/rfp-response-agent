"""The agent's steps, in order. The AI reads and writes. Code retrieves, compares and checks. People approve.

  1 read the RFP          code splits it into requirements; the AI says what each one is about
  2 position              code looks the topic up in the product catalogue and sets the fit (the AI cannot change it)
  3 reuse                 code finds the best past answers (retrieval); the AI drafts from them
  4 competition           the AI pulls claims from web pages; code keeps only claims whose quote is really in the page
  5 customer              the same, for what the customer has said in public
  6 pack                  code builds the draft response and two internal briefs, and runs the checks
  7 approval              two people sign. Nothing is sent by this tool.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from . import guardrails as g
from . import retrieval, web
from .common import (APPROVED, DATA, FIT, PENDING, Budget, Stop, audit, cfg, norm, ollama_json, read_json, today,
                     write_json, write_text)

REQ = re.compile(r"^\s*((?:R-\d+)|(?:\d+(?:\.\d+)+))[\s.:)\-]+(.{25,})$")
VERB = re.compile(r"\b(shall|must|should|describe|provide|explain|state|confirm|list)\b", re.I)
ORDER = {"STRONG": 0, "PARTIAL": 1, "GAP": 2}
COMPLIANCE = {"STRONG": "Meets the requirement", "PARTIAL": "Partly meets the requirement", "GAP": "Does not meet the requirement today"}


# ---------- 1. read the RFP ----------
def read_rfp_file(path: Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".docx":  # a Word file is a zip of XML; no extra software needed
        import zipfile
        xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
        return re.sub(r"<[^>]+>", "", xml.replace("</w:p>", "\n"))
    if path.suffix.lower() == ".pdf":
        try:
            import pymupdf
        except ImportError:
            raise RuntimeError("To read PDF files, run: pip install pymupdf  (or save the RFP as .txt or .docx)")
        with pymupdf.open(path) as d:
            return "\n".join(p.get_text() for p in d)
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_rfp(text: str, fallback_id: str = "RFP") -> dict:
    """Header facts and numbered requirements are found by code, not by the AI."""
    get = lambda pat: (re.search(pat, text, re.I) or [None, None])[1]
    reqs = []
    for line in text.splitlines():
        m = REQ.match(line)
        if m and VERB.search(m[2]):
            reqs.append(dict(id=m[1], text=m[2].strip()))
    rid = (get(r"RFP reference:\s*([\w-]+)") or fallback_id)
    return dict(rfp_id=re.sub(r"[^\w-]", "_", rid), customer=(get(r"Issued by:\s*(.+)") or "the customer").strip(),
                due=(get(r"Response due:\s*([\d-]+)") or ""), requirements=reqs)


def world() -> dict:
    lib = read_json(DATA / "library.json")
    comp = read_json(DATA / "company.json")
    return dict(tax=read_json(DATA / "taxonomy.json"), catalog=read_json(DATA / "catalog.json"), library=lib, company=comp,
                past_customers=[b["customer"] for b in lib["bids"]])


def truth() -> dict | None:
    p = DATA / "truth" / "truth.json"
    return read_json(p) if p.exists() else None


def by_keywords(text: str, w: dict) -> str:
    """No-AI fallback: pick the topic whose catalogue wording is closest."""
    docs = [t["label"] + " " + " ".join(c["text"] for c in w["catalog"] if c["category"] == t["code"]) for t in w["tax"]]
    return retrieval.best(w["tax"], docs, text)["code"]


def classify(reqs, mode, w, c, budget, key) -> dict:
    codes = [t["code"] for t in w["tax"]]
    known = {r["id"]: r["category"] for r in (key or {}).get("requirements", [])}
    out = {}
    for i, r in enumerate(reqs):
        budget.check()
        if mode == "ollama":
            menu = "\n".join(f"- {t['code']}: {t['label']}" for t in w["tax"])
            reply = ollama_json(c, budget, "You sort requirements from a request for proposal into topics.\n"
                                f"Topics:\n{menu}\n\nRequirement: {r['text']}\n\nChoose the one topic that fits best.",
                                {"type": "object", "properties": {"category": {"type": "string", "enum": codes}}, "required": ["category"]})
            out[r["id"]] = reply["category"]
        else:
            cat = known.get(r["id"]) or by_keywords(r["text"], w)
            if mode == "noisy_mock" and i % 7 == 3:  # a deliberate misreading, to prove the scoring notices
                cat = codes[(codes.index(cat) + 5) % len(codes)]
            out[r["id"]] = cat
    return out


# ---------- 2. position ----------
def position(req_text: str, category: str, w: dict) -> dict:
    caps = [x for x in w["catalog"] if x["category"] == category]
    cap = retrieval.best(caps, [x["text"] + " " + x["note"] for x in caps], req_text)
    if cap is None:
        cap = dict(id="C-none", product="", category=category, status="not_offered", text="Nothing in the catalogue covers this.", note="")
    return cap


# ---------- 3. reuse and draft ----------
def clean_source(answer: str, past_customers: list[str]) -> str:
    """Remove any sentence that names an old customer before the AI ever sees it."""
    keep = [s for s in re.split(r"(?<=[.!?])\s+", answer) if not any(p.lower() in s.lower() for p in past_customers)]
    return " ".join(keep)


def template_answer(cap: dict, fit: str, sources: list[dict]) -> str:
    extra = ""
    same = [s for s in sources if s["category"] == cap["category"]]
    if same:
        first = [x for x in re.split(r"(?<=[.!?])\s+", same[0]["answer"]) if norm(x) not in norm(cap["text"])]
        extra = (" " + " ".join(first[:2]) + f" [{same[0]['id']}]") if first else ""
    if fit == "GAP":
        return f"Vantora does not offer this today. {cap['text']} {cap['note']} [{cap['id']}]".replace("  ", " ")
    if fit == "PARTIAL":
        return f"{cap['text']} {cap['note']} [{cap['id']}]{extra}"
    return f"{cap['text']} [{cap['id']}]{extra}"


def draft_answer(req, cap, fit, sources, mode, w, c, budget, blocked) -> dict:
    kw = dict(fit=fit, capability=cap, sources=sources, requirement=req["text"], blocked_names=blocked,
              max_words=c["agent"]["max_words_per_answer"])
    if mode != "ollama":
        text = template_answer(cap, fit, sources)
        if mode == "noisy_mock" and req["id"].endswith("3"):   # planted faults, to prove the checks notice
            text += " This is proven at Harrowgate Mutual Bank, with 99 percent of alerts handled."
        return dict(text=text, violations=g.check_answer(text, **kw), attempts=1)
    src = "\n".join(f"[{s['id']}] {s['answer']}" for s in sources) or "(none)"
    base = ("You write one answer for a proposal. Use ONLY the facts below. Do not add numbers, names or promises.\n"
            f"Our position on this requirement is fixed: {COMPLIANCE[fit]}. Do not claim more than that.\n"
            + ("Say plainly that this is not offered today, then say what we can do instead.\n" if fit == "GAP" else "")
            + f"\nRequirement: {req['text']}\n\nProduct fact [{cap['id']}]: {cap['text']} {cap['note']}\n\nPast answers you may reuse:\n{src}\n\n"
            f"Write at most 120 words in plain English. Put [{cap['id']}] after the product fact you use, and the past answer's tag "
            "(for example [L-001]) after anything you reuse from it.")
    violations, text = [], ""
    for attempt in range(1, c["agent"]["max_retries_per_answer"] + 2):
        fix = ("\n\nYour last draft had these problems. Fix them:\n- " + "\n- ".join(violations)) if violations else ""
        text = ollama_json(c, budget, base + fix, {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]})["answer"].strip()
        violations = g.check_answer(text, **kw)
        if not violations:
            break
    return dict(text=text, violations=violations, attempts=attempt)


# ---------- 4 and 5. competition and customer ----------
def extract(entity, pages, kind, mode, w, c, budget, key) -> tuple[list[dict], list[dict]]:
    """Returns (kept, blocked). A statement is kept only if its quote is really in the page it cites."""
    codes = [t["code"] for t in w["tax"]]
    by_id = {p["id"]: p for p in pages}
    raw = []
    if mode == "ollama":
        menu = "\n".join(f"- {t['code']}: {t['label']}" for t in w["tax"])
        for p in pages:
            budget.check()
            if kind == "competitor":
                ask = (f"Below is a web page about {entity}, a supplier. List what the page says {entity}'s product does well (strength) "
                       "or does badly or lacks (weakness), only for the topics listed.")
                item = {"type": "object", "properties": {"category": {"type": "string", "enum": codes}, "stance": {"type": "string", "enum": ["strength", "weakness"]},
                                                         "quote": {"type": "string"}}, "required": ["category", "stance", "quote"]}
            else:
                ask = (f"Below is a public web page about {entity}, an organisation. List what the page says about its priorities, plans, "
                       "limits or problems, only for the topics listed. For 'role' give a job title or the kind of document (for example "
                       "'Chief Information Officer' or 'Annual report'). Never give a person's name.")
                item = {"type": "object", "properties": {"category": {"type": "string", "enum": codes}, "role": {"type": "string"},
                                                         "quote": {"type": "string"}}, "required": ["category", "role", "quote"]}
            reply = ollama_json(c, budget, f"{ask}\nFor each one, copy a short quote (under 25 words) EXACTLY as written on the page. "
                                f"If the page says nothing relevant, return an empty list. Do not guess.\n\nTopics:\n{menu}\n\nPage:\n{p['text']}",
                                {"type": "object", "properties": {"items": {"type": "array", "items": item}}, "required": ["items"]})
            raw += [dict(x, source=p["id"], entity=entity) for x in reply.get("items", [])]
    elif key:
        pool = key["claims"] if kind == "competitor" else key["priorities"]
        raw = [dict(x, entity=entity) for x in pool if x["source"] in by_id and (kind == "customer" or x["entity"] == entity)]
        if mode == "noisy_mock" and raw:
            raw = raw[1:] + [dict(raw[0], category=codes[0], quote="offers a mobile app and medical device monitoring at no extra cost")]
    kept, blocked = [], []
    for x in raw:
        p = by_id.get(x["source"])
        row = dict(x, url=p["url"] if p else "", title=p["title"] if p else "", date=p["date"] if p else "")
        (kept if p and g.verify_quote(x["quote"], p["text"]) else blocked).append(row)
    return kept, blocked


def build_grid(cats, fit_by_cat, claims, w) -> list[dict]:
    label = {t["code"]: t["label"] for t in w["tax"]}
    rows = []
    for cat in cats:
        ours = fit_by_cat[cat]
        s = [x for x in claims if x["category"] == cat and x["stance"] == "strength"]
        k = [x for x in claims if x["category"] == cat and x["stance"] == "weakness"]
        if ours == "STRONG" and k:
            pos = "Press our advantage"
        elif ours != "STRONG" and s:
            pos = "We are vulnerable"
        elif ours == "STRONG" and s:
            pos = "Even: win on the outcome"
        elif ours != "STRONG":
            pos = "Our weak spot (no competitor evidence found)"
        else:
            pos = "No competitor evidence found"
        rows.append(dict(category=cat, label=label[cat], ours=ours, position=pos, strengths=s, weaknesses=k))
    return rows


def talking_points(grid, priorities, in_rfp, caps_by_cat, customer) -> list[dict]:
    """Code builds the facts of each point, so every point carries its sources."""
    pts = []
    said = {p["category"]: p for p in priorities}
    for p in priorities:
        cap = caps_by_cat.get(p["category"])
        if p["category"] not in in_rfp and cap and FIT[cap["status"]] == "STRONG":
            pts.append(dict(kind="Overlooked by the RFP", text=f"The RFP does not ask about {cap_label(grid, p['category'])}, but {customer} has said: "
                            f"\"{p['quote']}\" [{p['source']}]. Open this conversation: {cap['text']} [{cap['id']}]"))
    for row in grid:
        cap = caps_by_cat.get(row["category"])
        if row["position"] == "We are vulnerable" and cap:
            x = row["strengths"][0]
            pts.append(dict(kind="Be upfront", text=f"On {low(row['label'])}, {x['entity']} says: \"{x['quote']}\" [{x['source']}]. "
                            f"Our position: {cap['text']} {cap['note']} [{cap['id']}] Raise it ourselves before they do, and say how we would cover it."))
    press = sorted([r for r in grid if r["position"] == "Press our advantage"], key=lambda r: r["category"] not in said)
    for row in press:
        cap, x = caps_by_cat.get(row["category"]), row["weaknesses"][0]
        why = f" This matters here because {customer} has said: \"{said[row['category']]['quote']}\" [{said[row['category']]['source']}]." if row["category"] in said else ""
        pts.append(dict(kind="Our strength", text=f"On {low(row['label'])}, we meet the requirement: {cap['text']} [{cap['id']}] "
                        f"Evidence about {x['entity']}: \"{x['quote']}\" [{x['source']}].{why} Ask how the customer would handle this with a tool that cannot."))
    return pts[:14]


def low(label: str) -> str:
    return label[:1].lower() + label[1:] if not label[:2].isupper() else label


def cap_label(grid, cat):
    return next((low(r["label"]) for r in grid if r["category"] == cat), cat.lower())


# ---------- 6. the pack ----------
def response_markdown(pack: dict) -> str:
    L = [f"# Response to {pack['rfp_id']}", "", f"Prepared for {pack['customer']} by {pack['vendor']}.", "",
         f"**Status: {pack['status']}.** This is a draft prepared by an AI agent from approved company material. "
         "It must not be sent until it has been approved by the technical consultant and the account lead.", "", "## Summary of compliance", "",
         "| Requirement | Our position |", "|---|---|"]
    L += [f"| {a['req_id']} | {COMPLIANCE[a['fit']]} |" for a in pack["answers"]]
    L += ["", "## Answers", ""]
    for a in pack["answers"]:
        L += [f"### {a['req_id']}  {a['requirement']}", "", f"**{COMPLIANCE[a['fit']]}.** {g.strip_tags(a['final'])}", ""]
    if pack["value_adds"]:
        L += ["## Beyond the requirements", "", "The RFP did not ask about the points below. We raise them because of what your organisation has said in public.", ""]
        L += [f"- {g.strip_tags(v['customer_text'])}" for v in pack["value_adds"]] + [""]
    return "\n".join(L)


def briefs_markdown(pack: dict) -> tuple[str, str]:
    head = "**INTERNAL. Not for the customer.** Every statement carries a source in square brackets. Check a source before you repeat a claim.\n"
    C = [f"# Competitive brief: {pack['rfp_id']}", "", head, "## Where we stand, topic by topic", "", "| Topic | Us | Position | Evidence |", "|---|---|---|---|"]
    for r in pack["grid"]:
        ev = "; ".join(f"{x['entity']} ({x['stance']}) [{x['source']}]" for x in r["strengths"] + r["weaknesses"]) or "none found"
        C.append(f"| {r['label']} | {r['ours']} | {r['position']} | {ev} |")
    C += ["", "## Talking points", ""] + [f"- **{p['kind']}.** {p['text']}" for p in pack["talking_points"]]
    C += ["", "## Evidence", ""] + [f"- [{x['source']}] {x['entity']}, {x['stance']}: \"{x['quote']}\" ({x['title']}, {x['date']}) {x['url']}" for x in pack["claims"]]
    C += ["", f"Statements removed because the quote was not found in the page cited: {len(pack['blocked'])}."]
    K = [f"# Customer brief: {pack['customer']}", "", head, "Only public, professional statements are used: press releases, reports, talks and job adverts. "
         "People are described by role, not by name.", "", "## What the customer has said", ""]
    K += [f"- **{p['label']}** ({p['relation']}). \"{p['quote']}\" ({p['role']}, {p['date']}) [{p['source']}] {p['url']}" for p in pack["priorities"]]
    K += ["", "## Consider adding to the submission", ""] + ([f"- {v['internal_text']}" for v in pack["value_adds"]] or ["- Nothing found."])
    K += ["", "## Handle with care", ""] + ([f"- {a}" for a in pack["avoid"]] or ["- Nothing found."])
    return "\n".join(C) + "\n", "\n".join(K) + "\n"


def save_pack(pack: dict):
    folder = (APPROVED if pack["status"] == "APPROVED" else PENDING) / pack["rfp_id"]
    write_json(folder / "pack.json", pack)
    write_text(folder / ("response_final.md" if pack["status"] == "APPROVED" else "response_draft.md"), response_markdown(pack))
    comp, cust = briefs_markdown(pack)
    write_text(folder / "competitive_brief_INTERNAL.md", comp)
    write_text(folder / "customer_brief_INTERNAL.md", cust)


def run(rfp_path, mode: str = "ollama") -> dict:
    c, w = cfg(), world()
    budget = Budget(c)
    budget.check()
    key = truth() if mode != "ollama" else None
    rfp = parse_rfp(read_rfp_file(rfp_path), Path(rfp_path).stem)
    if not rfp["requirements"]:
        raise ValueError("No numbered requirements were found in this document.")
    if (APPROVED / rfp["rfp_id"]).exists():
        raise ValueError(f"{rfp['rfp_id']} has already been approved. Approved packs are not overwritten.")
    audit("run_start", rfp=rfp["rfp_id"], mode=mode, model=c["ollama"]["model"] if mode == "ollama" else "none")
    day = today(c)
    label = {t["code"]: t["label"] for t in w["tax"]}
    blocked_names = w["company"]["competitors"] + w["past_customers"]

    cats = classify(rfp["requirements"], mode, w, c, budget, key)
    answers = []
    for r in rfp["requirements"]:
        cap = position(r["text"], cats[r["id"]], w)
        fit = FIT[cap["status"]]
        found = retrieval.past_answers(w["library"], r["text"] + " " + label[cats[r["id"]]], day, c)
        sources = [dict(s, answer=clean_source(s["answer"], w["past_customers"])) for s in found]
        d = draft_answer(r, cap, fit, sources, mode, w, c, budget, blocked_names)
        answers.append(dict(req_id=r["id"], requirement=r["text"], category=cats[r["id"]], label=label[cats[r["id"]]], fit=fit,
                            capability=cap, sources=sources, draft=d["text"], final=d["text"], violations=d["violations"],
                            attempts=d["attempts"], edited=False))

    claims, blocked = [], []
    for comp in w["company"]["competitors"]:
        k, b = extract(comp, web.search(comp, "competitor", c), "competitor", mode, w, c, budget, key)
        claims += k
        blocked += b
    pk, pb = extract(rfp["customer"], web.search(rfp["customer"], "customer", c), "customer", mode, w, c, budget, key)
    blocked += pb

    in_rfp = {}
    for a in answers:
        in_rfp.setdefault(a["category"], []).append(a["req_id"])
    fit_by_cat, caps_by_cat = {}, {}
    for a in answers:
        if a["category"] not in fit_by_cat or ORDER[a["fit"]] < ORDER[fit_by_cat[a["category"]]]:
            fit_by_cat[a["category"]], caps_by_cat[a["category"]] = a["fit"], a["capability"]
    for p in pk:
        if p["category"] not in fit_by_cat:
            caps = sorted([x for x in w["catalog"] if x["category"] == p["category"]], key=lambda x: ORDER[FIT[x["status"]]])
            if caps:
                fit_by_cat[p["category"]], caps_by_cat[p["category"]] = FIT[caps[0]["status"]], caps[0]
    grid = build_grid(list(fit_by_cat), fit_by_cat, claims, w)

    priorities, value_adds, avoid = [], [], []
    for p in pk:
        cat, cap = p["category"], caps_by_cat.get(p["category"])
        ours = fit_by_cat.get(cat, "GAP")
        relation = f"covered by {', '.join(in_rfp[cat])}" if cat in in_rfp else "not in the RFP"
        priorities.append(dict(p, label=label[cat], relation=relation, ours=ours))
        if cat not in in_rfp and cap and ours == "STRONG":
            value_adds.append(dict(category=cat,
                                   internal_text=f"{label[cat]}: the customer said \"{p['quote']}\" [{p['source']}] and the RFP does not ask about it. We can offer: {cap['text']} [{cap['id']}]",
                                   customer_text=f"{label[cat]}. Your organisation has said publicly: \"{p['quote']}\". {cap['text']}"))
        if ours == "GAP" and cap:
            avoid.append(f"Do not overclaim on {low(label[cat])}. The customer said \"{p['quote']}\" [{p['source']}], and we do not offer this: {cap['text']} {cap['note']} [{cap['id']}] Say so plainly and propose a partner.")
        if cat == "AI_EXPLAINABILITY":
            avoid.append(f"Avoid 'trust the AI' wording. The customer said \"{p['quote']}\" [{p['source']}]. Lead with how each decision is explained.")
    points = talking_points(grid, priorities, in_rfp, caps_by_cat, rfp["customer"])
    known = {x["id"] for x in w["catalog"]} | {x["source"] for x in claims + pk}
    for p in points:
        p["violations"] = g.check_point(p["text"], known)

    pack = dict(rfp_id=rfp["rfp_id"], customer=rfp["customer"], due=rfp["due"], vendor=w["company"]["vendor"], mode=mode,
                is_mock=mode != "ollama", model=c["ollama"]["model"] if mode == "ollama" else None, created=dt.datetime.now().isoformat(timespec="seconds"),
                status="PENDING_APPROVAL", approvals={}, outcome=None, ai_calls=budget.used, web_mode=c["web"]["mode"],
                answers=answers, claims=claims, blocked=blocked, grid=grid, priorities=priorities, value_adds=value_adds, avoid=avoid, talking_points=points)
    save_pack(pack)
    audit("run_end", rfp=rfp["rfp_id"], answers=len(answers), failing=sum(bool(a["violations"]) for a in answers),
          claims_kept=len(claims) + len(pk), claims_blocked=len(blocked), ai_calls=budget.used)
    return pack


# ---------- 7. approval ----------
def load_pack(rfp_id: str) -> dict:
    for folder in (PENDING, APPROVED):
        if (folder / rfp_id / "pack.json").exists():
            return read_json(folder / rfp_id / "pack.json")
    raise FileNotFoundError(f"No pack called {rfp_id}")


def list_packs() -> list[dict]:
    out = []
    for folder in (PENDING, APPROVED):
        for p in sorted(folder.glob("*/pack.json")):
            out.append(read_json(p))
    return out


def edit_answer(rfp_id: str, req_id: str, text: str, who: str) -> list[str]:
    pack, w, c = load_pack(rfp_id), world(), cfg()
    if pack["status"] == "APPROVED":
        raise ValueError("This pack is approved and can no longer be edited.")
    a = next(x for x in pack["answers"] if x["req_id"] == req_id)
    a["final"], a["edited"] = text.strip(), True
    a["violations"] = g.check_answer(a["final"], fit=a["fit"], capability=a["capability"], sources=a["sources"], requirement=a["requirement"],
                                     blocked_names=w["company"]["competitors"] + w["past_customers"], max_words=c["agent"]["max_words_per_answer"])
    pack["approvals"] = {}  # any edit clears earlier sign-offs
    save_pack(pack)
    audit("answer_edited", rfp=rfp_id, req=req_id, by=who, passes=not a["violations"])
    return a["violations"]


def approve(rfp_id: str, role: str, name: str) -> dict:
    pack, c = load_pack(rfp_id), cfg()
    roles = c["approval"]["roles"]
    name = name.strip()
    if pack["status"] == "APPROVED":
        raise ValueError("Already approved.")
    if role not in roles:
        raise ValueError(f"Role must be one of: {', '.join(roles)}")
    if not name:
        raise ValueError("A name is needed to sign.")
    failing = [a["req_id"] for a in pack["answers"] if a["violations"]]
    if failing:
        raise ValueError(f"These answers fail their checks and must be fixed first: {', '.join(failing)}")
    if any(v["name"].lower() == name.lower() for r, v in pack["approvals"].items() if r != role):
        raise ValueError("The two sign-offs must come from two different people.")
    pack["approvals"][role] = dict(name=name, time=dt.datetime.now().isoformat(timespec="seconds"))
    audit("signed", rfp=rfp_id, role=role, by=name)
    if all(r in pack["approvals"] for r in roles):
        pack["status"] = "APPROVED"
        save_pack(pack)
        import shutil
        shutil.rmtree(PENDING / rfp_id, ignore_errors=True)
        audit("approved", rfp=rfp_id)
    else:
        save_pack(pack)
    return pack


def set_outcome(rfp_id: str, outcome: str) -> dict:
    pack = load_pack(rfp_id)
    if pack["status"] != "APPROVED":
        raise ValueError("Only an approved submission can have a result.")
    if outcome not in ("won", "lost"):
        raise ValueError("Result must be won or lost.")
    pack["outcome"] = outcome
    save_pack(pack)
    audit("outcome", rfp=rfp_id, outcome=outcome)
    return pack
