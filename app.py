#!/usr/bin/env python3
"""The browser screen. Start it, then open http://localhost:8765 . Everything is done with buttons.

  python app.py

It listens on this computer only. It needs no extra Python packages, and loads nothing from the internet.
"""
import sys

if sys.version_info < (3, 11):
    sys.exit("This tool needs Python 3.11 or newer. You have " + sys.version.split()[0] + ". Install a newer Python from python.org.")
import html
import os
import re
import urllib.parse
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from rfpagent import catalog, charts, learn, pipeline, score
from rfpagent.common import DATA, FIT, OUT, Stop, cfg, read_json, write_json

E = lambda s: html.escape(str(s if s is not None else ""))
VIOLET, SKY, TEAL, GREEN, SUN, CORAL, INK, MUTED = "#6c4cf1", "#2d9cdb", "#12b5a6", "#1fb97a", "#f59e0b", "#ff5c7a", "#1b1f3b", "#6b7190"
FITC = {"STRONG": GREEN, "PARTIAL": SUN, "GAP": CORAL}
FITW = {"STRONG": "We meet it", "PARTIAL": "We partly meet it", "GAP": "We do not offer it"}
POSC = {"Press": GREEN, "We are": CORAL, "Even": SKY, "Our weak": SUN, "No comp": "#a3a8c3"}
KINDC = {"Overlooked by the RFP": VIOLET, "Be upfront": CORAL, "Our strength": GREEN}
ALLOWED = (".txt", ".md", ".docx", ".pdf")
ICON = {  # simple line icons, drawn here so nothing is downloaded
    "home": "M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z", "fit": "M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18zm-4-9l3 3 5-6",
    "comp": "M4 20V10m6 10V4m6 16v-7m4 7H2", "cust": "M4 5h16v11H9l-5 4z", "draft": "M4 20h4L19 9l-4-4L4 16zM14 6l4 4",
    "catalog": "M3 8l9-5 9 5v8l-9 5-9-5zm0 0l9 5 9-5m-9 5v8", "learn": "M4 12a8 8 0 0 1 14-5l2-2v6h-6l2-2a5 5 0 1 0 1 6",
    "up": "M12 16V5m0 0l-4 4m4-4l4 4M5 19h14", "check": "M5 12l5 5 9-10"}
