"""Checks written in plain code. The AI drafts; these rules decide whether a draft may go forward."""
from __future__ import annotations

import re

from .common import norm

TAG = re.compile(r"\[((?:C|L|W)-[\w-]+)\]")
NUM = re.compile(r"\d+(?:[.,]\d+)?")
HYPE = ["guarantee", "best-in-class", "world-class", "industry-leading", "unrivalled", "unmatched", "market-leading"]
OVERCLAIM = ["fully", "full support", "complete support", "out of the box"]


def strip_tags(text: str) -> str:
    return re.sub(r"\s*\[(?:C|L|W)-[\w-]+\]", "", text)


def verify_quote(quote: str, page_text: str) -> bool:
    """A claim only counts if its quote really appears in the page it cites."""
    q = norm(quote)
    return len(q) >= 12 and q in norm(page_text)


def check_answer(text: str, *, fit: str, capability: dict, sources: list[dict], requirement: str,
                 blocked_names: list[str], max_words: int) -> list[str]:
    """Returns a list of problems. An empty list means the answer passes."""
    bad = []
    tags = TAG.findall(text)
    if capability["id"] not in tags:
        bad.append(f"Does not cite the catalogue entry it relies on [{capability['id']}].")
    known = {capability["id"]} | {s["id"] for s in sources}
    for t in tags:
        if t not in known:
            bad.append(f"Cites [{t}], which was not one of its sources.")
    plain = strip_tags(text)
    if len(plain.split()) > max_words:
        bad.append(f"Longer than {max_words} words.")
    low = plain.lower()
    for name in blocked_names:
        if name.lower() in low:
            bad.append(f"Names '{name}', which must not appear in a customer response.")
    for word in HYPE:
        if word in low:
            bad.append(f"Uses the sales word '{word}'.")
    allowed = " ".join([capability["text"], capability.get("note", ""), requirement] + [s["answer"] for s in sources])
    allowed_nums = set(NUM.findall(allowed))
    for n in NUM.findall(plain):
        if n not in allowed_nums:
            bad.append(f"Contains the number {n}, which is not in its sources.")
    if fit != "STRONG":
        for word in OVERCLAIM:
            if word in low:
                bad.append(f"Says '{word}' although the catalogue marks this as {fit.lower()}.")
    if fit == "GAP" and not any(k in low for k in ["not ", "no ", "planned"]):
        bad.append("The catalogue says we do not offer this, but the answer does not say so plainly.")
    return bad


def check_point(text: str, known_tags: set[str]) -> list[str]:
    """Internal talking points must point at evidence."""
    tags = TAG.findall(text)
    if not tags:
        return ["No source cited."]
    return [f"Cites [{t}], which does not exist." for t in tags if t not in known_tags]
