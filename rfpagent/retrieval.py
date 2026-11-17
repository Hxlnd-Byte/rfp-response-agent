"""Finding the most useful past answers. Plain keyword ranking (BM25): no extra software, easy to explain."""
from __future__ import annotations

import datetime as dt
import math
import re

WORD = re.compile(r"[a-z0-9]+")
SKIP = set("the a an and or of to in on for with by is are be it its this that as at from how what which can does do "
           "shall must should will solution vendor describe provide customer including any all their our we you".split())


def words(s: str) -> list[str]:
    return [w for w in WORD.findall(s.lower()) if w not in SKIP and len(w) > 1]


class BM25:
    def __init__(self, docs: list[str]):
        self.docs = [words(d) for d in docs]
        self.n = len(self.docs)
        self.avg = (sum(len(d) for d in self.docs) / self.n) if self.n else 0
        self.df: dict[str, int] = {}
        for d in self.docs:
            for w in set(d):
                self.df[w] = self.df.get(w, 0) + 1

    def scores(self, query: str) -> list[float]:
        q, out = words(query), []
        for d in self.docs:
            s = 0.0
            for w in q:
                tf = d.count(w)
                if tf:
                    idf = math.log(1 + (self.n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    s += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(d) / (self.avg or 1)))
            out.append(s)
        return out


def best(items: list[dict], texts: list[str], query: str) -> dict | None:
    """The single best match, or the first item if nothing matches at all."""
    if not items:
        return None
    sc = BM25(texts).scores(query)
    return items[max(range(len(items)), key=lambda i: sc[i])]


def past_answers(library: dict, query: str, today: dt.date, c: dict) -> list[dict]:
    """Top past answers for one requirement. Answers from won bids and recent bids rank a little higher."""
    bids = {b["bid"]: b for b in library["bids"]}
    ans = library["answers"]
    sc = BM25([a["question"] + " " + a["answer"] for a in ans]).scores(query)
    ranked = []
    for a, s in zip(ans, sc):
        if s <= 0:
            continue
        b = bids[a["bid"]]
        years = max(0.0, (today - dt.date.fromisoformat(b["date"])).days / 365)
        s *= max(0.5, 1 - c["retrieval"]["recency_loss_per_year"] * years)
        if b["outcome"] == "won":
            s *= c["retrieval"]["won_boost"]
        ranked.append((s, a, b))
    ranked.sort(key=lambda x: -x[0])
    return [dict(id=a["id"], bid=a["bid"], category=a["category"], outcome=b["outcome"], date=b["date"],
                 answer=a["answer"], score=round(s, 2)) for s, a, b in ranked[: c["retrieval"]["top_k"]]]
