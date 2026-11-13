#!/usr/bin/env python3
"""
audit_names_and_swaps.py
========================
Phase 1 Diagnostic Scanner (year <= 1936):
1. Scans all abbreviated forename tokens ending in '.' -> reports/abbreviated_names_audit.tsv
2. Scans all swapped Surname <-> Forename candidates in 3 Confidence Tiers -> reports/swapped_names_audit.tsv
"""

import os
import csv
import re
from collections import Counter, defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

ABBR_OUT = os.path.join(REPORTS_DIR, "abbreviated_names_audit.tsv")
SWAP_OUT = os.path.join(REPORTS_DIR, "swapped_names_audit.tsv")
MAX_YEAR = 1936

NON_FORENAME_DOT_TOKENS = {
    "mrs.", "mr.", "miss.", "ms.", "rev.", "dr.", "capt.", "col.", "maj.", "sergt.", "sgt.",
    "prof.", "ald.", "cllr.", "hon.", "ven.", "rt.", "lt.", "gen.", "supt.", "insp.",
    "co.", "ltd.", "bros.", "st.", "junr.", "senr.", "jun.", "sen.", "jr.", "sr.", "esq.",
    "inc.", "no.", "etc.", "viz.", "g.w.r.", "l.m.s.", "j.p.", "m.d.", "b.a.", "m.a.",
    "r.n.", "r.a.", "k.c.", "c.b.", "d.s.o.", "m.c.", "v.c.", "o.b.e.", "m.b.e."
}

ABBR_FORENAME_TOKENS = {
    "wm.", "thos.", "geo.", "hy.", "chas.", "jas.", "fredk.", "jno.", "jos.", "ed.", "robt.",
    "edwd.", "saml.", "dd.", "benj.", "rd.", "alfd.", "albt.", "fred.", "richd.", "alf.",
    "herbt.", "alex.", "dl.", "danl.", "patk.", "jere.", "christr.", "nathl.", "matth.",
    "steph.", "walt.", "arth.", "ern.", "eliz.", "margt.", "cath.", "harrt.", "charl.",
    "michl.", "fras.", "abrm.", "archbld.", "ebenzr.", "regnld.", "phlp.", "edw.", "jn.",
    "jhn.", "willm.", "wilm.", "tim.", "nich.", "phil.", "lawr.", "bart.", "humph.",
    "reub.", "sol.", "zach.", "nat.", "jon.", "jonath.", "theoph.", "aug.", "bertd.",
    "cliffd.", "leon.", "perc.", "percevl.", "reg.", "sid.", "syd.", "stan.", "har.",
    "geoff.", "gilb.", "godf.", "hub.", "morg.", "osw.", "raym.", "rol.", "seym.",
    "val.", "vict.", "wilf.", "cecl.", "clar.", "cyrl.", "den.", "desm.", "don.",
    "floss.", "flor.", "flore.", "gertr.", "gert.", "glad.", "hild.", "kath.", "lil.",
    "mgt.", "mill.", "min.", "phyll.", "ros.", "sus.", "susan.", "win.", "winif."
}

# Virtually never surnames when paired with a surname in forename
UNAMBIGUOUS_FIRST_NAMES = {
    "hannah", "emma", "sarah", "elizabeth", "margaret", "ellen", "annie", "edith", "florence",
    "albert", "alfred", "ernest", "herbert", "frederick", "michael", "patrick", "samuel",
    "benjamin", "walter", "harold", "reginald", "sidney", "sydney", "edwin", "leonard",
    "clifford", "cecil", "horace", "percy", "percival", "arthur", "charles", "henry",
    "william", "richard", "edward", "robert", "joseph", "daniel", "stephen", "eliza",
    "martha", "harriet", "emily", "alice", "ethel", "gladys", "dorothy", "mabel",
    "winifred", "beatrice", "clara", "laura", "agnes", "jessie", "minnie", "lottie",
    "fanny", "rachel", "rebecca", "susannah", "mary", "jane", "ann", "catherine",
    "kathleen", "eileen", "phyllis", "marjorie", "doris", "violet", "ivy", "rose",
    "hilda", "lilian", "olive", "vera", "constance", "evelyn", "gertrude", "irene",
    "bertha", "ada", "grace", "daisy", "elsie", "maggie", "nellie", "ethel", "louisa",
    "caroline", "charlotte", "amelia", "matilda", "sophia", "helen", "lucy", "ruth",
    "esther", "miriam", "naomi", "phoebe", "priscilla", "susanna", "jemima", "dinah",
    "archibald", "alexander", "christopher", "nathaniel", "jeremiah", "jonathan",
    "timothy", "nicholas", "bartholomew", "abraham", "isaac", "jacob", "solomon",
    "ebenezer", "theophilus", "reuben", "enoch", "eli", "jethro", "moses", "aaron",
    "david", "john", "george", "thomas", "james", "francis" # Note: checked carefully below
}

