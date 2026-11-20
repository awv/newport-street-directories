#!/usr/bin/env python3
"""Expand abbreviated/OCR trade strings in data.csv and volume_csvs/."""

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
VOL_DIR = ROOT / "volume_csvs"

REPLACEMENTS = [
    (re.compile(r"\bi['’]worker\b", re.I), "Ironworker"),
    (re.compile(r"\bi,\s*worker\b", re.I), "Ironworker"),
    (re.compile(r"\bcochbldr\b", re.I), "Coachbuilder"),
    (re.compile(r"\bcachbldr\b", re.I), "Coachbuilder"),
    (re.compile(r"\bcarp['’]tr\b", re.I), "Carpenter"),
    (re.compile(r"\bcoal\s+f['’]man\b", re.I), "Coal Foreman"),
    (re.compile(r"\bmac['’]st\b", re.I), "Machinist"),
    (re.compile(r"\btrav['’]lr\b", re.I), "Traveller"),
    (re.compile(r"\brlyman\b", re.I), "Railwayman"),
    (re.compile(r"railwy['’]?yman", re.I), "Railwayman"),
    (re.compile(r"\bbus\s+cond\.?(?=\b|\s|$)", re.I), "Bus Conductor"),
    (re.compile(r"\bplastr['’]?r?\b", re.I), "Plasterer"),
    (re.compile(r"\bice\s+crm\s+vr\.?(?=\b|\s|$)", re.I), "Ice Cream Vendor"),
    (re.compile(r"\bacet\.?\s+br(?:nr)?\.?(?=\b|\s|$)", re.I), "Acetylene Burner"),
    (re.compile(r"\bglass\s+worker\.", re.I), "Glass Worker"),
    (re.compile(r"\bblr\.?\s+cleaner\b", re.I), "Boiler Cleaner"),
    (re.compile(r"\btrss\.?(?=\b|\s|$)", re.I), "Tailoress"),
    (re.compile(r"\bcom\.?\s+agent\b", re.I), "Commercial Agent"),
    (re.compile(r"\bbrklr\.?(?=\b|\s|$)", re.I), "Bricklayer"),
    (re.compile(r"\bgas\s+wks\.?(?=\b|\s|$)", re.I), "Gas Works"),
    (re.compile(r"\btram\s+dr\.?(?=\b|\s|$)", re.I), "Tram Driver"),
    (re.compile(r"\btram\s+con\.?(?=\b|\s|$)", re.I), "Tram Conductor"),
    (re.compile(r"\bballast\s+grd\.?(?=\b|\s|$)", re.I), "Ballast Guard"),
    (re.compile(r"\bstore\s+kpr\.?(?=\b|\s|$)", re.I), "Store Keeper"),
    (re.compile(r"\bbeef\s+retailer\b", re.I), "Beer Retailer"),
    (re.compile(r"\bins['’]nce\s+agent\b", re.I), "Insurance Agent"),
    (re.compile(r"\brly\.?\s+porter\b", re.I), "Railway Porter"),
    (re.compile(r"\brlwy['’]?man\b", re.I), "Railwayman"),
    (re.compile(r"\bgard['’]?n[e']?r\b", re.I), "Gardener"),
    (re.compile(r"\bcoal\s+tipr\.?(?=\b|\s|$)", re.I), "Coal Tipper"),
    (re.compile(r"\bcontractr\.?(?=\b|\s|$)", re.I), "Contractor"),
    (re.compile(r"\bB\.?\s*&\s*M\.?\s*R\.?(?=\b|\s|$)", re.I), "Brecon & Merthyr Railway"),
    (re.compile(r"\bboot\s*rep['’]?rs\b", re.I), "Boot Repairers"),
    (re.compile(r"\bboot\s*rep['’]?r\.?(?=\b|\s|$)", re.I), "Boot Repairer"),
    (re.compile(r"\bstat['’]?nrs\b", re.I), "Stationers"),
    (re.compile(r"\bstat['’]?nr\.?(?=\b|\s|$)", re.I), "Stationer"),
    (re.compile(r"\bst['’\.]?mason\b", re.I), "Stonemason"),
    (re.compile(r"\benginedrvr\b", re.I), "Engine Driver"),
    (re.compile(r"\btelegraphst\b", re.I), "Telegraphist"),
    (re.compile(r"\bsignwtr\b", re.I), "Sign Writer"),
    (re.compile(r"\bstockbrkr\b", re.I), "Stockbroker"),
    (re.compile(r"\bhelvemkrs\b", re.I), "Helve Makers"),
    (re.compile(r"\b(?:confctnrs|confrs)\b", re.I), "Confectioners"),
    (re.compile(r"\bslatewkr\b", re.I), "Slate Worker"),
    (re.compile(r"\bcarptrs\b", re.I), "Carpenters"),
    (re.compile(r"\bbricklr\b", re.I), "Bricklayer"),
    (re.compile(r"\bshipchanlr\b", re.I), "Shipchandler"),
    (re.compile(r"\bcoachpaintr\b", re.I), "Coachpainter"),
    (re.compile(r"\bmillwrgt\b", re.I), "Millwright"),
    (re.compile(r"\bbarmn\b", re.I), "Barman"),
    (re.compile(r"\bsurvyr\b", re.I), "Surveyor"),
    (re.compile(r"\bsecy\.?(?=\b|\s|$)", re.I), "Secretary"),
    (re.compile(r"\blbr\.?(?=\b|\s|$)", re.I), "Labourer"),
    (re.compile(r"\bwidw\.?(?=\b|\s|$)", re.I), "Widow"),
    (re.compile(r"\bnewsagts\b", re.I), "Newsagents"),
    (re.compile(r"\bbrickburnr\b", re.I), "Brickburner"),
    (re.compile(r"\bupholstrs\b", re.I), "Upholsterers"),
    (re.compile(r"\bcoppersmth\b", re.I), "Coppersmith"),
    (re.compile(r"\bhorsebrkr\b", re.I), "Horsebreaker"),
    (re.compile(r"\bshipbr(?:o)?ks\b", re.I), "Shipbrokers"),
    (re.compile(r"\bbrewrs\b", re.I), "Brewers"),
    (re.compile(r"\bhattrs\b", re.I), "Hatters"),
    (re.compile(r"\bpaintrs\b", re.I), "Painters"),
    (re.compile(r"\bironmongs\b", re.I), "Ironmongers"),
    (re.compile(r"\bauctns\b", re.I), "Auctioneers"),
    (re.compile(r"\bfishmmgr\b", re.I), "Fishmonger"),
    (re.compile(r"\bwatchmkrs\b", re.I), "Watchmakers"),
    (re.compile(r"\bbookselr\b", re.I), "Bookseller"),
    (re.compile(r"\barchit\.?(?=\b|\s|$)", re.I), "Architect"),
    (re.compile(r"\bshopmanr\b", re.I), "Shopman"),
    (re.compile(r"\bbrickmakr\b", re.I), "Brickmaker"),
    (re.compile(r"\bcarpenr\b", re.I), "Carpenter"),
    (re.compile(r"\bnurseryn\b", re.I), "Nurseryman"),
    (re.compile(r"\btobacongt\b", re.I), "Tobacconist"),
]

