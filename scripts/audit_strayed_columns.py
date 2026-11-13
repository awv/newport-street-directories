#!/usr/bin/env python3
"""
audit_strayed_columns.py
========================
Non-destructive diagnostic scanner to identify strayed columns across data.csv (year <= 1936):
1. HOUSE_IN_TRADE: Villa/house names trapped in the `trade` column.
2. COMPOUND_TRADE_AND_HOUSE: `trade` containing both a trade and a house name (e.g., "sign writer, Lorna Doone").
3. TRADE_IN_SURNAME: Clear multi-word or strictly occupational trades placed in `surname`.
4. BUSINESS_SPLIT: Business/company names split awkwardly across `surname`, `forename`, `building_name`, and `trade`.
5. TRADE_IN_BUILDING: Pure occupations (e.g., "Labourer", "Ironworker", "Clerk") trapped in `building_name`.

Outputs:
  - reports/strayed_columns_audit.tsv
  - Prints a summary by category, street, and top recurring patterns.
"""

import os
import csv
import re
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_CSV = os.path.join(PROJECT_ROOT, "data.csv")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
OUT_TSV = os.path.join(REPORTS_DIR, "strayed_columns_audit.tsv")

MAX_YEAR = 1936

# Suffixes/prefixes strongly indicative of house/villa names (not trades)
HOUSE_MORPHOLOGY_RE = re.compile(
    r"^(?:"
    r"(?:bryn|plas|ty|glan|nant|cwm|pant|pen|llan|maes|coed|bron|caer|tre)[\s\-][a-z]+|"
    r"(?:the\s+)?(?:laurels|firs|elms|oaks|pines|cedars|beeches|sycamores|poplars|willows|chestnuts|holly|ivy|fern|rose|hazel|ash|elm|oak|holme|hurst|croft|vale|view|dene|mount|grove|mead|brook|burn|glen|leigh|com[bp]e|wick|stead|cott|cot|villa|villas|cottage|cottages|lodge|house|ho|hall|court|manor|grange|rectory|vicarage|parsonage|priory|abbey|tower|castle|hollybush|sunnyside|fairfield|westfield|oaklands|woodlands|highfield|springfield|brooklands|greenbank|rocklands|cliffside|seaview|bayview|hillside|woodside|parkside|riverside|waterside)|"
    r"[a-z]+(?:dene|hurst|croft|holme|leigh|vale|view|grove|mead|mount|brook|glen|lands|side|wick|combe|thorpe|cliff)\.?|"
    r"[a-z\s\.\']+\s+(?:ho|house|villa|villas|cottage|cottages|lodge|hall|court|manor|grange|vale|view|mount|grove|dene)\.?$"
    r")$",
    re.I
)