# Names that are ALSO common Welsh/English surnames — kept out of Tier 2!
ALSO_SURNAMES = {
    "george", "thomas", "james", "john", "david", "francis", "lewis", "owen", "morgan",
    "martin", "howard", "lawrence", "matthew", "andrew", "simon", "paul", "mark", "peter",
    "philip", "frank", "henry", "charles", "arthur", "walter", "edward", "richard",
    "robert", "joseph", "daniel", "stephen", "samuel", "benjamin", "william", "alexander",
    "rose", "grace", "alice", "mary", "anne", "jane", "clark", "allen", "harold"
}

TIER2_SAFE_FIRST_NAMES = UNAMBIGUOUS_FIRST_NAMES - ALSO_SURNAMES

ALL_KNOWN_FIRST = UNAMBIGUOUS_FIRST_NAMES | {t.rstrip(".") for t in ABBR_FORENAME_TOKENS}

CORP_EXCLUDE_RE = re.compile(
    r"(?:&|\bltd\b|\blimited\b|\bco\.\b|\bbros\b|\bbrothers\b|\bsons?\b|\bgarage\b|\bstores\b|\bworks\b|\bsociety\b|\bclub\b|\bhotel\b|\binn\b|\bchurch\b|\bchapel\b|\bschool\b|\bbank\b|\boffice\b|\bchambers\b|\bhospital\b|\bcompany\b|\bassociation\b|\binstitute\b|\bbrewery\b|\bfoundry\b)",
    re.I
)

TITLE_START_RE = re.compile(r"^(?:mrs|mr|miss|rev|dr)\.?(?:\s|$)", re.I)
INITIAL_ONLY_RE = re.compile(r"^[A-Z]\.(?:\s*[A-Z]\.)?$")
SUFFIX_ONLY_RE = re.compile(r"^(?:junr?|senr?|jr|sr|esq)\.?$", re.I)