COMMON_FORE = {
    "william", "wm.", "john", "jno.", "thomas", "thos.", "george", "geo.",
    "james", "jas.", "henry", "hy.", "charles", "chas.", "edward", "edwd.",
    "samuel", "saml.", "richard", "richd.", "robert", "robt.", "joseph", "jos.",
    "david", "daniel", "alfred", "arthur", "albert", "frederick", "fredk.",
    "walter", "ernest", "frank", "harry", "edwin", "herbert", "benjamin",
    "stephen", "evan", "morgan", "elizabeth", "mary", "ann", "sarah", "jane",
    "margaret", "ellen", "hannah", "harriet", "alice", "emma", "louisa", "eliza",
}
NON_SURNAME_WORDS = {
    "builder", "grocer", "tailor", "butcher", "baker", "painter", "plumber",
    "carpenter", "labourer", "clerk", "moulder", "shunter", "fitter", "driver",
    "mason", "joiner", "carter", "haulier", "seaman", "mariner", "pilot",
    "rigger", "trimmer", "porter", "guard", "signalman", "platelayer", "caretaker",
    "secretary", "manager", "agent", "inspector", "constable", "policeman",
    "teacher", "nurse", "widow", "spinster", "gentleman", "private", "void",
    "empty", "engineer", "mechanic", "blacksmith", "shoemaker", "bootmaker",
    "draper", "chemist", "ironmonger", "tobacconist", "confectioner", "fruiterer",
    "greengrocer", "fishmonger", "newsagent", "stationer", "printer", "saddler",
    "cooper", "wheelwright", "watchmaker", "upholsterer", "gardener", "milkman",
    "dairyman", "sawyer", "bricklayer", "plasterer", "slater", "glazier",
    "shipwright", "stevedore", "hobbler", "puddler", "striker", "roller",
    "furnaceman", "boilermaker", "ironworker", "steelworker", "machinist",
    "electrician", "fireman", "stoker", "craneman", "hoistman", "weighman",
    "checker", "timekeeper", "warehouseman", "storekeeper", "packer", "hawker",
    "cabman", "coachman", "ostler", "cellarman", "laundress", "charwoman",
    "dressmaker", "milliner", "tailoress", "hairdresser", "solicitor", "surgeon",
    "accountant", "traveller", "collector", "auctioneer", "undertaker",
    "pawnbroker", "herbalist", "farrier", "currier", "tanner", "maltster",
    "coppersmith", "millwright", "patternmaker", "shearer", "rivetter",
    "annealer", "doubler", "pickler", "scaler", "tipper", "donkeyman",
    "wharfinger", "lighterman", "boatman", "waterman", "sailmaker", "ropemaker",
    "shipbroker", "contractor", "contractr", "merchant", "dealer", "broker",
    "artist", "musician", "photographer", "journalist", "schoolmaster",
    "assistant", "foreman", "steward", "postman", "waiter", "cook",
    "shopkeeper", "victualler", "chandler", "poulterer", "outfitter", "hosier",
    "hatter", "florist", "cyclist", "barber", "brazier", "tinman", "tinsmith",
    "decorator", "weaver", "dyer", "miller", "brewer", "turner", "carver",
    "gilder", "engraver", "optician", "dentist", "veterinary", "apothecary",
    "midwife", "matron", "minister", "curate", "vicar", "rector", "priest",
    "pastor", "clergyman", "captain", "major", "colonel", "lieutenant",
    "sergeant", "corporal", "superintendent", "surveyor", "architect",
    "draughtsman", "bailiff", "registrar", "overseer", "verger", "sexton",
    "watchman", "gatekeeper", "lockkeeper", "bridgeman", "pointsman", "ganger",
    "conductor", "motorman", "chauffeur", "groom", "carman", "drayman",
    "vanman", "stableman", "herdsman", "shepherd", "farmer", "yeoman",
    "cottager", "lodger", "pensioner", "annuitant", "independent", "scholar",
    "student", "apprentice", "servant", "housekeeper", "maid", "valet",
    "butler", "footman", "page", "governess", "companion", "do", "ditto",
    "ltd", "co", "son", "sons", "bros", "brothers", "jun", "sen", "junr",
    "senr", "esq", "mrs", "miss", "mr", "rev", "dr", "sir", "bart",
    "cottage", "house", "villa", "lodge", "hall", "chambers", "buildings",
    "flats", "apartments", "shop", "stores", "office", "offices", "works",
    "yard", "wharf", "quay", "dock", "mill", "foundry", "brewery", "bakery",
    "dairy", "laundry", "hotel", "inn", "tavern", "vaults", "club", "school",
    "chapel", "church", "mission", "institute", "hospital", "infirmary",
    "dispensary", "surgery", "bank", "exchange", "customs", "police", "fire",
    "post", "telegraph", "telephone", "railway", "station", "depot", "garage",
    "stables", "garden", "gardens", "nursery", "allotments", "park", "cemetery",
    "esquire", "gent", "clergy", "reverend", "retd", "retired", "warehouse",
    "workshop", "workman", "plater", "riveter", "caulker", "smith", "wright",
    "maker", "setter", "cutter", "finisher", "dresser", "cleaner", "sweeper",
    "sorter", "loader", "unloader", "carrier", "hauler", "teetotal", "temperance",
    "billiard", "theatre", "cinema", "studio", "druggist", "bookseller",
    "opticians", "shipbrokers", "shipowners", "merchants", "trustees",
    "committee", "commissioners", "guardians", "corporation", "council",
    "board", "union", "society", "association", "company", "limited",
    "pumping", "substation", "transformer", "pavilion", "museum", "library",
    "rest", "home", "homes", "almshouses", "orphanage", "convent", "abbey",
    "rectory", "vicarage", "manse", "parsonage", "presbytery", "pottery",
    "keeper", "proprietors", "photographers", "solicitors", "shipwrights",
}

