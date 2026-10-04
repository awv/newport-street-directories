import csv
import json

with open("data.csv", "r", encoding="utf-8") as f:
    all_rows = [r for r in csv.DictReader(f) if r.get("street", "").strip().lower() == "albany street"]

print(f"Total Albany Street records in data.csv: {len(all_rows)}")

# Known common forenames and surnames for reversal check
COMMON_FORENAMES = {
    "william", "wm", "john", "jno", "thomas", "thos", "james", "jas", "george", "geo",
    "charles", "chas", "david", "dav", "edward", "edwd", "edw", "frederick", "fredk", "fred",
    "joseph", "jos", "henry", "hy", "richard", "richd", "robert", "robt", "alfred", "alf",
    "michael", "mrs", "miss", "elizabeth", "mary", "ann", "sarah", "florence", "emily", "gladys",
    "jane", "matilda", "grace", "harriett", "martha", "joshua", "matthew", "elisha", "nicolas",
    "samuel", "daniel", "benjamin", "benj", "herbert", "hbt", "jacob", "arthur", "owen", "stephen",
    "reginald", "reg", "hubert", "lilian", "robert", "wilfred", "jesse", "bert", "carlson", "walter"
}

COMMON_TRADES = {
    "baker", "grocer", "labourer", "lab", "labr", "haulier", "carpenter", "fitter",
    "glassblower", "glass blower", "ironworker", "iwkr", "painter", "mason", "bootmaker",
    "hairdresser", "shopkeeper", "general shop", "confectioner", "stationer", "smith",
    "puddler", "stoker", "plasterer", "sailor", "hawker", "brickmaker", "brick burner",
    "electrician", "blacksmith", "crane driver", "cleaner", "manager", "steward", "widow",
    "potter", "gas worker", "gasfitter", "laundry", "dos works", "g.w.r", "gwr"
}

suspicious_trades_in_bldg = []
suspicious_trades_in_names = []
suspicious_reversed_names = []
terrace_records = []

for idx, r in enumerate(all_rows):
    yr = r.get("year", "")
    hnum = r.get("house_number", "")
    bldg = r.get("building_name", "")
    sn = r.get("surname", "")
    fn = r.get("forename", "")
    tr = r.get("trade", "")

    # Check 1: Trade in building_name
    bldg_low = bldg.lower().strip()
    if any(t in bldg_low for t in ["labourer", "baker", "grocer", "carpenter", "haulier", "fitter", "painter", "glass blower", "ironworker", "shopkeeper", "glassblower", "tram conductor", "slater"]):
        suspicious_trades_in_bldg.append((idx, r))

    # Check 2: Trade in surname/forename
    sn_low = sn.lower().strip()
    fn_low = fn.lower().strip()
    if any(t in sn_low or t in fn_low for t in ["labourer", "baker", "grocer", "carpenter", "haulier", "fitter", "glass blower"]):
        suspicious_trades_in_names.append((idx, r))

    # Check 3: Reversed names (e.g. forename in surname and surname in forename)
    # E.g. surname="William", forename="Thomas" or surname="John", forename="Thomas"
    if sn_low in {"william", "thomas", "john", "james", "george", "charles", "edward", "joseph", "david", "henry", "richard", "robert", "alfred", "michael"} and fn_low and fn_low not in {"mrs", "miss", "mrs."}:
        # Check if forename is actually a surname (like "Parfitt", "Malpas", "Healey", "Brown", "Short", "Murphy", "Davidson", "Doyle", "Shakesheft", "Coles", "Pope", "Phillips", "Thomas", "Perry", "Welfoot", "Parker", "Carrier", "Welsh", "Morant", "Wilson", "Marley", "Way", "O'shea", "Slape", "Shellam", "Griffiths", "Clayton", "Prior", "Picton", "Brute", "Dawe", "Hillman", "Carlson", "Manley", "Lockyer"})
        if fn_low in {"parfitt", "malpas", "healey", "brown", "short", "murphy", "davidson", "doyle", "shakesheft", "coles", "pope", "phillips", "perry", "welfoot", "parker", "carrier", "welsh", "morant", "wilson", "marley", "way", "oshea", "o'shea", "slape", "shellam", "griffiths", "clayton", "prior", "picton", "brute", "dawe", "hillman", "carlson", "manley", "lockyer"}:
            suspicious_reversed_names.append((idx, r))

    # Terraces / sub-building headings
    if bldg or "cottage" in bldg_low or "terrace" in bldg_low or "place" in bldg_low:
        terrace_records.append(r)

print(f"\n1. Suspicious Trades in Building Name ({len(suspicious_trades_in_bldg)}):")
for idx, r in suspicious_trades_in_bldg:
    print(f"   [{r['year']}] No. {r['house_number']}: Bldg=\"{r['building_name']}\" | Name=\"{r['surname']} {r['forename']}\" | Trade=\"{r['trade']}\"")

print(f"\n2. Suspicious Trades in Names ({len(suspicious_trades_in_names)}):")
for idx, r in suspicious_trades_in_names:
    print(f"   [{r['year']}] No. {r['house_number']}: Name=\"{r['surname']} {r['forename']}\" | Trade=\"{r['trade']}\"")

print(f"\n3. Suspicious Reversed Names ({len(suspicious_reversed_names)}):")
for idx, r in suspicious_reversed_names:
    print(f"   [{r['year']}] No. {r['house_number']}: Name=\"{r['surname']} {r['forename']}\" | Trade=\"{r['trade']}\"")

print(f"\n4. Terrace / Building Name entries sample ({len(terrace_records)}):")
for r in terrace_records[:15]:
    print(f"   [{r['year']}] No. {r['house_number']}: Bldg=\"{r['building_name']}\" | Name=\"{r['surname']} {r['forename']}\"")
