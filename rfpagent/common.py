"""Shared helpers: paths, settings, files, the audit log, the kill switch and the call to the local AI model."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("RFP_HOME") or Path(__file__).resolve().parent.parent)  # RFP_HOME lets the tests work on a copy
DATA = ROOT / "data"
OUT = ROOT / "output"
PENDING = ROOT / "outbox" / "pending"
APPROVED = ROOT / "outbox" / "approved"
FIT = {"available": "STRONG", "partial": "PARTIAL", "roadmap": "GAP", "not_offered": "GAP"}


def cfg() -> dict:
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def today(c: dict) -> dt.date:
    t = c["agent"].get("today") or ""
    return dt.date.fromisoformat(t) if t else dt.date.today()


def read_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def write_text(p, text):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def audit(event: str, **kw):
    OUT.mkdir(parents=True, exist_ok=True)
    row = dict(time=dt.datetime.now().isoformat(timespec="seconds"), event=event, **kw)
    with open(OUT / "audit_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def norm(s: str) -> str:
    """Lower-case, straighten quotes and collapse spaces, so a quote can be compared with its source."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


class Stop(Exception):
    pass


class Budget:
    """Counts AI calls and checks the kill switch before every step."""

    def __init__(self, c: dict):
        self.max = c["agent"]["max_llm_calls"]
        self.used = 0

    def check(self):
        if not cfg()["agent"]["enabled"] or (ROOT / "STOP").exists():
            raise Stop("Kill switch is on: the agent has stopped.")

    def use(self):
        self.check()
        if self.used >= self.max:
            raise Stop(f"AI call limit reached ({self.max}).")
        self.used += 1


def ollama_json(c: dict, budget: Budget, prompt: str, schema: dict) -> dict:
    """One call to the local model. The reply must match the schema. Only talks to the address in config.toml."""
    budget.use()
    o = c["ollama"]
    url = os.environ.get("OLLAMA_URL", o["url"]).rstrip("/") + "/api/chat"
    body = json.dumps({"model": o["model"], "stream": False, "format": schema,
                       "messages": [{"role": "user", "content": prompt}],
                       "options": {"temperature": 0, "num_ctx": o["num_ctx"]}}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=o["timeout_seconds"]) as r:
        reply = json.loads(r.read().decode("utf-8"))
    return json.loads(reply["message"]["content"])