TABS = [("home", "Start"), ("fit", "Our fit"), ("comp", "Competition"), ("cust", "Customer"), ("draft", "Approve"), ("catalog", "Products"), ("learn", "Learn")]
CSS = """
*{box-sizing:border-box}body{font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif;margin:0;background:#f6f7fd;color:#1b1f3b;font-size:15px;line-height:1.5}
a{color:#6c4cf1}header{background:linear-gradient(120deg,#6c4cf1 0%,#2d9cdb 55%,#12b5a6 100%);color:#fff;padding:18px 32px 62px}
header h1{margin:0;font-size:22px;letter-spacing:.2px}header p{margin:2px 0 0;opacity:.9;font-size:14px}
nav{max-width:1180px;margin:-34px auto 0;padding:0 24px;display:flex;gap:8px;flex-wrap:wrap}
nav a{display:flex;align-items:center;gap:8px;background:#fff;color:#4a5073;text-decoration:none;font-weight:600;padding:11px 16px;border-radius:14px;box-shadow:0 4px 14px rgba(40,44,90,.10)}
nav a.on{background:#1b1f3b;color:#fff}nav a svg,.btn svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
main{max-width:1180px;margin:0 auto;padding:22px 24px 60px}.card{background:#fff;border-radius:18px;padding:20px 22px;margin:16px 0;box-shadow:0 2px 10px rgba(40,44,90,.06)}
.grid{display:grid;gap:16px}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}@media(max-width:900px){.g2,.g3,.g4{grid-template-columns:1fr}}
h2{font-size:19px;margin:0 0 6px}h3{font-size:15.5px;margin:0 0 4px}.muted{color:#6b7190;font-size:13.5px}.pill{display:inline-block;color:#fff;border-radius:999px;padding:3px 11px;font-size:12.5px;font-weight:600;white-space:nowrap}
.chip{display:inline-block;background:#eef0fa;color:#4a5073;border-radius:999px;padding:2px 10px;font-size:12.5px;margin:2px 4px 2px 0}
.btn,button{display:inline-flex;align-items:center;gap:8px;background:#6c4cf1;color:#fff;border:0;border-radius:12px;padding:10px 16px;font-size:14.5px;font-weight:600;cursor:pointer;text-decoration:none;font-family:inherit;white-space:nowrap}
.btn:hover,button:hover{filter:brightness(1.08)}.teal{background:#12b5a6}.ghost{background:#eef0fa;color:#4a5073}.coral{background:#ff5c7a}.small{padding:6px 12px;font-size:13px;border-radius:10px}
input[type=text],select,textarea{font:inherit;font-size:14px;padding:9px 11px;border:1.5px solid #dfe2f1;border-radius:11px;background:#fff;color:#1b1f3b}textarea{width:100%}input:focus,textarea:focus,select:focus{outline:none;border-color:#6c4cf1}
.next{display:flex;align-items:center;gap:14px;background:#1b1f3b;color:#fff;border-radius:18px;padding:14px 20px;margin:16px 0}.next b{color:#ffd166}.next .btn{margin-left:auto;background:#ffd166;color:#1b1f3b}
.msg{background:#e9fbf4;border-left:5px solid #1fb97a;border-radius:12px;padding:11px 16px;margin:14px 0}.warn{background:#fff1f4;border-left-color:#ff5c7a}
.mock{background:#fff7e6;border:1.5px dashed #f59e0b;border-radius:12px;padding:8px 14px;margin:14px 0;font-size:13.5px}
.steps{display:flex;gap:6px;margin:16px 0;flex-wrap:wrap}.step{flex:1;min-width:120px;background:#fff;border-radius:14px;padding:10px 12px;font-size:13px;color:#6b7190;border:2px solid transparent}
.step b{display:block;color:#1b1f3b;font-size:14px}.step.done{background:#e9fbf4}.step.done b{color:#12805a}.step.now{border-color:#6c4cf1}
.hero{display:grid;grid-template-columns:1.3fr 1fr;gap:18px;align-items:center;background:linear-gradient(135deg,#fff 0%,#f1edff 100%)}@media(max-width:900px){.hero{grid-template-columns:1fr}}
.num{display:inline-flex;width:28px;height:28px;border-radius:50%;background:#6c4cf1;color:#fff;align-items:center;justify-content:center;font-weight:700;margin-right:10px;flex:none}
.how{display:flex;align-items:flex-start;margin:10px 0}.drop{border:2px dashed #c9cdea;border-radius:16px;padding:18px;text-align:center;background:#fafbff}
.tile{border-radius:16px;padding:16px 18px;color:#fff}.tile b{display:block;font-size:30px;line-height:1.1}.tile span{font-size:13.5px;opacity:.95}
table{border-collapse:separate;border-spacing:0;width:100%}th{font-size:12.5px;text-transform:uppercase;letter-spacing:.4px;color:#6b7190;text-align:left;padding:8px 10px;border-bottom:2px solid #eef0fa}
td{padding:11px 10px;border-bottom:1px solid #eef0fa;vertical-align:top;font-size:14px}tr:hover td{background:#fafbff}
.dot{display:inline-block;width:16px;height:16px;border-radius:50%;vertical-align:middle}.q{border-left:4px solid #6c4cf1;background:#f6f4ff;border-radius:0 12px 12px 0;padding:8px 14px;margin:8px 0;font-style:italic}
.tp{border-left:5px solid;border-radius:0 14px 14px 0;background:#fff;padding:12px 16px;margin:10px 0;box-shadow:0 2px 10px rgba(40,44,90,.06)}
.bad{color:#c92a4b;font-size:13.5px;font-weight:600}details{margin:6px 0}summary{cursor:pointer;color:#6c4cf1;font-weight:600;font-size:13.5px}pre{white-space:pre-wrap;font-size:13px;background:#fafbff;border-radius:12px;padding:14px;overflow:auto}
.sig{display:flex;align-items:center;gap:12px;border:2px dashed #dfe2f1;border-radius:16px;padding:12px 16px}.sig.ok{border:2px solid #1fb97a;background:#e9fbf4}.av{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;flex:none}
.meter{height:10px;background:#eef0fa;border-radius:6px;overflow:hidden}.meter i{display:block;height:100%;background:#1fb97a}label.file{cursor:pointer}label.file input{display:none}
"""
ART = """<svg viewBox="0 0 360 230" width="100%" role="img" aria-label="Documents become a checked draft that two people sign">
<rect x="18" y="38" width="120" height="150" rx="14" fill="#fff" stroke="#dfe2f1" stroke-width="2"/><rect x="34" y="60" width="70" height="9" rx="4" fill="#6c4cf1"/>
<rect x="34" y="82" width="88" height="7" rx="3" fill="#dfe2f1"/><rect x="34" y="98" width="80" height="7" rx="3" fill="#dfe2f1"/><rect x="34" y="114" width="88" height="7" rx="3" fill="#dfe2f1"/><rect x="34" y="130" width="60" height="7" rx="3" fill="#dfe2f1"/>
<text x="78" y="172" text-anchor="middle" font-size="12" font-weight="700" fill="#6b7190">RFP</text>
<path d="M150 112h44" stroke="#6c4cf1" stroke-width="4" stroke-linecap="round"/><path d="M186 102l12 10-12 10" fill="none" stroke="#6c4cf1" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="208" y="22" width="134" height="170" rx="14" fill="#fff" stroke="#12b5a6" stroke-width="3"/><rect x="224" y="42" width="80" height="9" rx="4" fill="#12b5a6"/>
<g fill="none" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M226 72l5 5 9-10" stroke="#1fb97a"/><path d="M226 98l5 5 9-10" stroke="#1fb97a"/><path d="M227 122l10 10m0-10l-10 10" stroke="#ff5c7a"/><path d="M226 152l5 5 9-10" stroke="#1fb97a"/></g>
<rect x="250" y="69" width="76" height="7" rx="3" fill="#dfe2f1"/><rect x="250" y="95" width="66" height="7" rx="3" fill="#dfe2f1"/><rect x="250" y="123" width="72" height="7" rx="3" fill="#ffd3dc"/><rect x="250" y="149" width="60" height="7" rx="3" fill="#dfe2f1"/>
<circle cx="238" cy="204" r="17" fill="#6c4cf1"/><circle cx="278" cy="204" r="17" fill="#ffb020"/><path d="M231 204l5 5 9-10M271 204l5 5 9-10" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="70" cy="22" r="9" fill="#ffb020"/><circle cx="150" cy="200" r="7" fill="#ff5c7a"/><circle cx="176" cy="40" r="5" fill="#12b5a6"/></svg>"""


