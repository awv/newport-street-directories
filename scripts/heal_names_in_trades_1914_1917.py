#!/usr/bin/env python3
"""
Heal name-in-trade bleeding and corporate-suffix splits (especially in 1914 & 1917):
1. Corporate suffixes in `surname` (Ltd., Limited, Co., Bros., & Co., & Sons) where the real
   surname leaked into `trade` (e.g. J. P. | Ltd. | Handford -> J. P. Ltd. | Handford | '').
2. Empty `surname` + leaked surname in `trade` (e.g. J. P. | '' | Handford) verified via
   adjacent-year address history or surname-vs-trade frequencies.
3. Comma-prefixed surname in `trade` matching address history (e.g. 1915 Handford, Shipping...).
4. "Surname Initials" packed into `forename` when `surname` is empty in 1914/1917.
5. OCR typos: Shiping -> Shipping, Ironmgs -> Ironmongers.
"""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"

CORP_SURNAME_RE = re.compile(
    r"^(Ltd\.?|Limited|Co\.?|Bros\.?|&\s*Co\.?|&\s*Sons\.?|&\s*Son\.?)$", re.IGNORECASE
)
PERSON_PACKED_RE = re.compile(
    r"^([A-Z][a-z'’-]{2,})\s+([A-Z]\.(?:\s*[A-Z]\.)*)$"
)
CORP_OR_INST_WORDS = re.compile(
    r"(&|\bLtd\b|\bCo\.?\b|\bLimited\b|\bSons?\b|\bBros\b|\bSchools?\b|\bChapel\b|\bChurch\b|"
    r"\bOffice|\bWorks\b|\bBank\b|\bHotel\b|\bInn\b|\bArms\b|\bHall\b|\bClub\b|\bSociety\b|"
    r"\bDaily\b|\bNews\b|\bEcho\b|\bStores?\b|\bDep[oô]t\b|\bFactory\b|\bFoundry\b|\bBrewery\b)",
    re.IGNORECASE,
)
SAFE_NON_SURNAME_TRADES = {
    "void", "bazaar", "stores", "manager", "manageress", "builders", "builder",
    "tailor", "tailors", "grocer", "grocers", "butcher", "butchers", "baker",
    "bakers", "draper", "drapers", "milliner", "milliners", "stationer",
    "stationers", "engineer", "surgeon", "analyst", "draughtsman", "ironmonger",
    "ironmongers", "chemist", "chemists", "printer", "printers", "jeweller",
    "bootmaker", "shoemaker", "hairdresser", "confectioner", "tobacconist",
    "carrier", "carriers", "agent", "agents", "contractor", "contractors",
    "merchant", "merchants", "broker", "brokers", "solicitor", "solicitors",
    "architect", "accountant", "auctioneer", "surveyor", "plumber", "painter",
    "carpenter", "joiner", "labourer", "driver", "clerk", "gardener", "widow",
    "spinster", "gentleman", "esquire", "rev", "reverend", "major", "captain",
    "colonel", "miss", "mrs", "mr", "proptrs", "solictrs", "salerooms",
    "auctioneers", "auctioneer", "proprietors", "proprietor",
}


