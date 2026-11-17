#!/usr/bin/env python3
"""
import sys

if sys.version_info < (3, 11):
    sys.exit("This tool needs Python 3.11 or newer. You have " + sys.version.split()[0] + ". Install a newer Python from python.org.")
Run the agent from the command line (the browser screen in app.py does the same thing with buttons).

  python run_demo.py                    real run with your local Ollama model
  python run_demo.py --mode mock        plumbing test, no AI needed (NOT a result)
  python run_demo.py --mode noisy_mock  a stand-in that makes mistakes on purpose, to show the checks catch them
"""
import argparse

from rfpagent import pipeline, score
from rfpagent.common import DATA, Stop

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="ollama", choices=["ollama", "mock", "noisy_mock"])
ap.add_argument("--rfp", default=str(DATA / "rfp" / "RFP-2026-014_Brackenfield.txt"))
a = ap.parse_args()
if not (DATA / "catalog.json").exists():
    import make_demo_data
    make_demo_data.main()
try:
    pack = pipeline.run(a.rfp, a.mode)
except Stop as e:
    print(e)
    sys.exit(2)
s = score.score(pack["rfp_id"])
print(("MOCK RUN - plumbing test, not an AI result\n" if pack["is_mock"] else "") + open("output/report.md", encoding="utf-8").read())
print(f"Draft pack: outbox/pending/{pack['rfp_id']}  (nothing is sent; two people must approve)")