FORE_BLDG_RE = re.compile(
    r"^(?:(?:Mrs\.?|Mr\.?|Miss|Rev\.?|Dr\.?)\s+[A-Z].*|"
    r"(?:William|Wm\.?|John|Jno\.?|Thomas|Thos\.?|George|Geo\.?|Charles|Chas\.?|James|Jas\.?|Henry|Hy\.?|Edward|Edwd\.?|Richard|Richd\.?|Robert|Robt\.?|Joseph|Jos\.?|Samuel|Saml\.?|Benjamin|Benj\.?|Frederick|Fredk\.?|Alfred|Arthur|Albert|Herbert|Walter|David|Daniel|Stephen|Ernest|Frank|Harry|Edwin|Hubert|Reginald|Sidney|Harold|Percy|Stanley|Evan|Morgan|Elizabeth|Mary|Ann|Sarah|Jane|Susan|Caroline|Margaret|Ellen|Hannah|Harriet|Alice|Emma|Louisa|Eliza)(?:\s+[A-Z]\.?){0,2})$"
)
BLDG_SUFFIX_RE = re.compile(
    r"\b(?:house|cottage|cottages|villa|villas|lodge|hall|chambers|buildings|flats|apartments|terrace|place|court|yard|wharf|hotel|inn|tavern|school|chapel|church|works|mill|office|offices|shop|stores|farm|manor|abbey|rectory|vicarage|st\.?)\b",
    re.I,
)

