#!/usr/bin/env python3
"""Find trade values in data.csv that don't match common trades (e.g. surnames)."""

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data.csv"
OUT_CSV = ROOT / "reports" / "non_trade_candidates.csv"

TRADE_SUFFIX_RE = re.compile(
    r"(?:er|ers|or|ors|ist|ists|man|men|woman|women|maker|makers|keeper|keepers|"
    r"dealer|dealers|smith|smiths|wright|wrights|master|masters|mistress|"
    r"works|work|shop|shops|store|stores|house|hotel|inn|tavern|vaults|"
    r"office|offices|agent|agents|broker|brokers|merchant|merchants|"
    r"builder|builders|engineer|engineers|clerk|clerks|driver|drivers|"
    r"labourer|laborer|miner|collier|mason|joiner|carpenter|painter|plumber|"
    r"tailor|butcher|baker|grocer|draper|chemist|printer|porter|guard|"
    r"signalman|platelayer|fitter|moulder|turner|cutter|packer|carter|"
    r"haulier|mariner|seaman|pilot|rigger|trimmer|stevedore|hobbler|"
    r"fruiterer|greengrocer|fishmonger|ironmonger|tobacconist|confectioner|"
    r"stationer|newsagent|hairdresser|barber|bootmaker|shoemaker|watchmaker|"
    r"jeweller|upholsterer|cabinetmaker|undertaker|auctioneer|surveyor|"
    r"architect|solicitor|accountant|surgeon|physician|dentist|optician|"
    r"veterinary|minister|curate|vicar|rector|priest|pastor|clergyman|"
    r"teacher|school|college|church|chapel|mission|institute|hospital|"
    r"club|bank|society|association|company|limited|ltd|corp|council|"
    r"railway|dock|wharf|quay|yard|mill|foundry|brewery|bakery|dairy|laundry|"
    r"garage|depot|warehouse|studio|theatre|cinema|pharmacy|dispensary|"
    r"surgery|restaurant|cafe|dining|refreshment|lodging|boarding|apartments|"
    r"void|empty|private|retired|retd|widow|spinster|gentleman|esq)$",
    re.I,
)

