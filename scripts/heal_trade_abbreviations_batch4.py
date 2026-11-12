#!/usr/bin/env python3
"""
scripts/heal_trade_abbreviations_batch4.py

Expands trade abbreviations (Batch 4) while preserving authenticity:
1. Al Tipper / C'al Tipper -> Coal Tipper
2. Pilot's Asst -> Pilot's Assistant
3. Cargo Wrkr -> Cargo Worker
4. Ppersmiths And Plumbers -> Coppersmiths & Plumbers
5. Eng'rs & Body Builders -> Engineers & Body Builders
6. Engmn -> Engineman
7. Timek'pr -> Timekeeper (and Timekepr)
8. Ckman -> Dockman
9. Ck Police -> Dock Police
10. Al Mercht. / Coal Mercht -> Coal Merchant (and Coal Merch'Nt, Coal Merch'T)
11. Engi-neers And Ironfounders -> Engineers & Ironfounders
12 & 13. Traffic M'gr / Mgr / Managr -> Traffic Manager
14. Draughtsmn / Draughtsm'N -> Draughtsman
15. H.m.c. -> H.M.C.
16. Rope & Twine Wks -> Rope & Twine Works (and Rope & Twine St -> Rope & Twine Stores)
17. Timber And Slate Merchts -> Timber & Slate Merchants (and Slate Merchnt)
18. Engnr -> Engineer (and Motor Engnr, Sanitary Engnr, etc.)
19. Hairdresr / Hairdressr -> Hairdresser
20. Lliery Prptr -> Colliery Proprietor
21. Al Exporters And Patent Fuel Merchants -> Coal Exporters & Patent Fuel Merchants
22. J.p. Solicitor -> Justice of the Peace & Solicitor
23. Rn Merchants / rn Merchant -> Corn Merchants / Corn Merchant
24. Annealr -> Annealer
25. Signalfttr / Signal Fitr / Signal Fittr -> Signal Fitter
26. Nf'tr / Conf'Tr / Conf'Trs -> Confectioner / Confectioners
27. Hammermn -> Hammerman
28. Wag'nmkr / Wagonmkr -> Wagonmaker
+ Disentangling trapped names and column misalignments discovered in these entries.
"""

import csv
import re
import shutil
from pathlib import Path
from collections import Counter

DATA_CSV = Path("data.csv")
BACKUP_CSV = Path("data.csv.bak_before_trades_batch4")