def icon(name):
    return f'<svg viewBox="0 0 24 24"><path d="{ICON[name]}"/></svg>'


def pill(text, colour):
    return f'<span class="pill" style="background:{colour}">{E(text)}</span>'


def tile(value, label, colour):
    return f'<div class="tile" style="background:{colour}"><b>{E(value)}</b><span>{E(label)}</span></div>'


def src(x):
    return f'<a href="{E(x["url"])}" target="_blank" rel="noopener">[{E(x["source"])}] {E(x["title"])}</a> <span class="muted">{E(x["date"])}</span>'


def current(q):
    packs = pipeline.list_packs()
    want = q.get("rfp", [""])[0]
    for p in packs:
        if p["rfp_id"] == want:
            return p, packs
    return (packs[-1] if packs else None), packs


def stage(p):
    """Where this RFP is on its journey, and the one thing to do next."""
    if p is None:
        return 0, "Add an RFP, or use the demo one, and press <b>Prepare draft</b>.", ("home", "Go to Start")
    failing = sum(bool(a["violations"]) for a in p["answers"])
    roles = cfg()["approval"]["roles"]
    if p["status"] != "APPROVED":
        if failing:
            return 2, f"<b>{failing} answer(s)</b> fail their checks. Fix them before anyone can sign.", ("draft", "Fix answers")
        missing = [r for r in roles if r not in p["approvals"]]
        if len(missing) == len(roles):
            return 2, "The draft is ready. Review <b>Our fit</b>, <b>Competition</b> and <b>Customer</b>, then sign.", ("draft", "Review and sign")
        return 3, f"One signature in. Waiting for the <b>{E(missing[0])} lead</b>.", ("draft", "Sign off")
    if not p["outcome"]:
        return 4, "Approved and saved for the team to submit. When you know, record <b>won or lost</b>.", ("draft", "Record result")
    if p["rfp_id"] not in read_json(DATA / "library.json")["learned_packs"]:
        return 5, "Result recorded. Run the <b>review</b> so the library learns from this bid.", ("learn", "Run review")
    return 6, "All done. This bid's approved answers are in the library.", ("home", "Start another")


def stepper(p):
    n = stage(p)[0]
    names = [("Add RFP", "upload or paste"), ("Draft", "agent prepares"), ("Review", "team checks"), ("Sign", "two people"), ("Result", "won or lost"), ("Learn", "library grows")]
    return '<div class="steps">' + "".join(f'<div class="step {"done" if i < n else ("now" if i == n else "")}"><b>{"✓ " if i < n else ""}{E(a)}</b>{E(b)}</div>' for i, (a, b) in enumerate(names)) + "</div>"


def upload_form(kind, text, colour):
    return (f'<form method="post" action="/upload" enctype="multipart/form-data"><input type="hidden" name="kind" value="{kind}">'
            f'<label class="file btn {colour}">{icon("up")}{E(text)}<input type="file" name="file" accept=".txt,.md,.docx,.pdf" onchange="this.form.submit()"></label></form>')


def rfp_files():
    out = []
    for f in sorted((DATA / "rfp").glob("*")):
        if f.is_file() and f.suffix.lower() in ALLOWED:
            try:
                meta = pipeline.parse_rfp(pipeline.read_rfp_file(f), f.stem)
            except Exception as e:
                meta = dict(rfp_id=f.stem, customer="could not read this file", due="", requirements=[], error=str(e))
            out.append((f.name, meta))
    return out


