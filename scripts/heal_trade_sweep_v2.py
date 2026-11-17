#!/usr/bin/env python3
"""Comprehensive 5-layer trade normalization sweep (vowel-drops, apostrophe contractions, period abbreviations, OCR typos, Void cleanup)."""
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

EXACT_MAP = {
    "void.": "Void",
    "void, do": "Void",
    "wareh'man": "Warehouseman",
    "wareh'semn": "Warehouseman",
    "wareh'sem'n": "Warehouseman",
    "warehousemn": "Warehouseman",
    "dres'r": "Dresser",
    "mas'n": "Mason",
    "cop'smith": "Coppersmith",
    "w'rfingers.": "Wharfingers",
    "w'rfingers": "Wharfingers",
    "w'fingers": "Wharfingers",
    "ironwork'r": "Ironworker",
    "ironwoker": "Ironworker",
    "ironwrkr": "Ironworker",
    "ironwker": "Ironworker",
    "check'r": "Checker",
    "eng'r": "Engineer",
    "sheet w'kr": "Sheet Worker",
    "shipch'ndlrs": "Shipchandlers",
    "rest't": "Restaurant",
    "ptr & decr'tr": "Painter & Decorator",
    "shoe'g smith": "Shoeing Smith",
    "sl'ghterman": "Slaughterman",
    "haul'r": "Haulier",
    "g'ngcr": "Greengrocer",
    "upholstr'r": "Upholsterer",
    "lcksmith": "Locksmith",
    "blksmith": "Blacksmith",
    "bricklyer": "Bricklayer",
    "electrican": "Electrician",
    "newsagnt": "Newsagent",
    "boilermakr": "Boilermaker",
    "boiler-maker": "Boilermaker",
    "stonemsn": "Stonemason",
    "shipwght": "Shipwright",
    "stevedr": "Stevedore",
    "solictr": "Solicitor",
    "caretakr": "Caretaker",
    "stewrd": "Steward",
    "stwd": "Steward",
    "travelr": "Traveller",
    "trvller": "Traveller",
    "travlr": "Traveller",
    "tvlr": "Traveller",
    "buildr": "Builder",
    "portr": "Porter",
    "eng driver": "Engine Driver",
    "eng. driver": "Engine Driver",
    "engineer driver": "Engine Driver",
}

WORD_MAP = {
    "supt": "Superintendent",
    "labr": "Labourer",
    "drvr": "Driver",
    "drivr": "Driver",
    "dvr": "Driver",
    "insp": "Inspector",
    "inspt": "Inspector",
    "carptr": "Carpenter",
    "carprntr": "Carpenter",
    "carpntr": "Carpenter",
    "cptr": "Carpenter",
    "crptr": "Carpenter",
    "mercht": "Merchant",
    "merchts": "Merchants",
    "merch'ts": "Merchants",
    "merch": "Merchant",
    "mcht": "Merchant",
    "mchts": "Merchants",
    "mer": "Merchant",
    "sergt": "Sergeant",
    "bldr": "Builder",
    "bldrs": "Builders",
    "rlwy": "Railway",
    "mftr": "Manufacturer",
    "mftrs": "Manufacturers",
    "manuf'tr": "Manufacturer",
    "trimmr": "Trimmer",
    "trmr": "Trimmer",
    "agnt": "Agent",
    "agt": "Agent",
    "wrks": "Works",
    "makr": "Maker",
    "mkrs": "Makers",
    "strs": "Stores",
    "mangr": "Manager",
    "mngr": "Manager",
    "hlpr": "Helper",
    "blwr": "Blower",
    "clnr": "Cleaner",
    "pntr": "Painter",
    "schl": "School",
    "plmbr": "Plumber",
    "plbr": "Plumber",
    "smth": "Smith",
    "prptr": "Proprietor",
    "wghr": "Weigher",
    "clrk": "Clerk",
    "sec": "Secretary",
    "ins": "Insurance",
    "insur": "Insurance",
    "eng": "Engineer",
    "surg": "Surgeon",
    "schoolrm": "Schoolroom",
    "dist": "District",
    "solctr": "Solicitor",
    "solct": "Solicitor",
    "solc": "Solicitor",
    "solr": "Solicitor",
    "solctrs": "Solicitors",
    "acct": "Accountant",
    "acct'nt": "Accountant",
    "accts": "Accountants",
    "wiredrwr": "Wiredrawer",
    "cellarmn": "Cellarman",
    "hoistmn": "Hoistman",
    "cabmn": "Cabman",
    "policemn": "Policeman",
    "firemn": "Fireman",
    "boatmn": "Boatman",
    "draymn": "Drayman",
    "carmn": "Carman",
    "watermn": "Waterman",
    "signalmn": "Signalman",
    "pointsman": "Pointsman",
}

TOKEN_RE = re.compile(r"\b([A-Za-z][A-Za-z']{1,18})(\.?)")


def normalize_trade(raw: str) -> str:
    t = (raw or "").strip()
    if not t:
        return t
    low = t.lower()
    if low in EXACT_MAP:
        return EXACT_MAP[low]

    def repl(m):
        word = m.group(1)
        dot = m.group(2)
        lw = word.lower()
        if lw in WORD_MAP:
            return WORD_MAP[lw]
        # Only expand trailing dot on known abbreviations; preserve dot on others
        if lw.endswith("mn") and len(lw) >= 6 and lw not in ("hymn", "autumn", "column", "solemn"):
            return word[:-2] + "man"
        return word + dot

    # Protect "(Eng.)" medical qualification from becoming "(Engineer)"
    if "(eng.)" in low:
        return t

    out = TOKEN_RE.sub(repl, t)
    out = re.sub(r"\bComm?\.?\s+For\s+Oaths\b", "Commissioner for Oaths", out, flags=re.I)
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
    for (o, n), cnt in changed.most_common(35):
        print(f"  {cnt:4d}: {o!r} -> {n!r}")


if __name__ == "__main__":
    main()