def main():
    print("Loading data.csv (year <= 1936)...")
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if not (r.get("year", "").strip().isdigit() and int(r.get("year", "").strip()) > MAX_YEAR)]

    print(f"Loaded {len(rows):,} records.")

    # 1. Abbreviated name tokens scan
    abbr_counts = Counter()
    for r in rows:
        for field in ("forename", "surname"):
            val = (r.get(field) or "").strip()
            for tok in val.split():
                if tok.endswith(".") and len(tok) >= 3:
                    tl = tok.lower()
                    if tl not in NON_FORENAME_DOT_TOKENS and not re.match(r"^[A-Z]\.$", tok):
                        abbr_counts[tok] += 1

    with open(ABBR_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["token", "count", "in_known_abbr_list"])
        for tok, cnt in abbr_counts.most_common():
            if cnt >= 5:
                w.writerow([tok, cnt, "YES" if tok.lower() in ABBR_FORENAME_TOKENS else "REVIEW"])

    # 2. Swapped names Tier 1 & Tier 2 scan + street/year stats
    block_total = Counter()
    block_swapped_t12 = Counter()
    candidates = []

    for idx, r in enumerate(rows):
        yr = (r.get("year") or "").strip()
        st = (r.get("street") or "").strip()
        hn = (r.get("house_number") or "").strip()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()

        if not sn or not fn:
            continue
        if CORP_EXCLUDE_RE.search(sn) or CORP_EXCLUDE_RE.search(fn):
            continue
        if SUFFIX_ONLY_RE.match(fn) or SUFFIX_ONLY_RE.match(sn):
            continue

        block_total[(yr, st)] += 1

        sn_toks = sn.split()
        sn_first_l = sn_toks[0].lower()
        fn_l = fn.lower()
        fn_first_l = fn.split()[0].lower().rstrip(".")

        tier = None
        reason = ""

        # Tier 1: Abbreviated forename, initial-only, or title in surname, while fn is a plain surname
        if (sn_first_l in ABBR_FORENAME_TOKENS or INITIAL_ONLY_RE.match(sn) or TITLE_START_RE.match(sn)):
            if not TITLE_START_RE.match(fn) and not INITIAL_ONLY_RE.match(fn) and fn_first_l not in ALL_KNOWN_FIRST and len(fn) >= 2:
                tier = "TIER1_ABBR_OR_INIT"
                reason = f"sn='{sn}' has forename abbrev/init/title"

        # Tier 2: Unambiguous first name in surname (rarely ever a surname)
        if not tier and sn_first_l in TIER2_SAFE_FIRST_NAMES:
            if not TITLE_START_RE.match(fn) and not INITIAL_ONLY_RE.match(fn) and fn_first_l not in ALL_KNOWN_FIRST and len(fn) >= 2:
                tier = "TIER2_UNAMBIGUOUS_FIRST"
                reason = f"sn='{sn}' is unambiguous given name"

        if tier:
            block_swapped_t12[(yr, st)] += 1
            candidates.append((tier, yr, st, hn, sn, fn, tr, reason))

    # Identify reversed street-year blocks for Tier 3
    reversed_blocks = set()
    for (yr, st), t12_cnt in block_swapped_t12.items():
        tot = block_total[(yr, st)]
        if t12_cnt >= 3 and (t12_cnt / max(tot, 1)) >= 0.25:
            reversed_blocks.add((yr, st))

    # Tier 3 pass: inside reversed street-year blocks, catch remaining (also-surname) first names like Henry, John, George
    seen_keys = set((c[1], c[2], c[3], c[4], c[5]) for c in candidates)
    for r in rows:
        yr = (r.get("year") or "").strip()
        st = (r.get("street") or "").strip()
        if (yr, st) not in reversed_blocks:
            continue
        hn = (r.get("house_number") or "").strip()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()
        if not sn or not fn or (yr, st, hn, sn, fn) in seen_keys:
            continue
        if CORP_EXCLUDE_RE.search(sn) or CORP_EXCLUDE_RE.search(fn) or SUFFIX_ONLY_RE.match(fn):
            continue
        sn_first_l = sn.split()[0].lower().rstrip(".")
        fn_first_l = fn.split()[0].lower().rstrip(".")
        if sn_first_l in ALL_KNOWN_FIRST and fn_first_l not in ALL_KNOWN_FIRST and not TITLE_START_RE.match(fn) and not INITIAL_ONLY_RE.match(fn):
            candidates.append(("TIER3_REVERSED_BLOCK", yr, st, hn, sn, fn, tr, f"inside reversed block ({yr} {st})"))

    with open(SWAP_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["tier", "year", "street", "house_number", "surname", "forename", "trade", "reason"])
        w.writerows(candidates)

    print(f"\nWrote {len(abbr_counts)} abbreviated tokens to {ABBR_OUT}")
    print("Top 40 shortened name tokens:")
    for tok, cnt in abbr_counts.most_common(40):
        flag = "KNOWN" if tok.lower() in ABBR_FORENAME_TOKENS else "CHECK"
        print(f"  {cnt:6d} | {tok:12s} | {flag}")

    tier_counts = Counter(c[0] for c in candidates)
    print(f"\nWrote {len(candidates):,} swapped-name candidates to {SWAP_OUT}")
    for t, cnt in tier_counts.most_common():
        print(f"  {t:25s}: {cnt:,}")
    print(f"Reversed (year, street) blocks detected: {len(reversed_blocks)}")

if __name__ == "__main__":
    main()