PACKED_FIRM_RE = re.compile(
    r"(&|\band\b|\bco\.?\b|\bltd\.?\b|\bbros\.?\b|\bson\b|\bsons\b|\bcompany\b|\bsociety\b|\bassociation\b|\bbank\b|\bworks\b|\bschool\b|\bchurch\b|\bchapel\b|\bhotel\b|\binn\b|\btavern\b|\bstores\b|\bhall\b|\bclub\b|\bdepot\b|\boffice\b|\bhere is\b|\bapartments\b|\bbuilding\b|\bhouse\b|\bcottage\b|\bvilla\b)",
    re.I,
)
PACKED_NAME_RE = re.compile(
    r"^([A-Z][a-z'\-]+)\s+("
    r"(?:Mrs\.?|Mr\.?|Miss|Rev\.?|Dr\.?)\s+.*|"
    r"(?:William|Wm\.?|John|Jno\.?|Thomas|Thos\.?|George|Geo\.?|Charles|Chas\.?|James|Jas\.?|Henry|Hy\.?|Edward|Edwd\.?|Richard|Richd\.?|Robert|Robt\.?|Joseph|Jos\.?|Samuel|Saml\.?|Benjamin|Benj\.?|Frederick|Fredk\.?|Alfred|Arthur|Albert|Herbert|Walter|David|Daniel|Stephen|Ernest|Frank|Harry|Edwin|Hubert|Reginald|Sidney|Harold|Percy|Stanley|Evan|Morgan|Clement|Elizabeth|Mary|Ann|Sarah|Jane|Susan|Caroline|Margaret|Ellen|Hannah|Harriet|Alice|Emma|Louisa|Eliza|Clara|Emily|Charlotte|Catherine|Lena|Minnie|Matilda|Nancy|Amelia|Thirza|Jemima)\b.*"
    r")$"
)


HO_RE = re.compile(
    r"\b([A-Za-z'\-]+)([\s\-])ho\.?(?![A-Za-z])",
    re.I,
)
HSE_RE = re.compile(r"\bhse\.?(?![A-Za-z])", re.I)


def fix_ho(val: str, col: str) -> str:
    new_val = HO_RE.sub(
        lambda m: m.group(0) if m.group(1).lower() == "westward" else f"{m.group(1)}{m.group(2)}House",
        val,
    )
    new_val = HSE_RE.sub("House", new_val)
    if col == "trade":
        new_val = re.sub(r"(?i)^ho\s+agent\b", "House Agent", new_val)
        new_val = re.sub(r"(?i)^ho\s+furnisher\b", "House Furnisher", new_val)
        new_val = re.sub(r"(?i)\bho,\s*Alteryn\b", "House, Alteryn", new_val)
    return new_val


