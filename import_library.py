#!/usr/bin/env python3
"""Load your own past RFP answers into the library from a spreadsheet saved as CSV.

  python import_library.py my_past_answers.csv

The CSV needs these column headings:  bid, customer, industry, date, outcome, category, question, answer
  date is YYYY-MM-DD, outcome is won or lost, category is one of the codes in data/taxonomy.json.
Existing answers are kept; new ones are added.
"""
import csv
import sys

from rfpagent.common import DATA, read_json, write_json

if len(sys.argv) != 2:
    sys.exit(__doc__)
lib = read_json(DATA / "library.json")
codes = {t["code"] for t in read_json(DATA / "taxonomy.json")}
bids = {b["bid"] for b in lib["bids"]}
n = len(lib["answers"])
added = 0
with open(sys.argv[1], newline="", encoding="utf-8-sig") as f:
    for i, row in enumerate(csv.DictReader(f), start=2):
        if row["category"] not in codes or row["outcome"] not in ("won", "lost"):
            sys.exit(f"Row {i}: unknown category or outcome. Nothing was saved.")
        if row["bid"] not in bids:
            lib["bids"].append(dict(bid=row["bid"], customer=row["customer"], industry=row.get("industry", ""), date=row["date"], outcome=row["outcome"]))
            bids.add(row["bid"])
        n, added = n + 1, added + 1
        lib["answers"].append(dict(id=f"L-{n:03d}", bid=row["bid"], category=row["category"], question=row["question"], answer=row["answer"]))
lib["version"] += 1
write_json(DATA / "library.json", lib)
print(f"Added {added} answers. The library is now version {lib['version']} with {len(lib['answers'])} answers.")
