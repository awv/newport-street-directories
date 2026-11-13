#!/usr/bin/env python3
"""20th-Century Trade & Business Normalization Engine across all years in data.csv (including 1971)."""
import csv
import re
import shutil
from collections import Counter
from pathlib import Path

DATA_CSV = Path(__file__).resolve().parent.parent / "data.csv"
BACKUP_CSV = Path(__file__).resolve().parent.parent / "data.csv.bak_before_trade_norm"

NAME_TRADE_RE = re.compile(
    r"^(Wm\.?|John|Geo\.?|Hy\.?|Thos\.?|Chas\.?|Jas\.?|Robt\.?|Edw\.?|Richd\.?|Fredk\.?|Saml\.?|Jos\.?|Benj\.?|Alfd\.?|Arth\.?),\s+([A-Za-z][A-Za-z .&'-]+)$"
)
MRS_MISS_NAME_RE = re.compile(r"^(Mrs\.?|Miss)\s+([A-Z][a-z]+\.?)$")
GEN_SUFFIX_RE = re.compile(r"^(Junr?\.?|Senr?\.?)$", re.IGNORECASE)

# Explicit, unambiguous OCR misspellings & dropped-vowel directory abbreviations
# Key: lowercased stripped trade -> Canonical trade
EXACT_TRADE_MAP = {
    "tel. linesmn": "Telephone Linesman",
    "tel. linemn": "Telephone Linesman",
    "tel. linesman": "Telephone Linesman",
    "eng. drv": "Engine Driver",
    "travellr": "Traveller",
    "ironmongr": "Ironmonger",
    "ironmngr": "Ironmonger",
    "refshmts": "Refreshments",
    "labouer": "Labourer",
    "carperntr": "Carpenter",
    "blacksmh": "Blacksmith",
    "shipwrght": "Shipwright",
    "shipwight": "Shipwright",
    "electricn": "Electrician",
    "decoratr": "Decorator",
    "stonemasn": "Stonemason",
    "signalmn": "Signalman",
    "signlmn": "Signalman",
    "quarrymn": "Quarryman",
    "dairymn": "Dairyman",
    "sailmakr": "Sailmaker",
    "cellerman": "Cellarman",
    "saddlr": "Saddler",
    "sadler": "Saddler",
    "gardner": "Gardener",
    "gardenr": "Gardener",
    "steelworkr": "Steelworker",
    "coal shippr": "Coal Shipper",
    "railway grd": "Railway Guard",
    "factory hnd": "Factory Hand",
    "wiremn": "Wireman",
    "solicitrs": "Solicitors",
    "shipbrokrs": "Shipbrokers",
    "packr": "Packer",
    "glass wrks": "Glass Works",
    "gas workr": "Gas Worker",
    "gasworkr": "Gas Worker",
    "gas wrkr": "Gas Worker",
    "sawyr": "Sawyer",
    "pilotsmn": "Pilotsman",
    "hobler": "Hobbler",
    "green-grocer": "Greengrocer",
    "newsagt": "Newsagent",
    "bldr": "Builder",
    "dlr": "Dealer",
}

EDITORIAL_CLEAR = {
    "[see arcades.]",
    "continuation/out of order on page",
    "[lower-road.]",
}


def main():
    with open(DATA_CSV, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    shutil.copy2(DATA_CSV, BACKUP_CSV)
    stats = Counter()

    for r in rows:
        tr = r["trade"].strip()
        fn = r["forename"].strip()
        sn = r["surname"].strip()
        bn = r["building_name"].strip()

        # Clean literal \N in building_name (1971 SQL export artifact)
        if bn == "\\N":
            r["building_name"] = ""
            stats["1971_bn_null"] += 1

        if not tr:
            continue

        tr_low = tr.lower()

        # Pass 1: 1971 export artifacts
        if tr in ("t\\t", "t\t"):
            r["trade"] = ""
            stats["1971_t_tab_cleared"] += 1
            continue
        if tr == "N" and bn in ("\\N", ""):
            r["trade"] = ""
            stats["1971_N_cleared"] += 1
            continue

        # Pass 2: Bracketed void / editorial notes
        if tr_low == "[void]":
            r["trade"] = "Void"
            stats["bracket_void_norm"] += 1
            continue
        if tr_low in EDITORIAL_CLEAR:
            r["trade"] = ""
            stats["editorial_note_cleared"] += 1
            continue

        # Pass 3: Generational suffix in trade
        if GEN_SUFFIX_RE.match(tr) and sn:
            if not sn.lower().endswith(tr_low.rstrip(".")):
                r["surname"] = f"{sn} {tr}"
            r["trade"] = ""
            stats["gen_suffix_moved"] += 1
            continue

        # Pass 4: Forename + Trade or Mrs/Miss Name packed into trade when forename is empty
        if not fn and sn:
            m1 = NAME_TRADE_RE.match(tr)
            if m1:
                r["forename"] = m1.group(1)
                new_tr = m1.group(2).strip()
                r["trade"] = new_tr.title() if new_tr.islower() else new_tr
                stats["name_trade_unpacked"] += 1
                continue
            m2 = MRS_MISS_NAME_RE.match(tr)
            if m2:
                r["forename"] = tr
                r["trade"] = ""
                stats["mrs_name_moved"] += 1
                continue

        # Pass 5: Dvr context-aware expansion
        if tr == "Dvr":
            if sn.lower() == "van":
                r["surname"] = ""
                r["trade"] = "Van Driver"
                stats["dvr_van"] += 1
            elif fn.lower().endswith(" eng."):
                r["forename"] = fn[:-5].strip()
                r["trade"] = "Engine Driver"
                stats["dvr_eng"] += 1
            else:
                r["trade"] = "Driver"
                stats["dvr_plain"] += 1
            continue

        # Pass 6: Exact-match OCR & abbreviation dictionary
        if tr_low in EXACT_TRADE_MAP:
            r["trade"] = EXACT_TRADE_MAP[tr_low]
            stats["ocr_abbr_normalized"] += 1
            continue

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Trade & Business Normalization complete:")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"Total adjustments: {sum(stats.values())}")
    print(f"Backup written to: {BACKUP_CSV}")


if __name__ == "__main__":
    main()