def fix_trade(trade: str) -> str:
    t = trade
    for pat, rep in REPLACEMENTS:
        t = pat.sub(rep, t)
    return t


EXTRA_NON_SURNAME = {
    "customs", "vacant", "unbuilt", "building", "re-building", "rebuilding",
    "closed", "schoolroom", "continued", "unfinished", "watchhouse", "glaslyn",
    "penrhiw", "englefield", "wardrobes", "books", "toys", "chaplaincy",
}


def build_known_surnames(path: Path) -> set[str]:
    counts: Counter[str] = Counter()
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            s = (r.get("surname") or "").strip()
            if re.match(r"^[A-Z][a-z'\-]+$", s):
                counts[s.lower()] += 1
    return {k for k, v in counts.items() if v >= 3} - NON_SURNAME_WORDS - EXTRA_NON_SURNAME


def looks_like_fore(other: str) -> bool:
    if PACKED_FIRM_RE.search(other):
        return False
    if re.match(r"^(?:Mrs?\.?|Miss|Rev\.?|Dr\.?|Capt\.?|Col\.?|Maj\.?)(\s+.*)?$", other, re.I):
        return True
    if re.match(r"^[A-Z]\.?(?:\s*[A-Z]\.?){0,3}$", other):
        return True
    parts = other.split()
    if len(parts) == 1 and re.match(r"^[A-Z][a-z'\-]+$", other):
        return True
    if parts and parts[0].lower().rstrip(".") in COMMON_FORE:
        return True
    return False


