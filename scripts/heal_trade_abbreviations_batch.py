#!/usr/bin/env python3
"""
scripts/heal_trade_abbreviations_batch.py

Expands abbreviations and contractions in trades while strictly preserving
occupational authenticity (no changing distinct occupations into generic ones,
e.g. keeping Hewer, Smith, Plater, Collier distinct).

Targets:
1. Prov Mer. -> Provision Merchant (and variants)
2. Hairdsr -> Hairdresser (and variants)
3. Tob & Fncy Gds -> Tobacconist & Fancy Goods (and Tob / Fncy Gds references)
4. Ladies Outftr -> Ladies Outfitter (and Outftr / Outftrs / etc.)
5. Nfectioner / Nfectioners -> Confectioners
6. Rest'rnt -> Restaurant (and Restrnt / Restaurnt)
7. Btchers / Btcher -> Butchers / Butcher (and Pork Btchr, Shipping Btchr, etc.)
8. Warehse -> Warehouse (confirmed 100% Warehouse across all commercial premises)
9. Surg Applnce Maker -> Surgical Appliance Maker
10. Gr'crs -> Grocers (and Grcr, Grocr, Greengcr, etc.)
11. Brush Manufacturers & Hardware Dlr -> Brush Manufacturers & Hardware Dealer (and Dlr/Dlrs/Dealr)
12. Tobcnst / Tobacnst -> Tobacconist
13. Dressmkr / Dressmkrs -> Dressmaker / Dressmakers
14. Dent'st -> Dentist
15. China Dealr / China Dlr -> China Dealer
16. Engrocer / Geengrocer -> Greengrocer
+ Disentangling names trapped inside these trade strings.
"""

import csv
import re
import shutil
from pathlib import Path
from collections import Counter

DATA_CSV = Path("data.csv")
BACKUP_CSV = Path("data.csv.bak_before_trades_expansion")

def clean_dlr_patterns(trade: str) -> str:
    s = trade
    # Specific compound dealer expansions
    s = re.sub(r'\bFurn(?:tr|ntr|uintr)?\.?\s+D(?:ea)?lrs?\b', lambda m: 'Furniture Dealers' if 's' in m.group(0).lower() else 'Furniture Dealer', s, flags=re.I)
    s = re.sub(r'\bGen(?:l)?\.?\s+D(?:ea)?lrs?\b', lambda m: 'General Dealers' if 's' in m.group(0).lower() else 'General Dealer', s, flags=re.I)
    s = re.sub(r'\bW(?:a)?rdr(?:b|be)?\.?\s+D(?:ea)?lrs?\b', lambda m: 'Wardrobe Dealers' if 's' in m.group(0).lower() else 'Wardrobe Dealer', s, flags=re.I)
    s = re.sub(r'\bEarth\'?ware\.?\s+D(?:ea)?lrs?\b', lambda m: 'Earthenware Dealers' if 's' in m.group(0).lower() else 'Earthenware Dealer', s, flags=re.I)
    s = re.sub(r'\bEarthenw\.?\s+D(?:ea)?lrs?\b', lambda m: 'Earthenware Dealers' if 's' in m.group(0).lower() else 'Earthenware Dealer', s, flags=re.I)
    s = re.sub(r'\bCrn\s+Dlrs\b', 'Corn Dealers', s, flags=re.I)
    s = re.sub(r'\b2Nd Hand\b', 'Second Hand', s, flags=re.I)
    s = re.sub(r'\b2nd-hand\b', 'Second Hand', s, flags=re.I)
    s = re.sub(r'\bSecond-Hd\b', 'Second Hand', s, flags=re.I)
    s = re.sub(r'\bMar(?:ine)?\.?\s+Store\s+D(?:ea)?lr\b', 'Marine Store Dealer', s, flags=re.I)
    s = re.sub(r'\bMar\.?\s+Store\s+D(?:ea)?lr\b', 'Marine Store Dealer', s, flags=re.I)
    s = re.sub(r'\bmar\s+store\s+dlr\b', 'Marine Store Dealer', s, flags=re.I)
    s = re.sub(r'\bProv\s+Dlrs\b', 'Provision Dealers', s, flags=re.I)
    s = re.sub(r'\bProv\s+Dlr\b', 'Provision Dealer', s, flags=re.I)

    # Word-level replacement for Dlr / Dealr
    s = re.sub(r'\bDlrs\.?\b', 'Dealers', s, flags=re.I)
    s = re.sub(r'\bDealrs\.?\b', 'Dealers', s, flags=re.I)
    s = re.sub(r'\bDlr\.?\b', 'Dealer', s, flags=re.I)
    s = re.sub(r'\bDealr\.?\b', 'Dealer', s, flags=re.I)
    s = re.sub(r'-Dealers\b', ' Dealers', s, flags=re.I)
    s = re.sub(r'-Dealer\b', ' Dealer', s, flags=re.I)
    return s