def tab_home(p, packs, q):
    by_id = {x["rfp_id"]: x for x in packs}
    h = f"""<div class="card hero"><div><h2 style="font-size:24px">Turn an RFP into a first draft</h2><p class="muted">The agent prepares. Your team decides. Nothing leaves this computer, and nothing is sent to a customer from here.</p>
    <div class="how"><span class="num">1</span><div><b>Add the RFP.</b> Upload the file or paste the text.</div></div>
    <div class="how"><span class="num" style="background:{TEAL}">2</span><div><b>Read the draft pack.</b> Our fit, the competition, and what the customer has said.</div></div>
    <div class="how"><span class="num" style="background:{SUN}">3</span><div><b>Edit and sign.</b> The technical lead and the account lead both approve.</div></div></div><div>{ART}</div></div>
    <div class="grid g2"><div class="card"><h3>Add the latest RFP</h3><p class="muted">Word (.docx), text (.txt) or PDF. Requirements should be numbered.</p><div class="drop">{upload_form("rfp", "Add an RFP", "")}</div>
    <details><summary>Or paste the text</summary><form method="post" action="/paste"><p><input type="text" name="name" placeholder="Short name, e.g. RFP-2027-001" size="30"></p>
    <textarea name="text" rows="5" placeholder="Paste the RFP here. Include 'Issued by: ...' and the numbered requirements."></textarea><p><button class="teal">Save</button></p></form></details></div>
    <div class="card"><h3>Add a product or service spec sheet</h3><p class="muted">The agent suggests catalogue entries from it. You choose the honest status for each before anything is added.</p>
    <div class="drop">{upload_form("spec", "Add a spec sheet", "teal")}</div><p class="muted" style="margin-bottom:0">See and manage the catalogue on the <a href="/?tab=catalog">Products</a> tab.</p></div></div><h2 style="margin-top:22px">Your RFPs</h2>"""
    for name, m in rfp_files():
        pk = by_id.get(m["rfp_id"])
        if pk:
            state = pill("Won" if pk["outcome"] == "won" else "Lost" if pk["outcome"] == "lost" else "Approved" if pk["status"] == "APPROVED" else "Draft waiting for sign-off",
                         GREEN if pk["outcome"] == "won" or (pk["status"] == "APPROVED" and not pk["outcome"]) else CORAL if pk["outcome"] == "lost" else VIOLET)
            act = f'<a class="btn" href="/?tab=fit&rfp={E(m["rfp_id"])}">Open the draft</a>'
            redo = "" if pk["status"] == "APPROVED" else "<details><summary>Prepare it again</summary>" + run_buttons(name) + "</details>"
        else:
            state, act, redo = pill("No draft yet", "#a3a8c3"), run_buttons(name), ""
        h += f"""<div class="card" style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><div style="flex:1;min-width:260px"><h3>{E(m["rfp_id"])} {state}</h3>
        <div class="muted">{E(m["customer"])} · {len(m["requirements"])} requirements{" · due " + E(m["due"]) if m["due"] else ""} · file {E(name)}</div>{redo}</div><div>{act}</div></div>"""
    return h


def run_buttons(name):
    f = lambda mode, text, cls: (f'<form method="post" action="/run" style="display:inline-block;margin:4px 6px 4px 0"><input type="hidden" name="file" value="{E(name)}">'
                                 f'<input type="hidden" name="mode" value="{mode}"><button class="{cls}">{text}</button></form>')
    return (f("ollama", "Prepare draft with AI", "") + f("mock", "Try it without AI (demo)", "ghost")
            + '<details style="display:inline-block"><summary>Advanced</summary>' + f("noisy_mock", "Demo with planted mistakes", "ghost small") + "</details>")


def tab_fit(p, packs, q):
    n = {k: sum(a["fit"] == k for a in p["answers"]) for k in FITC}
    d = charts.donut([(FITW[k], n[k], FITC[k]) for k in FITC], str(len(p["answers"])), "requirements")
    legend = "".join(f'<p style="margin:8px 0"><span class="dot" style="background:{FITC[k]}"></span> <b>{n[k]}</b> {FITW[k].lower()}</p>' for k in FITC)
    h = f"""<div class="card" style="display:flex;gap:28px;align-items:center;flex-wrap:wrap"><div>{d}</div><div style="flex:1;min-width:260px"><h2>How well we fit this RFP</h2>{legend}
    <p class="muted">The fit comes from the product catalogue, which your team controls. The AI cannot change it, so a gap is always shown as a gap.</p></div></div>
    <div class="card"><table><tr><th>No.</th><th>Requirement</th><th>Fit</th><th>What we position</th><th>Past answers reused</th></tr>"""
    for a in p["answers"]:
        c = a["capability"]
        past = "".join(f'<span class="chip">{E(s["id"])} · {E(s["bid"])} · {E(s["outcome"])}</span>' for s in a["sources"]) or '<span class="muted">none found</span>'
        h += f"""<tr><td><b>{E(a["req_id"])}</b></td><td>{E(a["requirement"])}<br><span class="chip">{E(a["label"])}</span></td><td>{pill(FITW[a["fit"]], FITC[a["fit"]])}</td>
        <td><b>{E(c["product"])}</b> <span class="muted">[{E(c["id"])}]</span><br>{E(c["text"])} <span class="muted">{E(c["note"])}</span></td><td>{past}</td></tr>"""
    return h + "</table></div>"


