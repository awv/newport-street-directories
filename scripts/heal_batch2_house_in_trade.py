#!/usr/bin/env python3
"""
heal_batch2_house_in_trade.py
=============================
Batch 2 of Strayed Column Healing (year <= 1936):
1. HOUSE_IN_TRADE:
   Moves unambiguous suburban villa, house, cottage, lodge, hall, Welsh-named,
   and pub/building names trapped in `trade` into `building_name` (when `building_name` is empty).
   Expands abbreviations (`ho` -> `House`, `cot` -> `Cottage`, `vil` -> `Villa`) cleanly.
2. Bonus Trade Normalizations surfaced by the audit:
   - Engine Dvr. -> Engine Driver
   - Lathrendr -> Lathrender
   - Dectr -> Decorator
   - Electcn -> Electrician
   - Crpntr / Carpntr -> Carpenter
   - Bdg Ho -> Boarding House
   - Lodging Ho -> Lodging House
   - Eating Ho -> Eating House
   - Chemical Wks -> Chemical Works
3. Rebuilds site data, trades data, and stats data (unless --dry-run is passed).
"""

import os
import sys
import csv
import re
import shutil
import subprocess
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_batch2_house")
MAX_YEAR = 1936

HOUSE_STRICT_RE = re.compile(
    r"^(?:"
    r"(?:bryn|plas|ty|glan|nant|cwm|pant|pen|llan|maes|coed|bron|caer|tre)[\s\-][a-z'\-]+|"
    r"the\s+(?:laurels|firs|elms|oaks|pines|cedars|beeches|sycamores|poplars|willows|chestnuts|holly|ivy|fern|ferns|hollies|rose|hazel|ash|elm|oak|grove|grange|mount|haven|nook|bungalow|lodge|manor|cottage|villa|laurel|elms|acacias|limes|chestnut|orchard|rectory|vicarage|priory|abbey|tower|castle|hall|court|meadows|paddock|woods|dene)|"
    r"[a-z'\-\s\.]+\s+(?:ho\.?|house|villa|villas|cot\.?|cottage|cottages|lodge|hall|court|manor|grange|farm|castle|vale|view|mount|grove|dene|lea)\.?$|"
    r"[a-z]+(?:dene|hurst|croft|holme|leigh|vale|view|wood|grove|mead|mount|brook|glen|side|wick|combe|thorpe|cliff|cliffe|dale)\.?$|"
    r"st\.?\s+(?:ives|malo|elmo|audries|helens|helen's|mary's|john's|david's|george's|anne's|paul's|peter's|thomas|james|edward|martin|nicholas|stephen|michael|joseph|lawrence|agnes|claire|albans|leonards|catherine|margaret|bartholomew|vincent|clair|clare)|"
    r"sunnyside|claremont|lawrenny|cartref|hatherleigh|ingleside|pendennis|britannia|royal\s+albert|windsor\s+castle|hare\s+and\s+greyhound|temple\s+of\s+health|dock\s+house|serne\s+ho\.?|mon\s+abria?|ivydene|lorna\s+doone|revelstoke|lydbrook|selsdon|tyrone|wellesley|chertsey|monteville|merridale|pendre"
    r")$",
    re.I
)

NOT_A_HOUSE_RE = re.compile(
    r"\b(?:lodging|eating|boarding|bdg|coffee|cocoa|public|beer|ale|refreshment|dining|temperance|station|police|customs|workhouse|poor\s*law|warehouse|wareho|wharf|wf|works|wks|yard|yd|depot|office|offices|shop|stores|store|factory|mill|mills|foundry|brewery|bakery|dairy|laundry|garage|club|institute|school|college|hospital|infirmary|dispensary|church|chapel|mission|theatre|cinema|bank|exchange|repository|mason|masons|builder|builders|carpenter|smith|engineer|driver|dvr|clerk|agent|manager|collector|dealer|merchant|trimmer|shipper|maker|mkr|worker|labourer|junr|senr|jr|sr|void|vacant|apartments|lodgings|private|retired|widow|spinster|gentleman|lathrendr|dectr|electcn|crpntr|masseuse)\b",
    re.I
)

