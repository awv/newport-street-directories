#!/usr/bin/env python3
"""Normalize Tobcnst, Furn. Dlrs, Pork Butch'r, Pawnbrokr, Hairdrsr, Manufact'r, Boarding Ho, Ship Chan., and siblings."""
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

EXACT_MAP = {
    "tobcnst": "Tobacconist",
    "tobacnst": "Tobacconist",
    "tobac'nst": "Tobacconist",
    "tobenst": "Tobacconist",
    "tobocnst": "Tobacconist",
    "tobaccnst": "Tobacconist",
    "tobacenst.": "Tobacconist",
    "tobnc'nst": "Tobacconist",
    "tobccnst": "Tobacconist",
    "tobaconst": "Tobacconist",
    "tobnsts": "Tobacconists",
    "tobacnsts": "Tobacconists",
    "who. tobccnsts": "Wholesale Tobacconists",
    "tobacnst etc.": "Tobacconist, etc.",
    "furn. dlrs": "Furniture Dealers",
    "furn. dlr": "Furniture Dealer",
    "port butch'r": "Pork Butcher",
    "pork butch'r": "Pork Butcher",
    "porkbutch'r": "Pork Butcher",
    "prk butcher": "Pork Butcher",
    "pork butchr": "Pork Butcher",
    "butchr": "Butcher",
    "butch'r": "Butcher",
    "butchrs": "Butchers",
    "pawnbrokr": "Pawnbroker",
    "pwnbrkr": "Pawnbroker",
    "pwnbrokr": "Pawnbroker",
    "shipbrokr": "Shipbroker",
    "ship brokr": "Shipbroker",
    "hairdrsr": "Hairdresser",
    "hairdressr": "Hairdresser",
    "hairdressrs": "Hairdressers",
    "hairdrssrs": "Hairdressers",
    "pork butcher and sausage manufact'r": "Pork Butcher and Sausage Manufacturer",
    "boarding ho": "Boarding House",
    "board'g ho": "Boarding House",
    "universal outfitters boot dlrs": "Universal Outfitters Boot Dealers",
    "wardrobe dl": "Wardrobe Dealer",
    "engrocers": "Greengrocers",
    "greengrocr": "Greengrocer",
    "greengrocrs": "Greengrocers",
    "ship chan.": "Ship Chandlers",
    "ship chan": "Ship Chandlers",
}

HOUSE_PREFIX_RE = re.compile(
    r"\b(Boarding|Board'g|Lodging|Lodg|School|Station|Refreshm(?:en)?t|Malt|Mission|Off Beer|Church|Chapel|Manager's|Coffee|Eating|Public|Beer|Ale)\s+Ho\.?\b",
    re.IGNORECASE,
)


def normalize_trade(raw: str) -> str:
    t = (raw or "").strip()
    if not t:
        return t

    # Repair embedded CSV leak if present
    if ",,, resident," in t:
        t = t.split(",,, resident,", 1)[0].strip()

    low = t.lower()
    if low in EXACT_MAP:
        return EXACT_MAP[low]

    out = t
    out = re.sub(r"\bFurn\.?\s+", "Furniture ", out, flags=re.I)
    out = re.sub(r"\bGenl\.?\s+", "General ", out, flags=re.I)
    out = re.sub(r"\bDlrs\.?\b", "Dealers", out, flags=re.I)
    out = re.sub(r"\bDlr\.?\b", "Dealer", out, flags=re.I)
    out = re.sub(r"\bDl\.?$", "Dealer", out, flags=re.I)
    out = re.sub(r"\bPrk\.?\s+Butcher", "Pork Butcher", out, flags=re.I)
    out = re.sub(r"\bPort\s+Butch'?r\b", "Pork Butcher", out, flags=re.I)
    out = re.sub(r"\bButch'?rs\b", "Butchers", out, flags=re.I)
    out = re.sub(r"\bButch'?r\b", "Butcher", out, flags=re.I)
    out = re.sub(r"\bShipbrokr\b", "Shipbroker", out, flags=re.I)
    out = re.sub(r"\bBrokr\b", "Broker", out, flags=re.I)
    out = re.sub(r"\bDrsr\b", "Dresser", out, flags=re.I)
    out = re.sub(r"\bManufact'?rs\b|\bManuf'?rs\b|\bManufrts\b", "Manufacturers", out, flags=re.I)
    out = re.sub(r"\bManufact'?r\b|\bManufr(?:'tr)?\b", "Manufacturer", out, flags=re.I)
    out = re.sub(r"\bToba[co']?nsts\b", "Tobacconists", out, flags=re.I)
    out = re.sub(r"\bToba[co']?nst\b|\bTobcnst\b", "Tobacconist", out, flags=re.I)
    out = HOUSE_PREFIX_RE.sub(lambda m: f"{m.group(1)} House", out)
    out = re.sub(r"\bRefreshmt\s+House\b", "Refreshment House", out, flags=re.I)
    out = re.sub(r"\bBoard'g\s+House\b", "Boarding House", out, flags=re.I)
    out = re.sub(r"\bLodg\s+House\b", "Lodging House", out, flags=re.I)

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
            changed[(old[:60], new[:60])] += 1

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Normalized {sum(changed.values())} trade rows across {len(changed)} distinct patterns.")
    for (o, n), cnt in changed.most_common(30):
        print(f"  {cnt:4d}: {o!r} -> {n!r}")


if __name__ == "__main__":
    main()