# Common short/non-suffix trade words
EXTRA_TRADE_WORDS = {
    "army", "navy", "police", "constable", "sergeant", "inspector", "captain",
    "major", "colonel", "lieutenant", "superintendent", "matron", "nurse",
    "midwife", "steward", "butler", "valet", "footman", "cook", "maid",
    "servant", "governess", "companion", "waiter", "waitress", "ostler",
    "groom", "coachman", "cabman", "chauffeur", "motorman", "conductor",
    "fireman", "stoker", "craneman", "hoistman", "weighman", "checker",
    "foreman", "overseer", "manager", "secretary", "treasurer", "collector",
    "registrar", "bailiff", "verger", "sexton", "postmaster", "postman",
    "telegraphist", "typist", "machinist", "electrician", "mechanic",
    "blacksmith", "whitesmith", "coppersmith", "tinsmith", "goldsmith",
    "silversmith", "locksmith", "gunsmith", "millwright", "wheelwright",
    "shipwright", "cartwright", "coachbuilder", "shipbroker", "shipowner",
    "coal", "timber", "iron", "steel", "tin", "copper", "brass", "lead",
    "glass", "china", "boot", "shoe", "hat", "glove", "hosier", "outfitter",
    "clothier", "furrier", "saddler", "harness", "cooper", "basket",
    "brush", "rope", "sail", "tent", "tarpaulin", "oil", "grease", "paint",
    "paper", "book", "music", "piano", "cycle", "motor", "car", "van",
    "cab", "taxi", "bus", "tram", "milk", "cream", "butter", "cheese",
    "egg", "poultry", "fish", "meat", "pork", "tripe", "bread", "cake",
    "pastry", "sweet", "fruit", "potato", "tea", "coffee", "beer", "wine",
    "spirit", "ale", "stout", "cider", "tobacco", "cigar", "snuff",
    "florist", "nursery", "seed", "corn", "flour", "hay", "straw", "malt",
    "hop", "salt", "soap", "candle", "rag", "bone", "marine", "scrap",
    "general", "fancy", "hardware", "earthenware", "furniture", "carpet",
    "bedding", "curtain", "linen", "woollen", "silk", "cotton", "lace",
    "umbrella", "trunk", "bag", "leather", "currier", "tanner", "fellmonger",
    "dyer", "bleacher", "weaver", "spinner", "carder", "knitter", "finisher",
    "carver", "gilder", "engraver", "lithographer", "bookbinder", "photographer",
    "artist", "sculptor", "musician", "organist", "pianist", "vocalist",
    "actor", "comedian", "journalist", "reporter", "author", "publisher",
    "editor", "bookseller", "librarian", "tutor", "lecturer", "professor",
    "scholar", "student", "apprentice", "pupil", "fellow", "justice",
    "magistrate", "alderman", "councillor", "mayor", "sheriff", "coroner",
    "consul", "notary", "barrister", "advocate", "commissioner", "trustee",
    "guardian", "warden", "ranger", "keeper", "caretaker", "janitor",
    "hallkeeper", "gatekeeper", "lockkeeper", "timekeeper", "storekeeper",
    "shopkeeper", "innkeeper", "hotelkeeper", "housekeeper", "landlord",
    "landlady", "proprietor", "proprietress", "lessee", "tenant", "occupier",
    "resident", "lodger", "pensioner", "annuitant", "independent", "gentry",
    "yeoman", "farmer", "grazier", "dairyman", "milkman", "cowkeeper",
    "shepherd", "herdsman", "ploughman", "thatcher", "hedger", "ditcher",
    "woodman", "forester", "sawyer", "feller", "quarryman", "brickmaker",
    "tilemaker", "potter", "glazier", "slater", "tiler", "plasterer",
    "roughcaster", "pavior", "paviour", "scavenger", "chimney", "sweep",
    "sweeper", "cleaner", "washer", "laundress", "charwoman", "ironer",
    "mangler", "dressmaker", "milliner", "seamstress", "needlewoman",
    "tailoress", "corset", "stay", "mantle", "costumier", "modiste",
    "drapery", "millinery", "hosiery", "haberdashery", "grocery", "provisions",
    "butchery", "bakery", "confectionery", "stationery", "ironmongery",
    "chandlery", "druggist", "apothecary", "herbalist", "chiropodist",
    "masseur", "masseuse", "osteopath", "optometry", "oculist", "aurist",
    "surgeon", "doctor", "medical", "surgical", "dental", "clinical",
    "nursing", "maternity", "convalescent", "asylum", "sanatorium",
    "chartered", "certified", "incorporated", "registered", "licensed",
    "victualler", "publican", "brewer", "maltster", "distiller", "rectifier",
    "bottler", "cellarman", "barman", "barmaid", "potman", "tapster",
    "billiard", "skittle", "bowling", "athletic", "cricket", "football",
    "golf", "tennis", "rowing", "yacht", "boating", "ferry", "tug",
    "barge", "lighter", "lighterman", "waterman", "boatman", "ferryman",
    "coxswain", "skipper", "mate", "boatswain", "bosun", "stewardess",
    "purser", "shipchandler", "shipwright", "caulker", "boiler", "boilermaker",
    "riveter", "rivetter", "plater", "holder", "strikers", "striker",
    "hammerman", "forge", "forgeman", "puddler", "shingler", "roller",
    "catcher", "hooker", "heater", "furnaceman", "smelter", "refiner",
    "annealer", "pickler", "galvanizer", "tinman", "brazier", "founder",
    "patternmaker", "coremaker", "fettler", "chipper", "grinder", "polisher",
    "buffer", "plater", "enameller", "japanner", "lacquerer", "varnisher",
    "french", "sign", "writer", "gilder", "paperhanger", "decorator",
    "glazer", "wire", "drawer", "nail", "bolt", "nut", "screw", "rivet",
    "chain", "anchor", "cable", "spring", "axle", "wheel", "tyre", "tire",
    "coach", "wagon", "waggon", "carriage", "cart", "van", "barrow",
    "perambulator", "cycle", "bicycle", "tricycle", "motorcycle", "aeroplane",
    "wireless", "radio", "electrical", "gas", "water", "hydraulic",
    "sanitary", "heating", "ventilating", "refrigerating", "cold", "ice",
    "timber", "saw", "planing", "joinery", "turnery", "cabinet", "chair",
    "bedstead", "mattress", "upholstery", "picture", "frame", "mirror",
    "clock", "watch", "jewellery", "jewelry", "diamond", "gold", "silver",
    "plate", "cutlery", "tool", "scale", "weight", "measure", "instrument",
    "optical", "scientific", "nautical", "musical", "gramophone", "sewing",
    "typewriter", "cash", "register", "safe", "lock", "bell", "lamp",
    "lantern", "stove", "grate", "range", "fender", "brassfoundry",
    "agricultural", "horticultural", "implement", "machine", "machinery",
    "engine", "locomotive", "traction", "steam", "oil", "petrol", "diesel",
    "coal", "coke", "charcoal", "patent", "fuel", "briquette", "lime",
    "cement", "plaster", "mortar", "concrete", "asphalt", "tar", "pitch",
    "brick", "tile", "slate", "stone", "granite", "marble", "sand",
    "gravel", "clay", "terra", "cotta", "pottery", "pipe", "drain",
    "sewer", "road", "paving", "flag", "kerb", "curb", "fence", "gate",
    "rail", "ironwork", "steelwork", "bridge", "girder", "tank", "boiler",
    "crane", "lift", "hoist", "pump", "valve", "pipe", "tube", "wire",
    "rope", "net", "twine", "canvas", "sailcloth", "sacking", "bagging",
    "jute", "hemp", "flax", "wool", "yarn", "thread", "cloth", "tweed",
    "serge", "flannel", "blanket", "rug", "carpet", "mat", "linoleum",
    "oilcloth", "wallpaper", "paint", "colour", "color", "varnish", "stain",
    "polish", "glue", "size", "putty", "whiting", "chalk", "ochre",
    "chemical", "acid", "alkali", "soda", "potash", "ammonia", "tar",
    "creosote", "naphtha", "benzole", "paraffin", "kerosene", "petroleum",
    "lubricating", "tallows", "tallow", "candle", "wax", "match", "starch",
    "blue", "blacking", "ink", "gum", "paste", "glue", "gelatine",
    "manure", "fertilizer", "guano", "bone", "seed", "grain", "corn",
    "meal", "bran", "pollard", "offal", "cake", "fodder", "forage",
    "provender", "chaff", "hay", "straw", "clover", "moss", "litter",
    "peat", "turf", "loam", "soil", "manure", "compost",
    "do", "ditto", "etc", "and", "of", "the", "for", "in", "to", "at", "on", "by", "with", "co",
    "gwr", "great", "western", "monmouthshire", "newport", "cardiff", "bristol",
    "brecon", "merthyr", "alexandra", "tredegar", "uskmouth", "caerleon",
}