# Common surnames or trades ending in -wood/-field/-side/-hill/-dale/-leigh/-brook that could appear in trade accidentally
SURNAME_OR_TRADE_FALSE_POS = {
    "wood", "field", "hill", "brook", "dale", "leigh", "side", "grove", "hurst",
    "haywood", "underwood", "greenwood", "blackwood", "oakwood", "sherwood",
    "mayfield", "springfield_surname", "burnside", "eastwood", "westwood",
    "norwood", "ashwood", "elmwood", "hollywood", "stanley", "ashley", "bradley",
    "harley", "shirley", "kelly", "bailey", "riley", "buckley", "crossley",
    "hartley", "bentleigh", "whitley", "moseley", "cowley", "crowley", "hawley",
    "radcliffe", "sutcliffe", "hinchliffe", "cunliffe", "stancliffe",
    "holme", "hulme", "holmes", "baird", "fairbairn"
}

TRADE_EXPANSIONS = [
    (re.compile(r"^engine\s*dvr\.?$", re.I), "Engine Driver"),
    (re.compile(r"^lathrend'?r\.?$", re.I), "Lathrender"),
    (re.compile(r"^dect'?r\.?$", re.I), "Decorator"),
    (re.compile(r"^elect'?cn\.?$", re.I), "Electrician"),
    (re.compile(r"^(?:crpntr|carpntr)\.?$", re.I), "Carpenter"),
    (re.compile(r"^bdg\s*ho\.?$", re.I), "Boarding House"),
    (re.compile(r"^lodging\s*ho\.?$", re.I), "Lodging House"),
    (re.compile(r"^eating\s*ho\.?$", re.I), "Eating House"),
    (re.compile(r"^chemical\s*wks\.?$", re.I), "Chemical Works"),
]

def normalize_building_name(b):
    b = b.strip().rstrip(".")
    b = re.sub(r"\bho$", "House", b, flags=re.I)
    b = re.sub(r"\bvil$", "Villa", b, flags=re.I)
    b = re.sub(r"\bcot$", "Cottage", b, flags=re.I)
    b = re.sub(r"\bbldgs$", "Buildings", b, flags=re.I)
    words = b.split()
    out = []
    for w in words:
        if re.match(r"^[a-z]+'[a-z]+$", w, re.I):
            parts = w.split("'")
            out.append(parts[0].capitalize() + "'" + parts[1].lower())
        elif "-" in w:
            out.append("-".join(p.capitalize() if p.lower() not in {"y", "yr"} else p.lower() for p in w.split("-")))
        elif w.lower() in {"of", "the", "and", "in", "on", "at", "y", "yr"} and out:
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    return " ".join(out)

def main():
    dry_run = "--dry-run" in sys.argv
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    moved = Counter()
    bonus = Counter()

    if not dry_run:
        print(f"Creating backup: {BACKUP_CSV}...")
        shutil.copyfile(DATA_CSV, BACKUP_CSV)

    for r in rows:
        yr = (r.get("year") or "").strip()
        if yr.isdigit() and int(yr) > MAX_YEAR:
            continue
        bn = (r.get("building_name") or "").strip()
        sn = (r.get("surname") or "").strip()
        tr = (r.get("trade") or "").strip()
        if not tr:
            continue

        # 1. Bonus trade expansions
        matched_trade = False
        for pat, target in TRADE_EXPANSIONS:
            if pat.match(tr):
                bonus[f"{tr} -> {target}"] += 1
                if not dry_run:
                    r["trade"] = target
                matched_trade = True
                break
        if matched_trade:
            continue

        # 2. House-in-trade extraction
        if not bn and sn and tr.lower().rstrip(".") not in SURNAME_OR_TRADE_FALSE_POS:
            if HOUSE_STRICT_RE.match(tr) and not NOT_A_HOUSE_RE.search(tr):
                canon_bn = normalize_building_name(tr)
                moved[canon_bn] += 1
                if not dry_run:
                    r["building_name"] = canon_bn
                    r["trade"] = ""

    print(f"House-in-trade records {'matched' if dry_run else 'healed'}: {sum(moved.values()):,} ({len(moved)} unique buildings)")
    print("Top 35 house names:")
    for k, v in moved.most_common(35):
        print(f"  {v:4d} | {k}")

    print(f"\nBonus trade normalizations {'matched' if dry_run else 'healed'}: {sum(bonus.values()):,}")
    for k, v in bonus.most_common(15):
        print(f"  {v:4d} | {k}")

    if dry_run:
        return

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("\nRebuilding site data and JSON indexes...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_site_data.py")], check=True)
    print("\nRebuilding trades data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_trades_data.py")], check=True)
    print("\nRebuilding stats data...")
    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "build_stats_data.py")], check=True)

    if os.path.exists(BACKUP_CSV):
        os.remove(BACKUP_CSV)
        print("Removed temporary backup file.")

    print("\n[SUCCESS] Batch 2 house names healed and site rebuilt!")

if __name__ == "__main__":
    main()