def tab_comp(p, packs, q):
    val = {"STRONG": 3, "PARTIAL": 2, "GAP": 1}
    comps = sorted({x["entity"] for x in p["claims"]})
    h = f"""<div class="card"><h2>Us against each competitor</h2><p class="muted">Each chart uses only the topics where we found evidence about that competitor. Further out is stronger.
    <span class="dot" style="background:{VIOLET}"></span> us &nbsp; <span class="dot" style="background:{CORAL}"></span> them</p><div class="grid g3">"""
    for comp in comps:
        rows = [(r, r["strengths"], r["weaknesses"]) for r in p["grid"] if any(x["entity"] == comp for x in r["strengths"] + r["weaknesses"])]
        axes, us, them = [], [], []
        for r, s, k in rows:
            cs, ck = any(x["entity"] == comp for x in s), any(x["entity"] == comp for x in k)
            axes.append(r["label"]); us.append(val[r["ours"]]); them.append(2 if cs and ck else 3 if cs else 1)
        ahead, behind = sum(u > t for u, t in zip(us, them)), sum(u < t for u, t in zip(us, them))
        chart = charts.radar(axes, [(comp, CORAL, them), ("Us", VIOLET, us)]) if len(axes) >= 3 else '<p class="muted">Too little evidence for a chart.</p>'
        h += f'<div style="text-align:center"><h3>{E(comp)}</h3>{chart}<div>{pill("We lead on %d" % ahead, GREEN)} {pill("They lead on %d" % behind, CORAL)}</div></div>'
    h += '</div></div><div class="card"><h2>Topic by topic</h2><p class="muted">Internal view. Open a row to see the exact words and the page they came from, so you can check a claim before you repeat it.</p><table><tr><th>Topic</th><th>Us</th>'
    h += "".join(f"<th>{E(c)}</th>" for c in comps) + "<th>What to do</th></tr>"
    for r in p["grid"]:
        cells = ""
        for comp in comps:
            s, k = any(x["entity"] == comp for x in r["strengths"]), any(x["entity"] == comp for x in r["weaknesses"])
            cells += "<td>" + (pill("strong", CORAL) if s else pill("weak", GREEN) if k else '<span class="muted">no evidence</span>') + "</td>"
        ev = "".join(f'<div class="q"><b>{E(x["entity"])}</b> ({E(x["stance"])}): "{E(x["quote"])}"<br>{src(x)}</div>' for x in r["strengths"] + r["weaknesses"])
        det = f'<details><summary>{len(r["strengths"]) + len(r["weaknesses"])} source(s)</summary>{ev}</details>' if ev else ""
        col = next(v for kk, v in POSC.items() if r["position"].startswith(kk))
        h += f'<tr><td><b>{E(r["label"])}</b>{det}</td><td>{pill(FITW[r["ours"]], FITC[r["ours"]])}</td>{cells}<td>{pill(r["position"], col)}</td></tr>'
    h += "</table></div><h2>Talking points</h2>"
    for kind, col in KINDC.items():
        pts = [t for t in p["talking_points"] if t["kind"] == kind]
        if pts:
            h += f'<h3 style="margin-top:16px;color:{col}">{E(kind)} ({len(pts)})</h3>' + "".join(f'<div class="tp" style="border-color:{col}">{E(t["text"])}{"".join("<div class=bad>" + E(v) + "</div>" for v in t["violations"])}</div>' for t in pts)
    if p["blocked"]:
        h += f'<div class="card"><h3 class="bad">Removed: {len(p["blocked"])} statement(s) whose quote was not in the page cited</h3>' + "".join(f'<p class="muted">{E(b.get("entity"))}: "{E(b["quote"])}" (cited {E(b["source"])})</p>' for b in p["blocked"]) + "</div>"
    return h


def tab_cust(p, packs, q):
    pr = p["priorities"]
    inr = sum(not x["relation"].startswith("not") for x in pr)
    h = f"""<div class="grid g4">{tile(len(pr), "public statements found", VIOLET)}{tile(inr, "covered by the RFP", TEAL)}{tile(len(pr) - inr, "the RFP did not ask about", SUN)}{tile(sum(x["ours"] == "GAP" for x in pr), "where we are weak", CORAL)}</div>
    <p class="muted">Internal view. Public, professional sources only. People are shown by role, never by name.</p><div class="grid g2">"""
    for x in pr:
        rel = pill("Not in the RFP: raise it", SUN) if x["relation"].startswith("not") else pill(x["relation"][:1].upper() + x["relation"][1:], TEAL)
        h += f'<div class="card" style="margin:0"><h3>{E(x["label"])}</h3><div class="q">"{E(x["quote"])}"</div><div class="muted">{E(x["role"])} · {src(x)}</div><p style="margin:10px 0 0">{rel} {pill(FITW[x["ours"]], FITC[x["ours"]])}</p></div>'
    h += '</div><div class="grid g2"><div class="card"><h2>Consider adding to the submission</h2>' + ("".join(f'<div class="tp" style="border-color:{VIOLET};box-shadow:none;background:#f6f4ff">{E(v["internal_text"])}</div>' for v in p["value_adds"]) or '<p class="muted">Nothing found.</p>')
    return h + '</div><div class="card"><h2>Handle with care</h2>' + ("".join(f'<div class="tp" style="border-color:{CORAL};box-shadow:none;background:#fff1f4">{E(a)}</div>' for a in p["avoid"]) or '<p class="muted">Nothing found.</p>') + "</div></div>"