def tokenize(s: str) -> list[str]:
    return re.findall(r"[A-Za-z]+", s.lower())


def is_known_trade_text(trade: str, common_trade_words: set[str]) -> bool:
    tokens = tokenize(trade)
    if not tokens:
        return True
    for tok in tokens:
        if tok in EXTRA_TRADE_WORDS or tok in common_trade_words or TRADE_SUFFIX_RE.search(tok):
            return True
    return False


def main() -> None:
    with open(DATA_CSV, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    # Build known surnames (appear >= 3 times as surname) and common trade words
    surname_counts = Counter()
    trade_counts = Counter()
    for r in rows:
        sur = (r.get("surname") or "").strip()
        if re.match(r"^[A-Z][a-z'\-]+$", sur):
            surname_counts[sur.lower()] += 1
        tr = (r.get("trade") or "").strip()
        if tr:
            trade_counts[tr.lower()] += 1

    known_surnames = {k for k, v in surname_counts.items() if v >= 3} - EXTRA_TRADE_WORDS

    # Words from trades appearing >= 10 times
    common_trade_words: set[str] = set()
    for tr_low, cnt in trade_counts.items():
        if cnt >= 10:
            for tok in tokenize(tr_low):
                if len(tok) >= 3 and tok not in known_surnames:
                    common_trade_words.add(tok)

    candidates = []
    reason_counts = Counter()

    for idx, r in enumerate(rows, start=2):
        tr = (r.get("trade") or "").strip()
        if not tr:
            continue
        sur = (r.get("surname") or "").strip()
        fore = (r.get("forename") or "").strip()
        bldg = (r.get("building_name") or "").strip()

        # Skip obvious house/building names still in trade (House, Villa, Cottage, etc.)
        if re.search(r"\b(?:house|villa|cottage|lodge|hall|terrace|place|court|road|street)\b", tr, re.I):
            continue

        reason = None
        # 1. Single capitalized word in trade that is a known surname (and not a known trade word)
        if re.match(r"^[A-Z][a-z'\-]+$", tr):
            low = tr.lower()
            if not (low in EXTRA_TRADE_WORDS or TRADE_SUFFIX_RE.search(low) or low in common_trade_words):
                if low in known_surnames and (not sur or not fore):
                    reason = "known_surname_missing_name_part"
                elif low in known_surnames:
                    reason = "known_surname_single_word"
                elif not sur or not fore:
                    reason = "capitalized_word_missing_name_part"
                else:
                    reason = "unknown_single_word"
        # 2. Multi-word trade with no known trade words at all
        elif not is_known_trade_text(tr, common_trade_words):
            reason = "no_known_trade_words"

        if reason:
            reason_counts[reason] += 1
            candidates.append({
                "csv_line": idx,
                "reason": reason,
                "year": r.get("year", ""),
                "street": r.get("street", ""),
                "house_number": r.get("house_number", ""),
                "building_name": bldg,
                "surname": sur,
                "forename": fore,
                "trade": tr,
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["csv_line", "reason", "year", "street", "house_number", "building_name", "surname", "forename", "trade"],
        )
        w.writeheader()
        w.writerows(candidates)

    print(f"Total candidates written to {OUT_CSV.relative_to(ROOT)}: {len(candidates)}")
    for reason, cnt in reason_counts.most_common():
        print(f"  {reason}: {cnt}")

    # Show top examples per reason
    by_reason = defaultdict(list)
    for c in candidates:
        by_reason[c["reason"]].append(c)

    for reason in [
        "known_surname_missing_name_part",
        "capitalized_word_missing_name_part",
        "known_surname_single_word",
        "unknown_single_word",
        "no_known_trade_words",
    ]:
        items = by_reason[reason]
        if not items:
            continue
        print(f"\n--- {reason} (top 20 of {len(items)}) ---")
        for c in items[:20]:
            print(f"  {c['year']} {c['street']} {c['house_number']} | {c['surname']!r} {c['forename']!r} | trade={c['trade']!r}")


if __name__ == "__main__":
    main()
