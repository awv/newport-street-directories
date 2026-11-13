#!/usr/bin/env python3
"""
Batch 8 trade normalizations:
* Junr. Labourer / Junr. Labr -> Junior Labourer
* H.M.'s Customs variants -> H.M.'s Customs
* Whsmn -> Warehouseman
* Tram Inspctr / Inspt. / Inspct / Insptr / Insp. / Inspr. / Insprtr / Inspect -> Tram Inspector
* Sheetwghr / Sheet Wghr -> Sheetweigher
* Accnt / Acc'Nt / Acc'Nt'Nt / Acc'Nt'T / Accnt'Nt -> Accountant (+ Turf Accnt -> Turf Accountant)
* Capt. / Capt -> Captain (Captain, Tug Captain, Tugboat Captain, Captain Tugboat, Captain S.S.)
* Tax Insp -> Tax Inspector
* Brickm'Kr -> Brickmaker
"""
import csv
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(BASE_DIR, "data.csv")


def normalize_trade(t: str) -> str:
    orig = t.strip()
    if not orig:
        return orig
    out = orig

    # Repair any double-expansion from prior run
    out = out.replace("Captainain", "Captain").replace("Captainr", "Captain").replace("Captainn", "Captain")
    out = out.replace("Tram Inspectoror", "Tram Inspector").replace("Tram Inspectortr", "Tram Inspector")
    out = out.replace("Tax Inspectorector", "Tax Inspector")
    out = out.replace("Accountantr", "Accountant")

    # 1. Junr. Labourer / Junr. Labr -> Junior Labourer
    out = re.sub(r"\bjunr\.?\s+(?:labr|labourer)(?:\.|\b)", "Junior Labourer", out, flags=re.I)

    # 2. H.M.'s Customs variants -> H.M.'s Customs
    out = re.sub(r"\bh\.?\s*m\.?\s*(?:'?s)?\s*cust(?:om)?s?(?:'s)?\b", "H.M.'s Customs", out, flags=re.I)
    out = re.sub(r"\bh\.?\s*m\.?\s*(?:'?s)?\s*custms\b", "H.M.'s Customs", out, flags=re.I)

    # 3. Whsmn -> Warehouseman
    out = re.sub(r"\bwhsmn(?:\.|\b)", "Warehouseman", out, flags=re.I)

    # 4. Tram Insp* -> Tram Inspector
    out = re.sub(r"\btram\s+insp(?:ctr|tr|ct|t|r|ect|ector)?(?:\.(?!\w)|\b)", "Tram Inspector", out, flags=re.I)

    # 5. Sheetwghr / Sheet Wghr -> Sheetweigher
    out = re.sub(r"\bsheet\s*wghr(?:\.|\b)", "Sheetweigher", out, flags=re.I)

    # 6. Accnt / Acc'Nt / Acc'Nt'Nt / Acc'Nt'T / Accnt'Nt -> Accountant
    out = re.sub(r"\bacc'?nt(?:'?(?:nt|t))?(?:\.(?!\w)|\b)", "Accountant", out, flags=re.I)
    out = re.sub(r"\b(?:chartered\s+)?accntnts?(?:\.(?!\w)|\b)", lambda m: ("Chartered " if "chartered" in m.group(0).lower() else "") + "Accountants", out, flags=re.I)

    # 7. Capt. / Capt -> Captain
    out = re.sub(r"\btugbt\s+capt(?:\.(?!\w)|\b)", "Tugboat Captain", out, flags=re.I)
    out = re.sub(r"\bcapt(?:\.(?!\w)|\b)", "Captain", out, flags=re.I)

    # 8. Tax Insp -> Tax Inspector
    out = re.sub(r"\btax\s+insp(?:ctr|tr|ct|t|r|ector)?(?:\.(?!\w)|\b)", "Tax Inspector", out, flags=re.I)

    # 9. Brickm'Kr -> Brickmaker
    out = re.sub(r"\bbrickm'?kr(?:\.|\b)", "Brickmaker", out, flags=re.I)

    # Clean up any leftover trailing dot / 's
    out = re.sub(r"\b(Captain|Tram Inspector|Tax Inspector|Accountant|Accountants)\.", r"\1", out)
    out = out.replace("H.M.'s Customs's", "H.M.'s Customs")

    return out


def main():
    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changes = Counter()
    for r in rows:
        if int(r["year"]) > 1936:
            continue
        old = r["trade"].strip()
        if not old:
            continue
        new = normalize_trade(old)
        if new != old:
            changes[(old, new)] += 1
            r["trade"] = new

    with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total rows updated: {sum(changes.values())}")
    for (o, n), c in changes.most_common():
        print(f"  {c:4d} | {o} -> {n}")


if __name__ == "__main__":
    main()
