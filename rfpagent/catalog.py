"""Product and service spec sheets. A spec sheet never changes the catalogue on its own:
the tool proposes entries, and a person chooses the honest status and adds each one."""
from __future__ import annotations

import re

from . import guardrails as g
from . import pipeline
from .common import DATA, FIT, Budget, audit, cfg, ollama_json, read_json, write_json

CLAIM = re.compile(r"\b(supports?|provides?|includes?|offers?|detects?|creates?|runs?|can|allows?|integrates?|automates?|monitors?|trains?|available|planned|does not|is not)\b", re.I)


def propose(text: str, mode: str = "keywords") -> list[dict]:
    """Sentences from a spec sheet that look like capabilities, each with a suggested topic. Suggestions only."""
    w = pipeline.world()
    label = {t["code"]: t["label"] for t in w["tax"]}
    have = {g.norm(c["text"]) for c in w["catalog"]}
    out = []
    if mode == "ollama":
        c = cfg()
        budget = Budget(c)
        menu = "\n".join(f"- {t['code']}: {t['label']}" for t in w["tax"])
        item = {"type": "object", "properties": {"category": {"type": "string", "enum": list(label)}, "quote": {"type": "string"}}, "required": ["category", "quote"]}
        reply = ollama_json(c, budget, "Below is a product or service spec sheet. List each capability it states. For each, copy ONE sentence exactly as "
                            f"written and choose the topic that fits best. Do not add anything that is not in the text.\n\nTopics:\n{menu}\n\nSpec sheet:\n{text[:12000]}",
                            {"type": "object", "properties": {"items": {"type": "array", "items": item}}, "required": ["items"]})
        found = [(x["quote"].strip(), x["category"]) for x in reply.get("items", []) if g.verify_quote(x["quote"], text)]  # must really be in the sheet
    else:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text)]
        found = [(s, pipeline.by_keywords(s, w)) for s in sentences if 40 <= len(s) <= 320 and CLAIM.search(s)]
    for sentence, cat in found:
        if g.norm(sentence) not in have and all(g.norm(sentence) != g.norm(o["text"]) for o in out):
            out.append(dict(text=sentence, category=cat, label=label[cat]))
    return out[:30]


def add_entry(product: str, category: str, status: str, text: str, note: str, who: str) -> dict:
    cat = read_json(DATA / "catalog.json")
    codes = {t["code"] for t in read_json(DATA / "taxonomy.json")}
    if status not in FIT:
        raise ValueError("Choose a status: available, partial, roadmap or not_offered.")
    if category not in codes:
        raise ValueError("Unknown topic.")
    if not product.strip() or not text.strip() or not who.strip():
        raise ValueError("Product name, wording and your name are all needed. The catalogue is a list of commitments.")
    n = max([int(c["id"].split("-")[1]) for c in cat if c["id"].split("-")[1].isdigit()] + [0]) + 1
    entry = dict(id=f"C-{n:02d}", product=product.strip(), category=category, status=status, text=text.strip(), note=note.strip())
    cat.append(entry)
    write_json(DATA / "catalog.json", cat)
    audit("catalogue_entry_added", id=entry["id"], status=status, by=who.strip())
    return entry