def clean_trade(trade: str) -> str:
    if not trade:
        return trade
    s = trade.strip()

    # 1. Al Tipper / C'al Tipper -> Coal Tipper
    s = re.sub(r'\b(?:c[\'’]?al|al)\s+tipper\b', 'Coal Tipper', s, flags=re.I)

    # 2. Pilot's Asst -> Pilot's Assistant
    s = re.sub(r'\bPilots?\'?\s+Asst\.?\b', 'Pilot\'s Assistant', s, flags=re.I)

    # 3. Cargo Wrkr -> Cargo Worker
    s = re.sub(r'\bCargo\s+Wrkr\b', 'Cargo Worker', s, flags=re.I)

    # 4. Ppersmiths -> Coppersmiths
    s = re.sub(r'\bPpersmiths\s+And\s+Plumbers\b', 'Coppersmiths & Plumbers', s, flags=re.I)
    s = re.sub(r'\bCoppersmiths\s+And\s+Plumbers\b', 'Coppersmiths & Plumbers', s, flags=re.I)

    # 5. Eng'rs & Body Builders -> Engineers & Body Builders
    s = re.sub(r'\b(?:Motor\s+)?(?:Void\s+)?Eng\'?rs\s+&\s+Body\s+Builders\b', 'Engineers & Body Builders', s, flags=re.I)

    # 6. Engmn -> Engineman
    s = re.sub(r'\bEngmn\b', 'Engineman', s, flags=re.I)

    # 7. Timek'pr -> Timekeeper
    s = re.sub(r'\bTimek[\'’]?pr\b', 'Timekeeper', s, flags=re.I)
    s = re.sub(r'\bTimekepr\b', 'Timekeeper', s, flags=re.I)

    # 8 & 9. Ckman -> Dockman, Ck Police -> Dock Police
    s = re.sub(r'\bCkman\b', 'Dockman', s, flags=re.I)
    s = re.sub(r'\bCk\s+Police\b', 'Dock Police', s, flags=re.I)

    # 10. Al Mercht. / Coal Mercht -> Coal Merchant
    s = re.sub(r'\b(?:c[\'’]?al|al|coal)\s*merch(?:t|[\'’]nt|[\'’]t)?\.?\b\.?', 'Coal Merchant', s, flags=re.I)

    # 11. Engi-neers -> Engineers
    s = re.sub(r'\bEngi-Neers\s+And\s+Ironfounders\b', 'Engineers & Ironfounders', s, flags=re.I)
    s = re.sub(r'\bEngi-Neers\s+And\s+Ship-?Smiths\b', 'Engineers & Ship Smiths', s, flags=re.I)
    s = re.sub(r'\bBridge\s+And\s+Roof\s+Engi-Neers\.?\b', 'Bridge & Roof Engineers', s, flags=re.I)

    # 12 & 13. Traffic Manager
    s = re.sub(r'\bTraffic\s+M(?:an|a|m|n)?\'?(?:a|g)?(?:g)?rs?\b', 'Traffic Manager', s, flags=re.I)

    # 14. Draughtsman
    s = re.sub(r'\bDraughtsm[\'’]?n\b', 'Draughtsman', s, flags=re.I)
    s = re.sub(r'\bDraughtsm\b', 'Draughtsman', s, flags=re.I)

    # 15. H.m.c. -> H.M.C.
    s = re.sub(r'\bH\.m\.c\.?\b', 'H.M.C.', s)
    s = re.sub(r'\bh\.m\.c\.?\b', 'H.M.C.', s)

    # 16. Rope & Twine Works / Stores
    s = re.sub(r'\bRope\s+&\s+Twine\s+Wks\b', 'Rope & Twine Works', s, flags=re.I)
    s = re.sub(r'\bRope\s+&\s+Twinestrs\b', 'Rope & Twine Stores', s, flags=re.I)
    s = re.sub(r'\bRope\s+&\s+Twine\s+Str?s?\b', 'Rope & Twine Stores', s, flags=re.I)

    # 17. Timber And Slate Merchants
    s = re.sub(r'\bTimber\s+(?:And|&)\s+Slate\s+Merch\'?nts?\b', 'Timber & Slate Merchants', s, flags=re.I)
    s = re.sub(r'\bSlate\s+Merchnt\b', 'Slate Merchant', s, flags=re.I)

    # 18. Engnr -> Engineer
    s = re.sub(r'\bMotor\s+Engnrs?\b', lambda m: 'Motor Engineers' if m.group(0).lower().endswith('s') else 'Motor Engineer', s, flags=re.I)
    s = re.sub(r'\bSanitary\s+Engnr\b', 'Sanitary Engineer', s, flags=re.I)
    s = re.sub(r'\bTugboat\s+Engnr\b', 'Tugboat Engineer', s, flags=re.I)
    s = re.sub(r'\bCiv\s+Engnr\b', 'Civil Engineer', s, flags=re.I)
    s = re.sub(r'\bElect\s+Engnr\s+And\s+Plumber\b', 'Electrical Engineer & Plumber', s, flags=re.I)
    s = re.sub(r'\bEngnrs\b', 'Engineers', s, flags=re.I)
    s = re.sub(r'\bEngnr\.?\b', 'Engineer', s, flags=re.I)

    # 19. Hairdresser
    s = re.sub(r'\bHairdres[\'’]?r\b', 'Hairdresser', s, flags=re.I)
    s = re.sub(r'\bHairdressr\b', 'Hairdresser', s, flags=re.I)

    # 20. Colliery Proprietor
    s = re.sub(r'\bLliery\s+Prptr\b', 'Colliery Proprietor', s, flags=re.I)

    # 21. Coal Exporters
    s = re.sub(r'\bAl\s+Exporters\s+And\s+Patent\s+Fuel\s+Merchants\b', 'Coal Exporters & Patent Fuel Merchants', s, flags=re.I)

    # 22. J.p. Solicitor -> Justice of the Peace & Solicitor
    s = re.sub(r'\bJ\.?P\.?\s+solicit(?:o|r)\b', 'Justice of the Peace & Solicitor', s, flags=re.I)

    # 23. Corn Merchants
    s = re.sub(r'\brn\s+Merchants?\b', lambda m: 'Corn Merchants' if m.group(0).lower().endswith('s') else 'Corn Merchant', s, flags=re.I)

    # 24. Annealr -> Annealer
    s = re.sub(r'\bAnnealr\b', 'Annealer', s, flags=re.I)

    # 25. Signal Fitter
    s = re.sub(r'\bSignal(?:f|fitt|fit|ft)?tr\b', 'Signal Fitter', s, flags=re.I)
    s = re.sub(r'\bSignal\s+(?:Fitr|Fittr|Ftr)\b', 'Signal Fitter', s, flags=re.I)
    s = re.sub(r'\bSignalfitter\b', 'Signal Fitter', s, flags=re.I)

    # 26. Confectioner (Conf'tr / Nf'tr)
    s = re.sub(r'\b(?:Baker\s+&\s+)?(?:Conf|Nf)[\'’]?trs\b', lambda m: 'Baker & Confectioners' if 'baker' in m.group(0).lower() else 'Confectioners', s, flags=re.I)
    s = re.sub(r'\b(?:Baker\s+&\s+)?(?:Conf|Nf)[\'’]?tr\.?\b', lambda m: 'Baker & Confectioner' if 'baker' in m.group(0).lower() else 'Confectioner', s, flags=re.I)
    s = re.sub(r'\bWhlsale\s+Conftr\b', 'Wholesale Confectioner', s, flags=re.I)

    # 27. Hammerman
    s = re.sub(r'\bHammermn\b', 'Hammerman', s, flags=re.I)
    s = re.sub(r'\bHammermar\b', 'Hammerman', s, flags=re.I)

    # 28. Wagonmaker
    s = re.sub(r'\bWag(?:on|\')?nmkr\b', 'Wagonmaker', s, flags=re.I)
    s = re.sub(r'\bwagon\s+mkr\b', 'Wagonmaker', s, flags=re.I)

    # Strip trailing period on target nouns
    if s.endswith('.'):
        for target in ['Coal Merchant.', 'Confectioner.', 'Engineer.', 'Draughtsman.', 'Timekeeper.', 'Signal Fitter.', 'Wagonmaker.']:
            if s.endswith(target):
                s = s[:-1]
                break

    return s