def clean_trade(trade: str) -> str:
    if not trade:
        return trade
    t = trade.strip()

    # 1. Provision Merchant / Prov Mer
    t = re.sub(r'\bProv\.?\s*Merchants\b', 'Provision Merchants', t, flags=re.I)
    t = re.sub(r'\bProv\.?\s*Merchts\b', 'Provision Merchants', t, flags=re.I)
    t = re.sub(r'\bProv\.?\s*Mercht\b', 'Provision Merchant', t, flags=re.I)
    t = re.sub(r'\bProv\.?\s*Mer\.?\b', 'Provision Merchant', t, flags=re.I)
    t = re.sub(r'\bWholesale\s+Prov\s+Merchts\b', 'Wholesale Provision Merchants', t, flags=re.I)
    t = re.sub(r'\b& Co\.\s*wholesale\s+prov\s+merchts\b', '& Co. Wholesale Provision Merchants', t, flags=re.I)
    t = re.sub(r'\bprov\s+merchants,\s*Ltd\.\b', 'Provision Merchants Ltd.', t, flags=re.I)
    t = re.sub(r'\bprov\.\s*merchants,\s*reg office and warehouse,\s*Ltd\.\b', 'Provision Merchants, Reg Office & Warehouse Ltd.', t, flags=re.I)
    t = re.sub(r'\bProv\.\s*Merchants[;,]\s*Reg Office And Warehouse\b', 'Provision Merchants, Reg Office & Warehouse', t, flags=re.I)
    t = re.sub(r'\bCheese Factors & Prov\.\s*Merchants\b', 'Cheese Factors & Provision Merchants', t, flags=re.I)
    t = re.sub(r'\bShip Chandlers & Prov\.\s*Mer\b', 'Ship Chandlers & Provision Merchants', t, flags=re.I)
    t = re.sub(r'\bwholesale & retail grocr & provision merchant and Italian warehouseman\b', 'Wholesale & Retail Grocer, Provision Merchant & Italian Warehouseman', t, flags=re.I)
    t = re.sub(r'\bwholesale & retail grocr provision merchant and Italian warehouseman\b', 'Wholesale & Retail Grocer, Provision Merchant & Italian Warehouseman', t, flags=re.I)

    # 2. Hairdresser / Hairdsr
    t = re.sub(r'\bHairds\'?r\b', 'Hairdresser', t, flags=re.I)
    t = re.sub(r'\bHairds\b', 'Hairdresser', t, flags=re.I)

    # 3. Tobacconist & Fancy Goods / Tob / Fncy Gds
    t = re.sub(r'\bTob\s*&\s*Fncy\s*Gds\b', 'Tobacconist & Fancy Goods', t, flags=re.I)
    t = re.sub(r'\btobacconist\s*&\s*fancy\s*gds\b', 'Tobacconist & Fancy Goods', t, flags=re.I)
    t = re.sub(r'\bTob\.?\s*(?:&|and)\s*Fancy\s*Goods\b', 'Tobacconist & Fancy Goods', t, flags=re.I)
    t = re.sub(r'\bTob\.?\s*(?:&|and)\s*Conf\.?\b', 'Tobacconist & Confectioner', t, flags=re.I)
    t = re.sub(r'\bFncy\s*Reposry\b', 'Fancy Repository', t, flags=re.I)
    t = re.sub(r'\bWhl\s+Toy\s+&\s+Fncy\s+Gds\s+Merc\b', 'Wholesale Toy & Fancy Goods Merchant', t, flags=re.I)
    t = re.sub(r'\bGds\s+Clerk\b', 'Goods Clerk', t, flags=re.I)

    # 4. Outfitter / Outftr
    t = re.sub(r'\bLadies\s+Outftr\b', 'Ladies Outfitter', t, flags=re.I)
    t = re.sub(r'\bTailor\s*&\s*Outftr\b', 'Tailor & Outfitter', t, flags=re.I)
    t = re.sub(r'\bChlds\s+Outftr\b', 'Children\'s Outfitter', t, flags=re.I)
    t = re.sub(r'\bOutfttrs\b', 'Outfitters', t, flags=re.I)
    t = re.sub(r'\bOutfit\'?rs\b', 'Outfitters', t, flags=re.I)
    t = re.sub(r'\bOutftrs\b', 'Outfitters', t, flags=re.I)
    t = re.sub(r'\bOutfitr\b', 'Outfitter', t, flags=re.I)
    t = re.sub(r'\bOutftr\b', 'Outfitter', t, flags=re.I)
    t = re.sub(r'\bPawnbrokers\s*&\s*Outfittrs\b', 'Pawnbrokers & Outfitters', t, flags=re.I)

    # 5. Confectioner / Nfectioner
    t = re.sub(r'\bNfectioners\b', 'Confectioners', t, flags=re.I)
    t = re.sub(r'\bNfectioner\b', 'Confectioner', t, flags=re.I)

    # 6. Restaurant / Rest'rnt
    t = re.sub(r'\bRest[\'’]?rnt\b', 'Restaurant', t, flags=re.I)
    t = re.sub(r'\bRestaurnt\b', 'Restaurant', t, flags=re.I)

    # 7. Butcher / Butchers / Btcher / Btchers / Pork Btchr
    t = re.sub(r'\bBtcher,\s*Pork\b', 'Pork Butcher', t, flags=re.I)
    t = re.sub(r'\b(?:Pork|Prk|Pk)\s*Btch(?:r|er)?\.?\b', 'Pork Butcher', t, flags=re.I)
    t = re.sub(r'\bPorkbtchr\b', 'Pork Butcher', t, flags=re.I)
    t = re.sub(r'\bPork\s*Btch\b', 'Pork Butcher', t, flags=re.I)
    t = re.sub(r'\bShip(?:\'?[a-z]+)?\s*Btchr\b', 'Shipping Butcher', t, flags=re.I)
    t = re.sub(r'\bBtchrs\.?\b', 'Butchers', t, flags=re.I)
    t = re.sub(r'\bBtchers\b', 'Butchers', t, flags=re.I)
    t = re.sub(r'\bBtchr\b', 'Butcher', t, flags=re.I)
    t = re.sub(r'\bBtcher\b', 'Butcher', t, flags=re.I)
    t = re.sub(r'\bPk\s+Btcher\s+And\s+Sausage\s+Manufact\'?R\b', 'Pork Butcher & Sausage Manufacturer', t, flags=re.I)

    # 8. Warehouse / Warehse
    t = re.sub(r'\bToy\s+Warehse\b', 'Toy Warehouse', t, flags=re.I)
    t = re.sub(r'\bBoot\s+Warehse\b', 'Boot Warehouse', t, flags=re.I)
    t = re.sub(r'\bBoot\s+Wareho\b', 'Boot Warehouse', t, flags=re.I)
    t = re.sub(r'\bToy\s+And\s+Fancy\s+Warehse\b', 'Toy & Fancy Warehouse', t, flags=re.I)
    t = re.sub(r'\bMusic\s+Warehse\b', 'Music Warehouse', t, flags=re.I)
    t = re.sub(r'\bStationer\s+Book\s+And\s+Music\s+Warehse\b', 'Stationer, Book & Music Warehouse', t, flags=re.I)
    t = re.sub(r'\bProv\.\s*Warehse\b', 'Provision Warehouse', t, flags=re.I)
    t = re.sub(r'\bConf\.\s*Warehse\b', 'Confectionery Warehouse', t, flags=re.I)
    t = re.sub(r'\bWarehse\b', 'Warehouse', t, flags=re.I)

    # 9. Surgical Appliance Maker / Surg Applnce Maker
    t = re.sub(r'\bSurg\s+Applnce\s+Maker\b', 'Surgical Appliance Maker', t, flags=re.I)

    # 10. Grocers / Gr'crs
    t = re.sub(r'\bGr[\'’]?crs\b', 'Grocers', t, flags=re.I)
    t = re.sub(r'\bGrcrs\b', 'Grocers', t, flags=re.I)
    t = re.sub(r'\bSharrem & Co\.grcrs\b', 'Sharrem & Co. Grocers', t, flags=re.I)
    t = re.sub(r'\bGrcrs\s+Assistant\b', 'Grocer\'s Assistant', t, flags=re.I)
    t = re.sub(r'\bFamily\s+Grocr\b', 'Family Grocer', t, flags=re.I)
    t = re.sub(r'\bGrocr\s*&\s*Bkr\b', 'Grocer & Baker', t, flags=re.I)
    t = re.sub(r'\bBakr\s*&\s*Grcr\b', 'Baker & Grocer', t, flags=re.I)
    t = re.sub(r'\bGrcr\s*&\s*Bkr\b', 'Grocer & Baker', t, flags=re.I)
    t = re.sub(r'\bGrcr\s*&\s*Conf\b', 'Grocer & Confectioner', t, flags=re.I)
    t = re.sub(r'\bPotato Merchan & Green Grocr\b', 'Potato Merchant & Greengrocer', t, flags=re.I)
    t = re.sub(r'\bGrcr\b', 'Grocer', t, flags=re.I)
    t = re.sub(r'\bGrocr\b', 'Grocer', t, flags=re.I)

    # Greengrocer contractions
    t = re.sub(r'\bGreengrcrs\b', 'Greengrocers', t, flags=re.I)
    t = re.sub(r'\bGreengcr\s+And\s+Confectioner\b', 'Greengrocer & Confectioner', t, flags=re.I)
    t = re.sub(r'\bGreengr[\'’]?cr\b', 'Greengrocer', t, flags=re.I)
    t = re.sub(r'\bGreeng[\'’]?cr\b', 'Greengrocer', t, flags=re.I)
    t = re.sub(r'\bGrngrcr\b', 'Greengrocer', t, flags=re.I)
    t = re.sub(r'\bGrngcr\.?\b', 'Greengrocer', t, flags=re.I)

    # 11. Dlr / Dealr (Dealer / Dealers)
    t = clean_dlr_patterns(t)

    # 12. Tobacconist contractions
    t = re.sub(r'\bTobacnsts\b', 'Tobacconists', t, flags=re.I)
    t = re.sub(r'\bTob[\'’]?conist\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobcnst\.?\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobacnst\.?\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobac[\'’]nist\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobacconst\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobac[\'’]nst\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobacnist\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobac[\'’]st\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobacst\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bToba[\'’]st\b', 'Tobacconist', t, flags=re.I)
    t = re.sub(r'\bTobacconist And Insurance Brokers\b', 'Tobacconist & Insurance Brokers', t, flags=re.I)
    t = re.sub(r'\bTobacconist And Newsagent\b', 'Tobacconist & Newsagent', t, flags=re.I)

    # 13. Dressmaker / Dressmkr
    t = re.sub(r'\bDrapers,?\s+Dressmkrs\b', 'Drapers & Dressmakers', t, flags=re.I)
    t = re.sub(r'\bDressmk[\'’]?rs\b', 'Dressmakers', t, flags=re.I)
    t = re.sub(r'\bDressmkrs\b', 'Dressmakers', t, flags=re.I)
    t = re.sub(r'\bDressmkr\.?\b', 'Dressmaker', t, flags=re.I)
    t = re.sub(r'\bDressmk\b', 'Dressmaker', t, flags=re.I)
    t = re.sub(r'\bDressmks\b', 'Dressmaker', t, flags=re.I)

    # 14. Dentist / Dent'st
    t = re.sub(r'\bDent[\'’]st\b', 'Dentist', t, flags=re.I)

    # 15. China Dealer (handled by China Dlr / China Dealr in clean_dlr_patterns)

    # 16. Greengrocer / Engrocer typo
    t = re.sub(r'\bGeengrocer\b', 'Greengrocer', t, flags=re.I)

    return t