def tab_draft(p, packs, q):
    done, roles = p["status"] == "APPROVED", cfg()["approval"]["roles"]
    ok = sum(not a["violations"] for a in p["answers"])
    sigs = ""
    for r, col in zip(roles, (VIOLET, SUN, TEAL, SKY)):
        v = p["approvals"].get(r)
        sigs += (f'<div class="sig ok"><div class="av" style="background:{col}">✓</div><div><b>{E(r.capitalize())} lead</b><br>{E(v["name"])} <span class="muted">{E(v["time"].replace("T", " "))}</span></div></div>' if v
                 else f'<div class="sig"><div class="av" style="background:#c9cdea">?</div><div><b>{E(r.capitalize())} lead</b><br><span class="muted">not signed yet</span></div></div>')
    h = f"""<div class="card"><h2>{"Approved" if done else "Waiting for sign-off"}</h2><div class="grid g2" style="margin:12px 0">{sigs}</div>
    <div class="meter"><i style="width:{100 * ok // max(1, len(p["answers"]))}%"></i></div><p class="muted">{ok} of {len(p["answers"])} answers pass every check.</p>"""
    if not done:
        opts = "".join(f"<option value='{E(r)}'>{E(r.capitalize())} lead</option>" for r in roles)
        h += f"""<form method="post" action="/approve"><input type="hidden" name="rfp" value="{E(p["rfp_id"])}">I am the <select name="role">{opts}</select> and my name is
        <input type="text" name="name" size="22" placeholder="Your name"> <button class="teal">{icon("check")}Sign off</button></form>
        <p class="muted" style="margin-bottom:0">Two different people must sign. Changing an answer clears earlier signatures. Nothing is sent from here: the approved response is saved to a folder for the team to submit.</p>"""
    else:
        h += f"""<p>The approved response is saved in <b>outbox/approved/{E(p["rfp_id"])}/response_final.md</b>. Result: <b>{E(p["outcome"] or "not recorded yet")}</b></p>
        <form method="post" action="/outcome"><input type="hidden" name="rfp" value="{E(p["rfp_id"])}"><button name="outcome" value="won" class="teal">We won</button> <button name="outcome" value="lost" class="coral">We lost</button></form>"""
    h += "</div>"
    for a in sorted(p["answers"], key=lambda a: not a["violations"]):  # answers that need attention come first
        bad = "".join(f'<div class="bad">Needs fixing: {E(v)}</div>' for v in a["violations"])
        state = pill("needs fixing", CORAL) if a["violations"] else pill("passes checks", GREEN)
        h += f'<div class="card"><h3>{E(a["req_id"])} <span style="font-weight:400">{E(a["requirement"])}</span></h3><p style="margin:6px 0">{pill(FITW[a["fit"]], FITC[a["fit"]])} {state} {"<span class=chip>edited by the team</span>" if a["edited"] else ""}</p>{bad}'
        if done:
            h += f"<p>{E(a['final'])}</p></div>"
        else:
            h += f"""<form method="post" action="/edit"><input type="hidden" name="rfp" value="{E(p["rfp_id"])}"><input type="hidden" name="req" value="{E(a["req_id"])}">
            <textarea name="text" rows="4">{E(a["final"])}</textarea><p style="margin:8px 0 0"><input type="text" name="who" size="18" placeholder="Edited by"> <button class="ghost small">Save and re-check</button>
            <span class="muted">Keep the tags in square brackets. They are removed from the customer copy.</span></p></form></div>"""
    return h


def tab_catalog(p, packs, q):
    cat, tax = read_json(DATA / "catalog.json"), read_json(DATA / "taxonomy.json")
    label = {t["code"]: t["label"] for t in tax}
    n = {s: sum(c["status"] == s for c in cat) for s in FIT}
    h = f"""<div class="grid g4">{tile(len(cat), "catalogue entries", VIOLET)}{tile(n["available"], "available today", GREEN)}{tile(n["partial"], "partly available", SUN)}{tile(n["roadmap"] + n["not_offered"], "roadmap or not offered", CORAL)}</div>
    <div class="card" style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><div style="flex:1;min-width:260px"><h2>Add a product or service spec sheet</h2>
    <p class="muted" style="margin:0">The catalogue is your list of commitments, so nothing is added automatically. The agent suggests entries and you set the honest status.</p></div>{upload_form("spec", "Add a spec sheet", "teal")}</div>"""
    prop = read_json(OUT / "spec_proposals.json") if (OUT / "spec_proposals.json").exists() else None
    if prop and prop["items"]:
        topic = lambda sel: "".join(f'<option value="{E(t["code"])}" {"selected" if t["code"] == sel else ""}>{E(t["label"])}</option>' for t in tax)
        h += f'<div class="card"><h2>Suggested from {E(prop["file"])}</h2><p class="muted">{len(prop["items"])} suggestion(s). Add the ones that are true, with the right status. Skip the rest.</p>'
        for i, it in enumerate(prop["items"]):
            h += f"""<form method="post" action="/catalog_add" style="border-top:1px solid #eef0fa;padding:12px 0"><input type="hidden" name="idx" value="{i}">
            <textarea name="text" rows="2">{E(it["text"])}</textarea><p style="margin:8px 0 0"><input type="text" name="product" size="20" placeholder="Product or service name">
            <select name="category">{topic(it["category"])}</select> <select name="status"><option value="">Choose status…</option><option value="available">Available today</option><option value="partial">Partly available</option>
            <option value="roadmap">On the roadmap</option><option value="not_offered">Not offered</option></select> <input type="text" name="note" size="26" placeholder="Honest note (optional)">
            <input type="text" name="who" size="14" placeholder="Your name"> <button class="small">Add</button> <button class="ghost small" name="skip" value="1">Skip</button></p></form>"""
        h += "</div>"
    statusw = {"available": ("Available", GREEN), "partial": ("Partly", SUN), "roadmap": ("Roadmap", CORAL), "not_offered": ("Not offered", CORAL)}
    for product in sorted({c["product"] for c in cat}):
        rows = [c for c in cat if c["product"] == product]
        h += f'<div class="card"><h3>{E(product)} <span class="chip">{len(rows)} {"entry" if len(rows) == 1 else "entries"}</span></h3><table>'
        h += "".join(f'<tr><td style="width:70px" class="muted">{E(c["id"])}</td><td style="width:210px"><span class="chip">{E(label.get(c["category"], c["category"]))}</span></td><td>{E(c["text"])} <span class="muted">{E(c["note"])}</span></td><td style="width:110px">{pill(*statusw[c["status"]])}</td></tr>' for c in rows) + "</table></div>"
    return h