# Broad occupational/non-house exclusions
OCCUPATION_WORD_RE = re.compile(
    r"(?:"
    r"\b(?:labourer|ironworker|steelworker|fireman|bricklayer|blacksmith|postman|assistant|steward|roller|timekeeper|"
    r"electrician|packer|weighman|quarryman|stonemason|ganger|sculptor|brewer|schoolmaster|schoolmistress|"
    r"stationmaster|postmaster|harbourmaster|g\.w\.r\.|gwr|l\.m\.s\.|shop|general\s+shop|stores|cab\s+proprietor|"
    r"clerk|agent|manager|foreman|inspector|superintendent|collector|traveller|salesman|cashier|bookkeeper|"
    r"mason|fitter|turner|machinist|engineer|carpenter|joiner|builder|contractor|plumber|painter|glazier|"
    r"decorator|plasterer|slater|tiler|pavior|farrier|smith|boilermaker|shipwright|wheelwright|coachbuilder|"
    r"patternmaker|moulder|founder|riveter|caulker|cutler|watchmaker|jeweller|optician|chemist|druggist|"
    r"dentist|surgeon|physician|doctor|nurse|midwife|solicitor|accountant|auditor|architect|surveyor|"
    r"auctioneer|valuer|broker|grocer|greengrocer|fruiterer|florist|gardener|nurseryman|baker|confectioner|"
    r"butcher|poulterer|fishmonger|dairyman|milkman|cheesemonger|chandler|ironmonger|draper|tailor|hosier|"
    r"hatter|milliner|dressmaker|outfitter|shoemaker|bootmaker|cordwainer|cobbler|saddler|hairdresser|barber|"
    r"tobacconist|stationer|bookseller|newsagent|printer|photographer|artist|musician|teacher|tutor|professor|"
    r"minister|clergyman|priest|curate|rector|vicar|pastor|sexton|verger|organist|publican|victualler|"
    r"innkeeper|waiter|porter|carrier|carter|haulier|drayman|cabman|coachman|groom|ostler|driver|conductor|"
    r"guard|signalman|pointsman|platelayer|seaman|mariner|sailor|pilot|waterman|boatman|lighterman|stevedore|"
    r"hobbler|rigger|trimmer|shipper|tipper|police|constable|sergeant|soldier|pensioner|widow|spinster|"
    r"gentleman|retired|private|void|vacant|empty|unoccupied|apartments|lodgings|boarding|warehouse|wharf|"
    r"depot|yard|office|offices|works|factory|mill|mills|foundry|brewery|bakery|dairy|laundry|garage|"
    r"charwoman|housekeeper|laundress|cook|servant|domestic|machinist|stoker|shunter|brakesman|checker|"
    r"craneman|enginedriver|engineman|miner|collier|puddler|smelter|annealer|galvanizer|tinplate|sawyer|"
    r"cooper|basketmaker|brushmaker|ropemaker|sailmaker|upholsterer|cabinetmaker|undertaker|pawnbroker|"
    r"dealer|merchant|shopkeeper|storekeeper|hawker|pedlar|costermonger|rag|marine|licensed|beerhouse|"
    r"refreshment|dining|coffee|cocoa|tavern|hotel|inn|arms|vaults|club|institute|school|college|hospital|"
    r"church|chapel|mission|theatre|cinema|bank|insurance|assurance|society|company|ltd|limited|& co|sons?)\b|"
    r"(?:maker|worker|driver|keeper|seller|dealer|merchant|wright|smith|master|mistress|man|men|woman|women|er|or|ist|ian)$"
    r")",
    re.I
)

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
    r"plasterer|plumber|glazier|decorator|bricklayer|slater|stonemason|"
    r"schoolmaster|schoolmistress|stationmaster|harbourmaster|postmaster|"
    r"publican|innkeeper|victualler|pawn\s*broker|pawnbroker"
    r")$",
    re.I
)

BUSINESS_RE = re.compile(
    r"\b(?:ltd\.?|limited|&\s*co\.?|&\s*sons?|bros\.?|brothers|company|printing\s+co|stores|works|foundry|brewery|building\s+soc|society|syndicate|association|garage|motors|ironfounders|contractors|merchants|furnishers|chambers)\b",
    re.I
)

def is_occupation(s):
    if not s:
        return False
    # Check each word/phrase against occupation patterns
    if OCCUPATION_WORD_RE.search(s):
        return True
    return False