def handle_trapped_names(row: dict) -> bool:
    """Special cases where person names or roles were trapped in trade field."""
    tr = row.get('trade', '')
    yr = row.get('year', '')
    st = row.get('street', '')
    no = row.get('house_number', '')

    modified = False

    # 1900 South Market Street 1: Davies, greengcr
    if yr == '1900' and 'South Market' in st and no == '1' and 'Davies, greengcr' in tr:
        row['surname'] = 'Davies'
        row['forename'] = 'Mrs. C. M.'
        row['trade'] = 'Greengrocer'
        return True

    # 1901 Dock Street 70: Fothergill, tob'co mfr
    if yr == '1901' and 'Dock Street' in st and no == '70' and 'Fothergill' in tr:
        row['surname'] = 'Fothergill'
        row['forename'] = 'Geo.'
        row['trade'] = 'Tobacco Manufacturer'
        return True

    # 1902 Herbert Street 5: Humphreys, hairdsr
    if yr == '1902' and 'Herbert' in st and no == '5' and 'Humphreys' in tr:
        row['surname'] = 'Humphreys'
        row['forename'] = 'H. R.'
        row['trade'] = 'Hairdresser'
        return True

    # 1902 Malpas Road 77: William Hormann Mrs, dressmkr
    if yr == '1902' and 'Malpas' in st and no == '77' and 'Hormann' in tr:
        row['surname'] = 'Hormann'
        row['forename'] = 'Mrs. William'
        row['trade'] = 'Dressmaker'
        return True

    # 1913 Fair Oak Terrace 24-5: Matthews, tobcnst
    if yr == '1913' and 'Fair Oak' in st and 'Matthews' in tr:
        row['surname'] = 'Matthews'
        row['forename'] = 'W. J.'
        row['trade'] = 'Tobacconist'
        return True

    # 1915 Clytha Park Road: Bezant, dressmkrs
    if yr == '1915' and 'Clytha Park' in st and 'Bezant' in tr:
        row['surname'] = 'Bezant'
        row['forename'] = 'C. & E.'
        row['trade'] = 'Dressmakers'
        return True

    # 1915 Dolphin Street 86: Davies, greengrcr
    if yr == '1915' and 'Dolphin' in st and no == '86' and 'Davies' in tr:
        row['surname'] = 'Davies'
        row['forename'] = 'Mrs. A. M.'
        row['trade'] = 'Greengrocer'
        return True

    # 1925 Caerleon Road 43: Robertson, tobacnst
    if yr == '1925' and 'Caerleon' in st and no == '43' and 'Robertson' in tr:
        row['surname'] = 'Robertson'
        row['forename'] = 'W. E.'
        row['trade'] = 'Tobacconist'
        return True

    # 1920 Alexandra Road 80: greengcr, Heard
    if yr == '1920' and 'Alexandra' in st and no == '80' and 'Heard' in tr:
        row['surname'] = 'Heard'
        row['forename'] = 'Albert E.'
        row['trade'] = 'Greengrocer'
        return True

    # 1906 Commercial Street: Budge Madame, dressmkr
    if yr == '1906' and 'Commercial' in st and 'Budge' in tr:
        row['surname'] = 'Budge'
        row['forename'] = 'Madame'
        row['trade'] = 'Dressmaker'
        return True

    # 1906 Railway Street 91: lot, gds grd
    if yr == '1906' and 'Railway' in st and no == '91' and 'gds grd' in tr:
        row['trade'] = 'Goods Guard'
        return True

    # 1903 Raglan Street 91: Watts, Lot, gds grd
    if yr == '1903' and 'Raglan' in st and no == '91' and 'Watts' in tr:
        row['surname'] = 'Watts'
        row['forename'] = 'Oliver'
        row['trade'] = 'Goods Guard'
        return True

    # 1924 Clytha Square 14: Pitchford pork btchr; Adams Miss L. L. supt.
    if yr == '1924' and 'Clytha Square' in st and no == '14' and 'Adams Miss' in tr:
        row['trade'] = 'Pork Butcher'
        return True

    # 1887 Robert Street 26: Hurley, cattle dealr
    if yr == '1887' and 'Robert' in st and no == '26' and 'Hurley' in tr:
        row['surname'] = 'Hurley'
        row['forename'] = 'Cornelius'
        row['trade'] = 'Cattle Dealer'
        return True

    # 1890 Market Street 4: Smith, earth' ware dlr
    if yr == '1890' and 'Market' in st and no == '4' and 'Smith' in tr:
        row['surname'] = 'Smith'
        row['forename'] = 'J.'
        row['trade'] = 'Earthenware Dealer'
        return True

    # 1895 Commercial Road 131: Goldstein, fancy dlr
    if yr == '1895' and 'Commercial' in st and no == '131' and 'Goldstein' in tr:
        row['surname'] = 'Goldstein'
        row['forename'] = 'Mrs.'
        row['trade'] = 'Fancy Dealer'
        return True

    # 1901 Marion Street 72: Sanders, marine dlr
    if yr == '1901' and 'Marion' in st and no == '72' and 'Sanders' in tr:
        row['surname'] = 'Sanders'
        row['forename'] = 'Mark'
        row['trade'] = 'Marine Dealer'
        return True

    # 1910 Chepstow Road 174a: Bevan R. china dlr.
    if yr == '1910' and 'Chepstow' in st and '174' in no and 'Bevan' in tr:
        row['surname'] = 'Bevan'
        row['forename'] = 'R.'
        row['trade'] = 'China Dealer'
        return True

    # 1920 Shaftesbury Street 56: furniture dlr, Knee
    if yr == '1920' and 'Shaftesbury' in st and no == '56' and 'Knee' in tr:
        row['surname'] = 'Knee'
        row['forename'] = 'Frank'
        row['trade'] = 'Furniture Dealer'
        return True

    # 1908 Chepstow Road 186: Summers | F. J. boot dlr
    if yr == '1908' and 'Chepstow' in st and no == '186' and 'F. J. boot dlr' in tr:
        row['surname'] = 'Summers'
        row['forename'] = 'F. J.'
        row['trade'] = 'Boot Dealer'
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

        # 1. Handle trapped names
        trapped_fixed = handle_trapped_names(r)

        # 2. Clean trade string
        cur_trade = r.get("trade", "")
        new_trade = clean_trade(cur_trade)
        if new_trade != cur_trade:
            r["trade"] = new_trade

        if r["trade"] != old_trade or r["surname"] != old_sur or r["forename"] != old_fore:
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