def tab_learn(p, packs, q):
    lib = read_json(DATA / "library.json")
    won = sum(b["outcome"] == "won" for b in lib["bids"])
    h = f"""<div class="grid g4">{tile(len(lib["answers"]), "answers in the library", VIOLET)}{tile(len(lib["bids"]), "bids on record", SKY)}{tile(won, "bids won", GREEN)}{tile("v" + str(lib["version"]), "library version", SUN)}</div>
    <div class="card" style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><div style="flex:1;min-width:260px"><h2>Six-month review</h2><p class="muted" style="margin:0">Adds approved answers that have a result to the library, and reports what the team rewrote, won and lost. No AI is involved.</p></div>
    <form method="post" action="/learn"><button>{icon("learn")}Run the review now</button></form></div>"""
    bycat = {}
    for a in lib["answers"]:
        bycat[a["category"]] = bycat.get(a["category"], 0) + 1
    label = {t["code"]: t["label"] for t in read_json(DATA / "taxonomy.json")}
    top = sorted(bycat.items(), key=lambda x: -x[1])
    mx = top[0][1] if top else 1
    palette = [VIOLET, SKY, TEAL, GREEN, SUN, CORAL]
    h += '<div class="card"><h2>What the library knows most about</h2>' + charts.bars([(label.get(c, c), v / mx, palette[i % 6], f"{v} answers") for i, (c, v) in enumerate(top[:10])]) + "</div>"
    reports = sorted(OUT.glob("learning_review_*.md"))
    if reports:
        h += f'<div class="card"><h2>Latest review</h2><pre>{E(reports[-1].read_text(encoding="utf-8"))}</pre></div>'
    if (OUT / "report.md").exists():
        h += f'<div class="card"><details><summary>Test results against the answer key (invented demo RFP only)</summary><pre>{E((OUT / "report.md").read_text(encoding="utf-8"))}</pre></details></div>'
    if (OUT / "audit_log.jsonl").exists():
        tail = (OUT / "audit_log.jsonl").read_text(encoding="utf-8").splitlines()[-20:]
        h += f'<div class="card"><details><summary>Audit log (last 20 lines)</summary><pre>{E(chr(10).join(tail))}</pre></details></div>'
    return h


RENDER = dict(home=tab_home, fit=tab_fit, comp=tab_comp, cust=tab_cust, draft=tab_draft, catalog=tab_catalog, learn=tab_learn)
NEEDS_PACK = ("fit", "comp", "cust", "draft")


