"""Looking things up on the web. Two rules: only a company name plus an approved topic word leaves the machine,
and every page that comes back keeps its address so a person can check it."""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request

from .common import DATA, audit, read_json


def safe_query(entity: str, topic: str, c: dict) -> str:
    """Build a search phrase from the company name and one approved topic. Refuse anything else."""
    allowed = set(c["web"]["competitor_topics"]) | set(c["web"]["customer_topics"])
    if topic not in allowed:
        raise ValueError(f"Topic not on the approved list: {topic!r}")
    if not entity or len(entity.split()) > 6 or len(entity) > 60:
        raise ValueError("A search may only use a short company name.")
    return f"{entity} {topic}"


def _strip(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|nav|footer|header).*?</\1>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", page))).strip()


def search(entity: str, kind: str, c: dict) -> list[dict]:
    """Pages about one company. kind is 'competitor' or 'customer'."""
    mode = c["web"]["mode"]
    if mode == "off":
        return []
    if mode == "snapshot":
        return [p for p in read_json(DATA / "web_snapshot.json") if p["entity"] == entity]
    pages, seen = [], set()
    for topic in c["web"][f"{kind}_topics"]:
        q = safe_query(entity, topic, c)
        audit("web_search", query=q)  # the exact words sent are logged
        url = c["web"]["searxng_url"].rstrip("/") + "/search?" + urllib.parse.urlencode({"q": q, "format": "json"})
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                results = json.loads(r.read().decode("utf-8")).get("results", [])
        except Exception as e:  # a failed search is reported, never hidden
            audit("web_search_failed", query=q, error=str(e))
            continue
        for res in results[:3]:
            if res.get("url") in seen or len(pages) >= c["web"]["max_pages_per_entity"]:
                continue
            seen.add(res["url"])
            try:
                with urllib.request.urlopen(urllib.request.Request(res["url"], headers={"User-Agent": "rfp-response-agent"}), timeout=30) as r:
                    text = _strip(r.read(400_000).decode("utf-8", "ignore"))[:6000]
            except Exception:
                text = res.get("content", "")
            pages.append(dict(id=f"W-{len(pages) + 1:02d}-{kind[:2]}-{abs(hash(entity)) % 1000}", entity=entity, kind="web_page",
                              date=(res.get("publishedDate") or "")[:10], url=res["url"], title=res.get("title", ""), text=text))
    return pages