def handle_trapped_names(row: dict) -> bool:
    tr = row.get('trade', '')
    yr = row.get('year', '')
    st = row.get('street', '')
    no = row.get('house_number', '')
    sur = row.get('surname', '')
    fore = row.get('forename', '')

    # 1908 Price Street 59: surname: "c'al tipper", forename: 'John', trade: 'Harris'
    if yr == '1908' and 'Price Street' in st and no == '59' and "c'al tipper" in sur:
        row['surname'] = 'Harris'
        row['forename'] = 'John'
        row['trade'] = 'Coal Tipper'
        return True

    # 1908 Price Street 33: surname: 'Jackson', forename: 'Geo. dock police', trade: ''
    if yr == '1908' and 'Price Street' in st and no == '33' and 'dock police' in fore.lower():
        row['surname'] = 'Jackson'
        row['forename'] = 'Geo.'
        row['trade'] = 'Dock Police'
        return True

    # 1936 High Street: surname: 'F. Blackborow coal mercht'
    if yr == '1936' and 'High Street' in st and 'blackborow' in sur.lower() and 'mercht' in sur.lower():
        row['surname'] = 'Blackborow'
        row['forename'] = 'F.'
        row['trade'] = 'Coal Merchant'
        return True

    # 1936 Tredegar Street 5: surname: 'Bros. hay and Newcombe corn merchants'
    if yr == '1936' and 'Tredegar Street' in st and no == '5' and 'newcombe' in sur.lower():
        row['surname'] = 'Newcombe'
        row['forename'] = 'Bros.'
        row['trade'] = 'Hay & Corn Merchants'
        return True

    # 1936 Coomassie Street 36: trade: 'Shop Kemp J. W. & Co. coppersmiths and plumbers'
    if yr == '1936' and 'Coomassie' in st and no == '36' and 'coppersmiths' in tr.lower():
        row['trade'] = 'Coppersmiths & Plumbers'
        return True

    return False

def main():
    if not DATA_CSV.exists():
        print(f"Error: {DATA_CSV} not found.")
        return

    # Backup data.csv
    print(f"Backing up {DATA_CSV} to {BACKUP_CSV}...")
    shutil.copy2(DATA_CSV, BACKUP_CSV)

    rows = []
    fieldnames = []
    with open(DATA_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {DATA_CSV}.")

    modified_count = 0
    trade_changes = Counter()

    for r in rows:
        old_trade = r.get("trade", "")
        old_sur = r.get("surname", "")
        old_fore = r.get("forename", "")
        old_bld = r.get("building_name", "")

        # 1. Handle trapped names
        handle_trapped_names(r)

        # 2. Clean trade string
        cur_trade = r.get("trade", "")
        new_trade = clean_trade(cur_trade)
        if new_trade != cur_trade:
            r["trade"] = new_trade

        if (r["trade"] != old_trade or r["surname"] != old_sur or
            r["forename"] != old_fore or r.get("building_name", "") != old_bld):
            modified_count += 1
            if r["trade"] != old_trade:
                trade_changes[f"{old_trade}  ->  {r['trade']}"] += 1

    print(f"\nTotal rows modified: {modified_count}")
    print("\nTop 40 Trade Expansions Applied:")
    for change, count in trade_changes.most_common(40):
        print(f"  {count:4d}: {change}")

    print(f"\nWriting updated records back to {DATA_CSV}...")
    with open(DATA_CSV, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Successfully wrote healed data.csv!")

if __name__ == "__main__":
    main()