def page(q):
    tab = q.get("tab", ["home"])[0]
    tab = tab if tab in RENDER else "home"
    msg = q.get("msg", [""])[0]
    p, packs = current(q)
    rid = p["rfp_id"] if p else ""
    nav = "".join(f'<a class="{"on" if k == tab else ""}" href="/?tab={k}&rfp={E(rid)}">{icon(k)}{E(v)}</a>' for k, v in TABS)
    body = f'<div class="msg {"warn" if msg.startswith("!") else ""}">{E(msg.lstrip("!"))}</div>' if msg else ""
    if tab in NEEDS_PACK and p is None:
        body += f'<div class="card" style="text-align:center"><div style="max-width:300px;margin:0 auto">{ART}</div><h2>No draft yet</h2><p class="muted">Add an RFP on the Start page and prepare a draft first.</p><a class="btn" href="/?tab=home">Go to Start</a></div>'
    else:
        if p and tab != "catalog":
            n, text, (go, btn) = stage(p)
            if len(packs) > 1 and tab in NEEDS_PACK:
                body += '<p class="muted">Showing ' + " ".join(f'<a class="chip" style="{"background:#1b1f3b;color:#fff" if x["rfp_id"] == rid else ""}" href="/?tab={tab}&rfp={E(x["rfp_id"])}">{E(x["rfp_id"])}</a>' for x in packs) + "</p>"
            body += stepper(p) + f'<div class="next"><span>Next for <b>{E(rid)}</b>: {text}</span>' + (f'<a class="btn" href="/?tab={go}&rfp={E(rid)}">{E(btn)}</a>' if go != tab else "") + "</div>"
            if p["is_mock"] and tab in NEEDS_PACK:
                body += '<div class="mock"><b>Demo run.</b> A stand-in was used here, not an AI model. It shows how the tool works. It is not a test of the AI.</div>'
        body += RENDER[tab](p, packs, q)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RFP Response Agent</title><style>{CSS}</style></head><body>
    <header><h1>RFP Response Agent</h1><p>The agent drafts from work you have already done. Your team checks and signs.</p></header><nav>{nav}</nav><main>{body}</main></body></html>"""


def read_form(handler):
    raw = handler.rfile.read(int(handler.headers.get("Content-Length", 0)))
    ctype = handler.headers.get("Content-Type", "")
    if ctype.startswith("multipart/form-data"):
        msg = BytesParser(policy=email_policy).parsebytes(b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + raw)
        out = {}
        for part in msg.iter_parts():
            name, data = part.get_param("name", header="content-disposition"), part.get_payload(decode=True) or b""
            out[name] = (part.get_filename(), data) if part.get_filename() is not None else data.decode("utf-8", "ignore")
        return out
    return {k: v[0] for k, v in urllib.parse.parse_qs(raw.decode("utf-8"), keep_blank_values=True).items()}


def safe_name(name):
    name = re.sub(r"[^\w.\- ]", "_", os.path.basename(name or "")).strip() or "file.txt"
    if not name.lower().endswith(ALLOWED):
        raise ValueError("Please use a .txt, .docx or .pdf file.")
    return name


def handle(path, f):
    """Does one action. Returns (tab, rfp id, message)."""
    if path == "/run":
        pack = pipeline.run(DATA / "rfp" / safe_name(f["file"]), f["mode"])
        key = pipeline.truth()
        if key and "Brackenfield" in pack["customer"]:
            score.score(pack["rfp_id"])
        bad = sum(bool(a["violations"]) for a in pack["answers"])
        return "fit", pack["rfp_id"], f"Draft ready: {len(pack['answers'])} answers, {bad} needing a fix. Start with Our fit."
    if path == "/upload":
        fname, data = f.get("file", ("", b""))
        if not data:
            raise ValueError("No file was chosen.")
        if len(data) > 15_000_000:
            raise ValueError("That file is over 15 MB.")
        name = safe_name(fname)
        folder = DATA / ("rfp" if f.get("kind") == "rfp" else "specs")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(data)
        if f.get("kind") == "rfp":
            n = len(pipeline.parse_rfp(pipeline.read_rfp_file(folder / name), name)["requirements"])
            return "home", "", (f"Added {name}. Found {n} numbered requirements. Press Prepare draft." if n else f"!Added {name}, but no numbered requirements were found. Check the numbering, or paste the text.")
        items = catalog.propose(pipeline.read_rfp_file(folder / name))
        write_json(OUT / "spec_proposals.json", dict(file=name, items=items))
        return "catalog", "", f"Read {name}: {len(items)} suggested catalogue entries. Nothing has been added yet."
    if path == "/paste":
        name = "".join(ch for ch in f.get("name", "") if ch.isalnum() or ch in "-_") or "pasted-rfp"
        (DATA / "rfp" / f"{name}.txt").write_text(f.get("text", ""), encoding="utf-8")
        return "home", "", f"Saved as {name}.txt. Press Prepare draft."
    if path == "/edit":
        bad = pipeline.edit_answer(f["rfp"], f["req"], f["text"], f.get("who", ""))
        return "draft", f["rfp"], (f"{f['req']} saved. It passes its checks." if not bad else f"!{f['req']} saved, but it still needs fixing: " + " ".join(bad))
    if path == "/approve":
        pack = pipeline.approve(f["rfp"], f["role"], f.get("name", ""))
        return "draft", f["rfp"], ("Both people have signed. The response is approved and saved for the team to submit." if pack["status"] == "APPROVED" else "Signed. One more signature is needed.")
    if path == "/outcome":
        pipeline.set_outcome(f["rfp"], f["outcome"])
        return "learn", f["rfp"], "Result saved. Run the review so the library learns from it."
    if path == "/learn":
        r = learn.review()
        return "learn", "", f"Review done: learned from {r['learned']} bid(s), added {r['added']} answers. Library is now version {r['version']}."
    if path == "/catalog_add":
        prop = read_json(OUT / "spec_proposals.json")
        i = int(f["idx"])
        if not f.get("skip"):
            e = catalog.add_entry(f.get("product", ""), f["category"], f.get("status", ""), f["text"], f.get("note", ""), f.get("who", ""))
            note = f"Added {e['id']} to the catalogue."
        else:
            note = "Skipped."
        prop["items"].pop(i)
        write_json(OUT / "spec_proposals.json", prop)
        return "catalog", "", note
    raise ValueError("Unknown action.")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        data = page(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        path, f = urllib.parse.urlparse(self.path).path, {}
        back = dict(run="home", upload="home", paste="home", edit="draft", approve="draft", outcome="draft", learn="learn", catalog_add="catalog").get(path.strip("/"), "home")
        try:
            f = read_form(self)
            tab, rfp, msg = handle(path, f)
        except Stop as e:
            tab, rfp, msg = back, "", "!" + str(e)
        except Exception as e:
            hint = "  Is Ollama running? Open the Ollama app, or use 'Try it without AI'." if any(k in str(e) for k in ("urlopen", "refused", "timed out")) else ""
            tab, rfp, msg = back, (f.get("rfp", "") if isinstance(f.get("rfp", ""), str) else ""), f"!Could not do that: {e}{hint}"
        self.send_response(303)  # go back to the page, so refreshing the browser never repeats an action
        self.send_header("Location", "/?" + urllib.parse.urlencode(dict(tab=tab, rfp=rfp, msg=msg)))
        self.end_headers()


if __name__ == "__main__":
    if not (DATA / "catalog.json").exists():
        import make_demo_data
        make_demo_data.main()
    s = cfg()["server"]
    print(f"RFP Response Agent is running. Open http://localhost:{s['port']} in your browser. Press Ctrl+C to stop.")
    ThreadingHTTPServer((os.environ.get("RFP_HOST", s["host"]), s["port"]), H).serve_forever()