def main():
    print("Loading data.csv and building clean reference sets...")
    with open(DATA_CSV, "r", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if not (r.get("year", "").strip().isdigit() and int(r.get("year", "").strip()) > MAX_YEAR)]

    print(f"Loaded {len(rows):,} records (year <= {MAX_YEAR}).")

    # Count trade frequencies to distinguish real common trades from rare trapped house names
    trade_freq = Counter((r.get("trade") or "").strip().lower() for r in rows if (r.get("trade") or "").strip())

    # Build clean known building_names (must not look like occupations or appear heavily in trade)
    known_buildings = set()
    for r in rows:
        bn = (r.get("building_name") or "").strip()
        if bn and len(bn) >= 4:
            bn_l = bn.lower()
            if not is_occupation(bn) and trade_freq.get(bn_l, 0) < 15:
                known_buildings.add(bn_l)

    print(f"Collected {len(known_buildings):,} clean non-trade building names.")

    findings = []
    cat_counts = Counter()
    street_counts = Counter()
    house_in_trade_counts = Counter()
    trade_in_bldg_counts = Counter()

    for r in rows:
        yr = (r.get("year") or "").strip()
        st = (r.get("street") or "").strip()
        hn = (r.get("house_number") or "").strip()
        bn = (r.get("building_name") or "").strip()
        sn = (r.get("surname") or "").strip()
        fn = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()

        # 1. COMPOUND_TRADE_AND_HOUSE: e.g., "sign writer, Lorna Doone"
        if "," in tr and sn:
            parts = [p.strip() for p in tr.split(",", 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                p0, p1 = parts[0], parts[1]
                p1_is_house = (p1.lower() in known_buildings or (HOUSE_MORPHOLOGY_RE.match(p1) and not is_occupation(p1)))
                p0_is_trade = is_occupation(p0)
                if p1_is_house and p0_is_trade:
                    findings.append(("COMPOUND_TRADE_AND_HOUSE", yr, st, hn, bn, sn, fn, tr, f"trade='{p0}', bldg='{p1}'"))
                    cat_counts["COMPOUND_TRADE_AND_HOUSE"] += 1
                    street_counts[st] += 1
                    house_in_trade_counts[p1] += 1
                    continue

        # 2. HOUSE_IN_TRADE: trade looks like a house/villa name while surname exists
        if tr and sn and not is_occupation(tr):
            tr_lower = tr.lower().rstrip(".")
            is_known_bldg = tr_lower in known_buildings
            is_house_morph = bool(HOUSE_MORPHOLOGY_RE.match(tr))
            if is_known_bldg or is_house_morph:
                if len(tr) >= 4 and not re.match(r"^[A-Z]\.?\s*[A-Z]?\.?$", tr):
                    reason = "known_building" if is_known_bldg else "house_morphology"
                    findings.append(("HOUSE_IN_TRADE", yr, st, hn, bn, sn, fn, tr, reason))
                    cat_counts["HOUSE_IN_TRADE"] += 1
                    street_counts[st] += 1
                    house_in_trade_counts[tr] += 1
                    continue

        # 3. TRADE_IN_BUILDING: pure occupation trapped in building_name
        if bn and is_occupation(bn) and not HOUSE_MORPHOLOGY_RE.match(bn) and not re.search(r"\b(house|ho|villa|villas|cottage|lodge|hall|court|manor|inn|hotel|arms|tavern|works|foundry|brewery|chambers|buildings|school|chapel|church)\b", bn, re.I):
            if trade_freq.get(bn.lower(), 0) >= 5:
                findings.append(("TRADE_IN_BUILDING", yr, st, hn, bn, sn, fn, tr, f"bn='{bn}' is a common trade"))
                cat_counts["TRADE_IN_BUILDING"] += 1
                street_counts[st] += 1
                trade_in_bldg_counts[bn] += 1
                continue

        # 4. TRADE_IN_SURNAME: surname is strictly an occupational trade
        if sn and STRICT_TRADE_IN_SURNAME_RE.match(sn):
            findings.append(("TRADE_IN_SURNAME", yr, st, hn, bn, sn, fn, tr, f"sn='{sn}' looks like trade"))
            cat_counts["TRADE_IN_SURNAME"] += 1
            street_counts[st] += 1
            continue

        # 5. BUSINESS_SPLIT: business entity split across forename/building/trade awkwardly
        if BUSINESS_RE.search(fn) or (BUSINESS_RE.search(sn) and fn and not re.match(r"^(?:&|and|mrs|mr|miss|jr|jun|sen)\b", fn, re.I)):
            if not (BUSINESS_RE.search(sn) and not fn):
                findings.append(("BUSINESS_SPLIT", yr, st, hn, bn, sn, fn, tr, "corporate keyword in fn or split sn/fn"))
                cat_counts["BUSINESS_SPLIT"] += 1
                street_counts[st] += 1

    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["category", "year", "street", "house_number", "building_name", "surname", "forename", "trade", "notes"])
        writer.writerows(findings)

    print(f"\nWrote {len(findings):,} candidate findings to {OUT_TSV}")
    print("\n=== Findings by Category ===")
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat:28s}: {cnt:,}")

    print("\n=== Top 20 Affected Streets ===")
    for st, cnt in street_counts.most_common(20):
        print(f"  {st:35s}: {cnt:,}")

    print("\n=== Top 25 Recurring House Names in Trade ===")
    for th, cnt in house_in_trade_counts.most_common(25):
        print(f"  {th:35s}: {cnt:,}")

    print("\n=== Top 15 Trades Trapped in Building Name ===")
    for tb, cnt in trade_in_bldg_counts.most_common(15):
        print(f"  {tb:35s}: {cnt:,}")

if __name__ == "__main__":
    main()
