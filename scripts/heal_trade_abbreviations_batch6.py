#!/usr/bin/env python3
"""Normalize Conf & Tobac, Resturant/Restaur, Wkr/Wrkr, Bkr/Asst, and Engrocers trade abbreviations."""
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

EXACT_MAP = {
    "conf & tobac": "Confectioner and Tobacconist",
    "tobac": "Tobacconist",
    "confr": "Confectioner",
    "confr.": "Confectioner",
    "baker & confr": "Baker and Confectioner",
    "resturant": "Restaurant",
    "restaur": "Restaurant",
    "restaur'nt": "Restaurant",
    "engrocers": "Greengrocers",
    "engrocer": "Greengrocer",
    "i.wkr": "Iron Worker",
    "wkr": "Worker",
    "wrkr": "Worker",
}


def normalize_trade(raw: str) -> str:
    t = (raw or "").strip()
    if not t:
        return t
    low = t.lower()
    if low in EXACT_MAP:
        return EXACT_MAP[low]

    out = t
    out = re.sub(r"\bResturant\b|\bRestaur'Nt\b|\bRestaur\b", "Restaurant", out, flags=re.I)
    out = re.sub(r"\bConfection'R\b|\bConfect'Nr\b|\bConfr\.?\b", "Confectioner", out, flags=re.I)
    out = re.sub(r"\bTobac\.?\b", "Tobacconist", out, flags=re.I)
    out = re.sub(r"\bChem\.?\s+W(?:r)?kr\.?\b", "Chemical Worker", out, flags=re.I)
    out = re.sub(r"\bTransp\.?\s+W(?:r)?kr\.?\b", "Transport Worker", out, flags=re.I)
    out = re.sub(r"\bI\.?\s*W(?:r)?kr\.?\b", "Iron Worker", out, flags=re.I)
    out = re.sub(r"\bW(?:r)?kr\.?\b", "Worker", out, flags=re.I)
    out = re.sub(r"\bBkr\.?\b", "Baker", out, flags=re.I)
    out = re.sub(r"\bAsst\.?\b", "Assistant", out, flags=re.I)
    out = re.sub(r"\bEngrocers\b", "Greengrocers", out, flags=re.I)
    out = re.sub(r"\bEngrocer\b", "Greengrocer", out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def main():
    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changed = Counter()
    for r in rows:
        old = (r.get("trade") or "").strip()
        new = normalize_trade(old)
        if new != old:
            r["trade"] = new
            changed[(old, new)] += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Normalized {sum(changed.values())} trade rows across {len(changed)} distinct patterns.")
    for (o, n), cnt in changed.most_common(30):
        print(f"  {cnt:4d}: {o!r} -> {n!r}")


if __name__ == "__main__":
    main()