def main():
    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    surname_freq = Counter()
    trade_freq = Counter()
    addr_surnames = defaultdict(set)

    for r in rows:
        sn = (r.get("surname") or "").strip()
        tr = (r.get("trade") or "").strip()
        st = (r.get("street") or "").strip().lower()
        hn = (r.get("house_number") or "").strip().lower()
        if sn and not CORP_SURNAME_RE.match(sn) and sn.lower() != "void":
            surname_freq[sn.lower()] += 1
            if r.get("year") not in ("1914", "1917") and st and hn:
                addr_surnames[(st, hn)].add(sn.lower())
        if tr:
            trade_freq[tr.lower()] += 1

    def is_likely_surname(word, st_lower, hn_lower):
        wl = word.lower().rstrip(".,")
        if not wl or wl in SAFE_NON_SURNAME_TRADES or len(wl) < 3:
            return False
        if wl in addr_surnames.get((st_lower, hn_lower), ()):
            return True
        return surname_freq[wl] >= 5 and trade_freq[wl] <= 2

    stats = Counter()
    examples = defaultdict(list)

    for r in rows:
        yr = r.get("year", "")
        st = (r.get("street") or "").strip()
        hn = (r.get("house_number") or "").strip()
        st_l, hn_l = st.lower(), hn.lower()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()

        # 5. Global OCR trade typos spotted
        if tr:
            new_tr = re.sub(r"\bShiping\b", "Shipping", tr)
            new_tr = re.sub(r"\bIronmgs\b", "Ironmongers", new_tr)
            new_tr = re.sub(r"\bProptrs\b", "Proprietors", new_tr)
            new_tr = re.sub(r"\bSolictrs\b", "Solicitors", new_tr)
            if new_tr != tr:
                r["trade"] = new_tr
                tr = new_tr
                stats["trade_typo_fixed"] += 1

        # 1. Corporate suffix in surname (e.g. J. P. | Ltd. | Handford)
        if sn and CORP_SURNAME_RE.match(sn):
            if tr and re.match(r"^[A-Z][a-z'’-]+$", tr) and is_likely_surname(tr, st_l, hn_l):
                r["surname"] = tr
                r["forename"] = f"{fn} {sn}".strip()
                r["trade"] = ""
                stats["corp_suffix_surname_swapped"] += 1
                if len(examples["corp_suffix_surname_swapped"]) < 10:
                    examples["corp_suffix_surname_swapped"].append((yr, st, hn, fn, sn, tr))
                continue
            m_comma = re.match(r"^([A-Z][a-z'’-]{2,}),\s+(.+)$", tr)
            if m_comma and is_likely_surname(m_comma.group(1), st_l, hn_l):
                r["surname"] = m_comma.group(1)
                r["forename"] = f"{fn} {sn}".strip()
                r["trade"] = m_comma.group(2).strip()
                stats["corp_suffix_comma_swapped"] += 1
                if len(examples["corp_suffix_comma_swapped"]) < 10:
                    examples["corp_suffix_comma_swapped"].append((yr, st, hn, fn, sn, tr))
                continue
            # Fold standalone Ltd./Co. into forename so surname isn't "Ltd."
            if fn:
                r["forename"] = f"{fn}, {sn}" if not fn.endswith(",") else f"{fn} {sn}"
                r["surname"] = ""
                stats["corp_suffix_folded"] += 1
                sn = ""

        # 2. Empty surname + leaked surname in trade (1914 & 1917, or comma-prefix matching address history)
        if not sn and fn and tr and not CORP_OR_INST_WORDS.search(fn):
            if yr in ("1914", "1917") and re.match(r"^[A-Z][a-z'’-]+$", tr) and is_likely_surname(tr, st_l, hn_l):
                r["surname"] = tr
                r["trade"] = ""
                stats["empty_surname_from_trade"] += 1
                if len(examples["empty_surname_from_trade"]) < 10:
                    examples["empty_surname_from_trade"].append((yr, st, hn, fn, tr))
                continue
            m_comma = re.match(r"^([A-Z][a-z'’-]{2,}),\s+(.+)$", tr)
            if m_comma and m_comma.group(1).lower() in addr_surnames.get((st_l, hn_l), ()):
                r["surname"] = m_comma.group(1)
                r["trade"] = m_comma.group(2).strip()
                stats["comma_surname_from_trade"] += 1
                if len(examples["comma_surname_from_trade"]) < 10:
                    examples["comma_surname_from_trade"].append((yr, st, hn, fn, tr))
                continue

        # 3. "Surname Initials" packed into forename when surname is empty (1914 & 1917)
        if yr in ("1914", "1917") and not r["surname"] and fn and not CORP_OR_INST_WORDS.search(fn):
            m_pack = PERSON_PACKED_RE.match(fn)
            if m_pack:
                cand_sn, cand_fn = m_pack.group(1), m_pack.group(2)
                if cand_sn.lower() not in ("miss", "mrs", "mr", "rev", "dr", "sir", "capt", "col", "maj", "sgt"):
                    r["surname"] = cand_sn
                    r["forename"] = cand_fn
                    stats["packed_person_split"] += 1
                    if len(examples["packed_person_split"]) < 10:
                        examples["packed_person_split"].append((yr, st, hn, fn, cand_sn, cand_fn))

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print("Healing summary:", dict(stats))
    for k, ex in examples.items():
        print(f"  {k}: {ex[:5]}")


if __name__ == "__main__":
    main()