def process_csv(path: Path, known_surnames: set[str] | None = None) -> int:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    changed = 0
    for r in rows:
        row_changed = False
        sur = (r.get("surname") or "").strip()
        fore = (r.get("forename") or "").strip()
        tr = (r.get("trade") or "").strip()

        # Fix "senr." / "junr." in surname with "<RealSurname>, <Trade>" (or "<RealSurname>") in trade
        if sur.lower().rstrip(".") in {"senr", "junr", "jr", "sr"} and tr:
            m = re.match(r"^([A-Z][a-z'\-]+)(?:,\s*(.*))?$", tr)
            if m:
                r["surname"] = m.group(1)
                r["forename"] = f"{fore} {sur}".strip()
                r["trade"] = (m.group(2) or "").strip()
                row_changed = True
        elif tr.lower().startswith("senr. ") or tr.lower().startswith("junr. "):
            parts = tr.split(" ", 1)
            r["forename"] = f"{fore} {parts[0]}".strip()
            r["trade"] = parts[1].strip()
            row_changed = True

        # Split packed "Surname Forename" / "Surname Mrs. Forename" when forename is empty
        if not fore and sur and not PACKED_FIRM_RE.search(sur):
            m_pn = PACKED_NAME_RE.match(sur)
            if m_pn:
                r["surname"] = m_pn.group(1).strip()
                r["forename"] = m_pn.group(2).strip()
                sur = r["surname"]
                fore = r["forename"]
                row_changed = True

        # Fix forename stranded in building_name when house_number is empty
        bldg = (r.get("building_name") or "").strip()
        hn = (r.get("house_number") or "").strip()
        if not hn and bldg and FORE_BLDG_RE.match(bldg) and not BLDG_SUFFIX_RE.search(bldg):
            if not sur and fore and fore[0].isupper():
                r["surname"] = fore
                r["forename"] = bldg
                r["building_name"] = ""
                sur = r["surname"]
                fore = r["forename"]
                row_changed = True
            elif not fore and sur and sur[0].isupper():
                r["forename"] = bldg
                r["building_name"] = ""
                fore = r["forename"]
                row_changed = True

        # Fix forename-only in surname/forename with real surname stranded in trade (e.g. Bedford Rd 1898 No. 15: William | Wilson)
        if ((not sur and fore.lower() in COMMON_FORE) or (not fore and sur.lower() in COMMON_FORE)) and tr:
            if (
                re.match(r"^[A-Z][a-z'\-]+$", tr)
                and tr.lower() not in NON_SURNAME_WORDS
                and not re.search(r"(?:ers|ors|ists|wrights|smiths|makers|keepers|dealers)$", tr, re.I)
            ):
                r["forename"] = fore or sur
                r["surname"] = tr
                r["trade"] = ""
                sur = r["surname"]
                fore = r["forename"]
                tr = ""
                row_changed = True
        elif known_surnames and ((sur and not fore) or (fore and not sur)) and tr:
            if tr.lower() in known_surnames and looks_like_fore(sur or fore):
                r["forename"] = fore or sur
                r["surname"] = tr
                r["trade"] = ""
                sur = r["surname"]
                fore = r["forename"]
                tr = ""
                row_changed = True

        # Fix Albert Terrace No. 3 (Engineers' Arms), No. 19 (1910), and No. 24 (Camelly Cottage / Camley House)
        if r.get("street") == "Albert Terrace":
            hn = (r.get("house_number") or "").strip()
            yr = (r.get("year") or "").strip()
            if hn == "19" and yr == "1910" and "B. & M.R." in fore:
                r["forename"] = fore.replace("B. & M.R.", "").strip()
                r["trade"] = "Brecon & Merthyr Railway"
                row_changed = True
            if hn == "3":
                if yr in {"1895", "1904", "1908", "1910", "1933"} and "engineer" in tr.lower():
                    r["building_name"] = "Engineers' Arms"
                    r["trade"] = ""
                    row_changed = True
                elif yr == "1894" and "engineer" in fore.lower():
                    r["surname"] = "Witts"
                    r["forename"] = "F."
                    row_changed = True
                elif yr == "1913" and "witts" in tr.lower():
                    r["building_name"] = "Engineers' Arms"
                    r["surname"] = "Witts"
                    r["forename"] = "E. S."
                    r["trade"] = ""
                    row_changed = True
                elif yr == "1927" and "witts" in tr.lower():
                    r["building_name"] = "Engineers' Arms"
                    r["surname"] = "Witts"
                    r["forename"] = "Hubert H."
                    r["trade"] = ""
                    row_changed = True
                elif yr == "1936" and sur == "Miss" and "Witts" in fore:
                    r["surname"] = "Witts"
                    r["forename"] = "Miss Laura L."
                    row_changed = True
                elif yr in {"1938", "1946"} and "engineer" in sur.lower():
                    r["building_name"] = "Engineers' Arms"
                    r["surname"] = "Witts"
                    r["forename"] = "Miss Laura L."
                    r["trade"] = ""
                    row_changed = True
                elif yr == "1950" and "engineers arms" in tr.lower():
                    r["building_name"] = "Engineers' Arms"
                    r["trade"] = ""
                    row_changed = True
            elif hn == "24":
                if yr == "1913" and sur == "Reginald" and tr == "Poole":
                    r["building_name"] = "Camelly Cottage"
                    r["surname"] = "Poole"
                    r["forename"] = "Reginald"
                    r["trade"] = ""
                    row_changed = True
                elif yr == "1920" and sur == "Camelly" and "Poole" in fore:
                    r["building_name"] = "Camelly Cottage"
                    r["surname"] = "Poole"
                    r["forename"] = "Reginald"
                    row_changed = True
                elif yr == "1933" and sur == "Camley House" and "Griffiths" in fore:
                    r["building_name"] = "Camley House"
                    r["surname"] = "Griffiths"
                    r["forename"] = "BTA"
                    row_changed = True

        for col in ("building_name", "trade", "surname", "forename"):
            old_val = r.get(col) or ""
            new_val = fix_ho(old_val, col)
            if new_val != old_val:
                r[col] = new_val
                row_changed = True

        old = r.get("trade") or ""
        new = fix_trade(old)
        if new != old:
            r["trade"] = new
            row_changed = True

        if row_changed:
            changed += 1

    if changed:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    return changed


def main() -> None:
    known_surnames = build_known_surnames(DATA_CSV)
    total = process_csv(DATA_CSV, known_surnames)
    print(f"Updated {total} rows in {DATA_CSV.name}.")

    for vol_csv in sorted(VOL_DIR.glob("*_cleaned.csv")):
        vc = process_csv(vol_csv, known_surnames)
        if vc:
            print(f"Updated {vc} rows in {vol_csv.name}.")


if __name__ == "__main__":
    main()
