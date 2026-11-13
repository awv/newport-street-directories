#!/usr/bin/env python3
"""
heal_batch3_trades_and_businesses.py
====================================
Batch 3 of Strayed Column Healing (year <= 1936):
1. TRADE_IN_SURNAME:
   Moves strict non-surname occupations trapped in `surname` into `trade`
   (e.g., sn='Architect', fn='And', tr='Surveyor' -> tr='Architect & Surveyor';
    sn='upholsterer' -> tr='Upholsterer').
   Preserves genuine surnames like 'Slater' when paired with a personal forename.
2. BUSINESS_SPLIT:
   - Rejoins trailing corporate suffixes stuck in `surname` with their name in `forename`
     (e.g., sn='Ltd.', fn='Lloyd & Yorath' -> sn='Lloyd & Yorath Ltd.', fn='').
   - Moves corporate names trapped in `forename` with blank `surname` into `surname`
     (e.g., sn='', fn="Eastman's Ltd." -> sn="Eastman's Ltd.", fn='').
   - Rejoins split `Bros.` / `& Co. Ltd.` / `Garage` from `forename` onto `surname`
     (e.g., sn='Houghton', fn='Bros.' -> sn='Houghton Bros.', fn='';
      sn='Elliotts', fn='Garage' -> sn='Elliotts Garage', fn='', tr='Garage').
   Preserves genuine surnames like 'Chambers' and 'Brothers' with personal forenames.
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
BACKUP_CSV = os.path.join(PROJECT_ROOT, "data.csv.bak_before_batch3_biz")
MAX_YEAR = 1936

STRICT_TRADE_IN_SURNAME_RE = re.compile(
    r"^(?:"
    r"dental\s+surgeon|building\s+contr.*|coal\s+(?:merchant|mercht|trimmer|shipper|exporter|heaver|seller|tipper)|"
    r"insurance\s+(?:agent|broker)|commission\s+agent|estate\s+agent|house\s+agent|shipping\s+agent|"
    r"licensed\s+victualler|general\s+(?:dealer|shop|merchant)|marine\s+store|"
    r"engineer|civil\s+engineer|mechanical\s+engineer|electrical\s+engineer|motor\s+engineer|consulting\s+engineer|"
    r"solicitor|accountant|chartered\s+accountant|architect|surveyor|auctioneer|valuer|"
    r"ironmonger|tobacconist|confectioner|greengrocer|fruiterer|fishmonger|poulterer|cheesemonger|"
    r"watchmaker|clockmaker|jeweller|silversmith|optician|chemist|druggist|pharmacist|"
    r"boilermaker|shipwright|wheelwright|millwright|coachbuilder|patternmaker|blacksmith|"
    r"shoemaker|bootmaker|cordwainer|dressmaker|milliner|upholsterer|cabinetmaker|"
    r"hairdresser|photographer|printer|stationer|bookseller|newsagent|"
    r"plasterer|plumber|glazier|decorator|bricklayer|stonemason|"
    r"schoolmaster|schoolmistress|stationmaster|harbourmaster|postmaster|"
    r"publican|innkeeper|victualler|pawn\s*broker|pawnbroker"
    r")$",
    re.I
)

TRAILING_CORP_IN_SN = re.compile(r"^(?:ltd\.?|limited|co\.?|&\s*co\.?(?:\s*ltd\.?)?|&\s*sons?|sons?|bros\.?)$", re.I)
CORP_SUFFIX_IN_FN = re.compile(r"^(?:bros\.?|&\s*co\.?(?:\s*ltd\.?)?|&\s*sons?|&\s*son|ltd\.?|limited|garage|stores|motors|works)$", re.I)
FULL_CORP_IN_FN = re.compile(r"\b(?:ltd\.?|limited|&\s*co\.?|&\s*sons?|bros\.?|brothers|garage|motors|supply\s+co|printing\s+co|building\s+soc)\b", re.I)

def normalize_trade(t):
    t = t.strip()
    if not t:
        return ""
    if t.isupper() or t.islower():
        return " ".join(w.capitalize() if w.lower() not in {"and", "of", "&"} else w.lower() for w in t.split())
    return t[0].upper() + t[1:] if len(t) > 1 else t.upper()

def main():
    dry_run = "--dry-run" in sys.argv
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    tis_counts = Counter()
    biz_counts = Counter()

    if not dry_run:
        print(f"Creating backup: {BACKUP_CSV}...")
        shutil.copyfile(DATA_CSV, BACKUP_CSV)

    for r in rows:
        yr = (r.get("year") or "").strip()
        if yr.isdigit() and int(yr) > MAX_YEAR:
            continue
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        bn = (r.get("building_name") or "").strip()
        tr = (r.get("trade") or "").strip()

        # 1. TRADE_IN_SURNAME
        if sn and STRICT_TRADE_IN_SURNAME_RE.match(sn):
            # Case A: sn='Architect', fn='And', tr='Surveyor'
            if sn.lower() == "architect" and fn.lower() == "and" and "surveyor" in tr.lower():
                tis_counts["Architect & Surveyor"] += 1
                if not dry_run:
                    r["surname"] = ""
                    r["forename"] = ""
                    r["trade"] = "Architect & Surveyor"
                continue
            # Case B: blank forename -> pure strayed occupation
            if not fn:
                new_tr = normalize_trade(sn)
                tis_counts[new_tr] += 1
                if not dry_run:
                    r["surname"] = ""
                    if not tr or tr.lower() == new_tr.lower():
                        r["trade"] = new_tr
                    else:
                        # e.g. tr='Coventry Permanent Economic Building Soc', sn='valuer'
                        if "soc" in tr.lower() or "company" in tr.lower():
                            r["surname"] = tr
                            r["trade"] = new_tr
                        else:
                            r["trade"] = f"{new_tr}, {tr}"
                continue

        # 2. BUSINESS_SPLIT
        # Rule A: Trailing corporate suffix stuck in surname (e.g. sn='Ltd.', fn='Lloyd & Yorath')
        if sn and fn and TRAILING_CORP_IN_SN.match(sn):
            # Skip 'Brothers' when fn is a personal name like 'Geo.'
            if sn.lower() in {"brothers", "sons"} and re.match(r"^[A-Z][a-z]{1,8}\.?$", fn):
                pass
            else:
                combined = f"{fn} {sn}".strip()
                biz_counts[f"REJOIN_SN_SUFFIX: {combined}"] += 1
                if not dry_run:
                    r["surname"] = combined
                    r["forename"] = ""
                continue

        # Rule B: Corporate name in forename with blank surname (e.g. sn='', fn="Eastman's Ltd.")
        if not sn and fn and FULL_CORP_IN_FN.search(fn) and not TRAILING_CORP_IN_SN.match(fn):
            biz_counts[f"MOVE_FN_TO_SN: {fn}"] += 1
            if not dry_run:
                r["surname"] = fn
                r["forename"] = ""
            continue

        # Rule C: Split suffix or 'Garage' in forename after surname (e.g. sn='Houghton', fn='Bros.'; sn='Elliotts', fn='Garage')
        if sn and fn and sn.lower() != "chambers":
            if CORP_SUFFIX_IN_FN.match(fn) or re.match(r"^[A-Z]\.?\s*&\s*Co\.?\s*Ltd\.?$", fn, re.I):
                combined = f"{sn} {fn}".strip()
                biz_counts[f"REJOIN_FN_SUFFIX: {combined}"] += 1
                if not dry_run:
                    r["surname"] = combined
                    r["forename"] = ""
                    if fn.lower() == "garage" and not tr:
                        r["trade"] = "Garage"
                continue

    print(f"TRADE_IN_SURNAME records {'matched' if dry_run else 'healed'}: {sum(tis_counts.values()):,}")
    for k, v in tis_counts.most_common(15):
        print(f"  {v:4d} | {k}")

    print(f"\nBUSINESS_SPLIT records {'matched' if dry_run else 'healed'}: {sum(biz_counts.values()):,}")
    for k, v in biz_counts.most_common(20):
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

    print("\n[SUCCESS] Batch 3 trades and businesses healed and site rebuilt!")

if __name__ == "__main__":
    main()
