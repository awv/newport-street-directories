#!/usr/bin/env python3
"""
scripts/heal_trade_abbreviations_batch2.py

Expands trade abbreviations (Batch 2) while strictly preserving
occupational authenticity (keeping distinct trades like Hewer, Smith, Plater intact).

Targets:
1. Ffee Tavern -> Coffee Tavern (and ffee Stall -> Coffee Stall, Coffee Tav, etc.)
2. Drapr -> Draper (and Draprs -> Drapers, Trav. Drapr, Fancy Draprs, etc.)
3. Leather Sellr -> Leather Seller
4. Fishmnger -> Fishmonger (and Fishmongr)
5. Brusmkrs -> Brushmakers (and Brushmkrs, Brushmkr, etc.)
6. Min. Water Mnf. -> Mineral Water Manufacturers (and Min Water Mfr, etc.)
7. Photogrphr -> Photographer (and Photographers, Photoghr, etc.)
8. Bakr And Confectioner -> Baker & Confectioner (and Bakr -> Baker)
9. Pawnbrokrs & Outfittrs -> Pawnbrokers & Outfitters
10. Proptr. -> Proprietor (and Cab Proptr, Taxi Proptr, Colliery Propr, etc.)
11. Grocers And Provision Mrchnts -> Grocers & Provision Merchants (and Coal Mrcht, Corn Mrcht, etc.)
12. Brssfndr -> Brassfounder (and Brass Fndrs -> Brassfounders, Ironfndr, etc.)
13. Dresskr -> Dressmaker
14. Funeral Furnshr -> Funeral Furnisher (and House Furnshr, Furnshr)
15. Basket Makers & Toy Dlrs -> Basket Makers & Toy Dealers
16. Drsmk -> Dressmaker (and Drsmkr)
17. Tobacnis -> Tobacconist
18. Bazaa -> Bazaar
19. Picture Framr -> Picture Framer (and pic. framrs -> Picture Framers)
20. Nfectioner -> Confectioner
21. Pork Butcher And Sausage Manufactr -> Pork Butcher & Sausage Manufacturer (and Hat Manufactrs, Grease Manufactr, etc.)
22. Boarding Ho -> Boarding House (and Boardg Ho, Boarding Ho.)
23. Ironmongrs -> Ironmongers (and Ironmngrs, Ironmngers, Ironmgers, irnmngrs)
24. Ship Ch'rs -> Ship Chandlers (and Ship Chan., Ship Chan)
25. Railway Gu'rd -> Railway Guard
+ Disentangling names and buildings trapped inside these trade strings.
"""

import csv
import re
import shutil
from pathlib import Path
from collections import Counter

DATA_CSV = Path("data.csv")
BACKUP_CSV = Path("data.csv.bak_before_trades_batch2")

def clean_trade(trade: str) -> str:
    if not trade:
        return trade
    s = trade.strip()

    # 1. Coffee Tavern / Coffee Stall / ffee
    s = re.sub(r'\bffee\s+Stall\b', 'Coffee Stall', s, flags=re.I)
    s = re.sub(r'\bFfee\s+Tavern\b', 'Coffee Tavern', s, flags=re.I)
    s = re.sub(r'\bCoffee\s+Tavr?\b', 'Coffee Tavern', s, flags=re.I)
    s = re.sub(r'\bCoffee\s+Ho\.?\b', 'Coffee House', s, flags=re.I)
    s = re.sub(r'\bCoffee\s+Rm\b', 'Coffee Room', s, flags=re.I)

    # 2. Draper
    s = re.sub(r'\bHouse\s+Furnish(?:er)?s\s+&\s+Draprs\b', 'House Furnishers & Drapers', s, flags=re.I)
    s = re.sub(r'\bHouse\s+Furnishrs\s+&\s+Draprs\b', 'House Furnishers & Drapers', s, flags=re.I)
    s = re.sub(r'\bFancy\s+Draprs\b', 'Fancy Drapers', s, flags=re.I)
    s = re.sub(r'\bTrav\.?\s+Drapr\b', 'Travelling Draper', s, flags=re.I)
    s = re.sub(r'\bTailor\s*&\s*Drapr\b', 'Tailor & Draper', s, flags=re.I)
    s = re.sub(r'\bUniversal\s+outfitters\s+draprs\b', 'Universal Outfitters & Drapers', s, flags=re.I)
    s = re.sub(r'\bDraprs\b', 'Drapers', s, flags=re.I)
    s = re.sub(r'\bDrapri?\b', 'Draper', s, flags=re.I)

    # 3. Leather Seller
    s = re.sub(r'\bLeather\s+Sellr\b', 'Leather Seller', s, flags=re.I)

    # 4. Fishmonger / Fishmongers (check endswith 's')
    s = re.sub(r'\bFishm(?:o|e)?ngrs\b', 'Fishmongers', s, flags=re.I)
    s = re.sub(r'\bFishm(?:o|e)?ngr\b', 'Fishmonger', s, flags=re.I)

    # 5. Brushmakers / Brushmaker
    s = re.sub(r'\b(?:Brus|Brush|brussn)m(?:a|k)?krs\.?\b', 'Brushmakers', s, flags=re.I)
    s = re.sub(r'\b(?:Brush|brusl?ı)m(?:a|k)?kr\.?\b', 'Brushmaker', s, flags=re.I)
    s = re.sub(r'\bBrush\s+Mnf\b', 'Brush Manufacturer', s, flags=re.I)
    s = re.sub(r'\bBrush\s+Mftrs\b', 'Brush Manufacturers', s, flags=re.I)
    s = re.sub(r'\bBrush\s+Mftr\b', 'Brush Manufacturer', s, flags=re.I)

    # 6. Mineral Water Manufacturers
    s = re.sub(r'\bMin\.?\s*Water\s+Mnf\.?\b', 'Mineral Water Manufacturers', s, flags=re.I)
    s = re.sub(r'\bMin\.?\s*Water\s+Mf(?:t)?rs\b', 'Mineral Water Manufacturers', s, flags=re.I)
    s = re.sub(r'\bMin\.?\s*Water\s+Mf(?:t)?r\b', 'Mineral Water Manufacturer', s, flags=re.I)
    s = re.sub(r'\bMin\.?\s*Water\s+Wks\b', 'Mineral Water Works', s, flags=re.I)

    # 7. Photographer / Photographers
    s = re.sub(r'\bPainters\s+&\s+Photogrphrs\b', 'Painters & Photographers', s, flags=re.I)
    s = re.sub(r'\bPhotog\'?phrs\s+And\s+Framemakers\b', 'Photographers & Framemakers', s, flags=re.I)
    s = re.sub(r'\bPhotographers\s+And\s+Framemakers\b', 'Photographers & Framemakers', s, flags=re.I)
    s = re.sub(r'\bPhotogra(?:ph)?rs\b', 'Photographers', s, flags=re.I)
    s = re.sub(r'\bPhotograp\'?rs\b', 'Photographers', s, flags=re.I)
    s = re.sub(r'\bPhotogrprs\b', 'Photographers', s, flags=re.I)
    s = re.sub(r'\bPhotog\'?rs\b', 'Photographers', s, flags=re.I)
    s = re.sub(r'\bPhotograp\'?r\b', 'Photographer', s, flags=re.I)
    s = re.sub(r'\bPhotogr\'?pr\b', 'Photographer', s, flags=re.I)
    s = re.sub(r'\bPhotog\'?phr\b', 'Photographer', s, flags=re.I)
    s = re.sub(r'\bPhotogrph\b', 'Photographer', s, flags=re.I)
    s = re.sub(r'\bPhotog(?:r|h)?(?:p|ph|pr)?(?:r|er)\b', 'Photographer', s, flags=re.I)
    s = re.sub(r'\bPhotogrp\'?r\b', 'Photographer', s, flags=re.I)
    s = re.sub(r'\bPhotog\'?r\b', 'Photographer', s, flags=re.I)

    # 8. Baker
    s = re.sub(r'\bBakr\s+And\s+Confectioner\b', 'Baker & Confectioner', s, flags=re.I)
    s = re.sub(r'\bGrocer\s*&\s*Bakr\b', 'Grocer & Baker', s, flags=re.I)
    s = re.sub(r'\bBakr\s*&\s*Frutr\b', 'Baker & Fruiterer', s, flags=re.I)
    s = re.sub(r'\bBakr\b', 'Baker', s, flags=re.I)

    # 9. Pawnbrokers & Outfitters
    s = re.sub(r'\bPawnbrokrs\s*(?:&|and)?\s*Outfitters\b', 'Pawnbrokers & Outfitters', s, flags=re.I)
    s = re.sub(r'\bPawnbrokrs\s*(?:&|and)?\s*Outfittrs\b', 'Pawnbrokers & Outfitters', s, flags=re.I)
    s = re.sub(r'\bPawnbrkr\b', 'Pawnbroker', s, flags=re.I)
    s = re.sub(r'\bPawnbrokr\b', 'Pawnbroker', s, flags=re.I)
    s = re.sub(r'\bPawnbkr\b', 'Pawnbroker', s, flags=re.I)
    s = re.sub(r'\bOutfittrs\b', 'Outfitters', s, flags=re.I)

    # 10. Proprietor / Proprietors
    s = re.sub(r'\bFruiterer\s+Florist\s+Seedsman\s+Temperance\s+Bar\s+Proprtr\s+And\s+Confectioner\b', 'Fruiterer, Florist, Seedsman, Temperance Bar Proprietor & Confectioner', s, flags=re.I)
    s = re.sub(r'\bCab\s+Propr?\'?(?:t|i)?(?:e|r)?(?:t)?(?:r|tor)?s\b', 'Cab Proprietors', s, flags=re.I)
    s = re.sub(r'\bCab\s+Propr?\'?(?:t|i)?(?:e|r)?(?:t)?(?:r|tor)?\.?\b', 'Cab Proprietor', s, flags=re.I)
    s = re.sub(r'\bCab\s+Prop\'?Tr\b', 'Cab Proprietor', s, flags=re.I)
    s = re.sub(r'\bCab\.\s+Propr\b', 'Cab Proprietor', s, flags=re.I)
    s = re.sub(r'\bTaxi(?:cab)?\s+Propr?\'?(?:t|i)?(?:e|r)?(?:t)?(?:r)?s?\b', 'Taxi Proprietor', s, flags=re.I)
    s = re.sub(r'\bTaxi\s+Prop\b', 'Taxi Proprietor', s, flags=re.I)
    s = re.sub(r'\bColliery\s+Propr?\'?(?:t|i)?(?:e|r)?(?:t)?(?:r)?s\b', 'Colliery Proprietors', s, flags=re.I)
    s = re.sub(r'\bColliery\s+Propr?\'?(?:t|i)?(?:e|r)?(?:t)?(?:r)?\b', 'Colliery Proprietor', s, flags=re.I)
    s = re.sub(r'\bcoll\.\s+propr\b', 'Colliery Proprietor', s, flags=re.I)
    s = re.sub(r'\bFurniture\s+Wareho\.\s+&\s+Van\s+Propr?\'?(?:t|i)?(?:e|r)?(?:t)?r\b', 'Furniture Warehouse & Van Proprietor', s, flags=re.I)
    s = re.sub(r'\bFurniture\s+Warehouse\s+&\s+Van\s+Proptr\b', 'Furniture Warehouse & Van Proprietor', s, flags=re.I)
    s = re.sub(r'\bCharabanc\s+Proptr,?\s+Motor\s+Haulage\s+Contractor\b', 'Charabanc Proprietor & Motor Haulage Contractor', s, flags=re.I)
    s = re.sub(r'\bProptr\.?\b', 'Proprietor', s, flags=re.I)
    s = re.sub(r'\bPropr\'?tors\b', 'Proprietors', s, flags=re.I)
    s = re.sub(r'\bProprietrs\b', 'Proprietors', s, flags=re.I)
    s = re.sub(r'\bProprietr\b', 'Proprietor', s, flags=re.I)
    s = re.sub(r'\bPropr\b', 'Proprietor', s, flags=re.I)

    # 11. Merchants
    s = re.sub(r'\bGrocers\s+And\s+Provision\s+Mrchnts\b', 'Grocers & Provision Merchants', s, flags=re.I)
    s = re.sub(r'\bCoal\s*mrch(?:n)?t\b', 'Coal Merchant', s, flags=re.I)
    s = re.sub(r'\bCorn\s*mrch(?:n)?t\b', 'Corn Merchant', s, flags=re.I)
    s = re.sub(r'\b(?:Corn|Crn)\s+(?:And\s+Commission\s+)?Mrchnts\b', 'Corn Merchants', s, flags=re.I)
    s = re.sub(r'\bCorn\s+And\s+Commission\s+Mrchts\b', 'Corn & Commission Merchants', s, flags=re.I)
    s = re.sub(r'\bCorn\s+Mrchts\b', 'Corn Merchants', s, flags=re.I)
    s = re.sub(r'\b(?:Prvisn|Provsn)\s+Mrcht\b', 'Provision Merchant', s, flags=re.I)
    s = re.sub(r'\bIron\s+Mrchts\b', 'Iron Merchants', s, flags=re.I)
    s = re.sub(r'\bIron\s+Mrcht\b', 'Iron Merchant', s, flags=re.I)
    s = re.sub(r'\bGlass\s+&\s+China\s+Mrchnts\b', 'Glass & China Merchants', s, flags=re.I)
    s = re.sub(r'\bGlass\s+Mrcht\b', 'Glass Merchant', s, flags=re.I)
    s = re.sub(r'\bSalt\s+Mrcht\b', 'Salt Merchant', s, flags=re.I)
    s = re.sub(r'\bLime\s+Mrcht\b', 'Lime Merchant', s, flags=re.I)
    s = re.sub(r'\bLeather\s+Mrcht\.?\b', 'Leather Merchant', s, flags=re.I)
    s = re.sub(r'\btmbr\s+mrchnts\.?\b', 'Timber Merchants', s, flags=re.I)
    s = re.sub(r'\bWine\s+Mrcht\s+\[Ant&\s+Auctioneer\b', 'Wine Merchant & Auctioneer', s, flags=re.I)
    s = re.sub(r'\bcoal\s+merchants,\s*Walker\s+iron\s*&\s*metal\s*mrchnts\b', 'Coal, Iron & Metal Merchants', s, flags=re.I)

    # 12. Brassfounder / Ironfounder / Glassfounder
    s = re.sub(r'\bBrssfndr\b', 'Brassfounder', s, flags=re.I)
    s = re.sub(r'\bBrassfndr\b', 'Brassfounder', s, flags=re.I)
    s = re.sub(r'\bbrssfoundr\b', 'Brassfounder', s, flags=re.I)
    s = re.sub(r'\bBrass\s+Fndrs\b', 'Brassfounders', s, flags=re.I)
    s = re.sub(r'\bBrass\s+Fndr\b', 'Brassfounder', s, flags=re.I)
    s = re.sub(r'\bIronfndr\b', 'Ironfounder', s, flags=re.I)
    s = re.sub(r'\bglassfndr\b', 'Glassfounder', s, flags=re.I)
    s = re.sub(r'\bBrassfndr\s+And\s+Ironmonger\s+\[Cher\b', 'Brassfounder & Ironmonger', s, flags=re.I)
    s = re.sub(r'\bFndry\s+Hd\b', 'Foundry Hand', s, flags=re.I)
    s = re.sub(r'\bFndryman\b', 'Foundryman', s, flags=re.I)

    # 13 & 16. Dressmaker
    s = re.sub(r'\bDresskr\b', 'Dressmaker', s, flags=re.I)
    s = re.sub(r'\bDrsmk(?:r)?\.?\b', 'Dressmaker', s, flags=re.I)

    # 14. Furnisher
    s = re.sub(r'\bFuneral\s+Furnshr\b', 'Funeral Furnisher', s, flags=re.I)
    s = re.sub(r'\bHouse\s+Furnshr\b', 'House Furnisher', s, flags=re.I)
    s = re.sub(r'\bCabinet\s+Makr\s+&\s+House\s+Furnshr\b', 'Cabinet Maker & House Furnisher', s, flags=re.I)
    s = re.sub(r'\bFurnshr\b', 'Furnisher', s, flags=re.I)

    # 15. Basket Makers & Toy Dealers
    s = re.sub(r'\bbasket\s+makrs\s+&\s+toy\s+(?:dllrs|dealers\.?)\b', 'Basket Makers & Toy Dealers', s, flags=re.I)

    # 17. Tobacconist
    s = re.sub(r'\bTobacnis\b', 'Tobacconist', s, flags=re.I)

    # 18. Bazaar
    s = re.sub(r'\bBazaa\b', 'Bazaar', s, flags=re.I)

    # 19. Picture Framer
    s = re.sub(r'\bPicture\s*framr\b', 'Picture Framer', s, flags=re.I)
    s = re.sub(r'\bpic\.?\s*framrs\b', 'Picture Framers', s, flags=re.I)

    # 20. Confectioner (Nfectioner typo)
    s = re.sub(r'\bNfectioners\b', 'Confectioners', s, flags=re.I)
    s = re.sub(r'\bNfectioner\b', 'Confectioner', s, flags=re.I)

    # 21. Manufacturer
    s = re.sub(r'\bPork\s+Butch?e?r?\s+And\s+Sausage\s+Manufactr\b', 'Pork Butcher & Sausage Manufacturer', s, flags=re.I)
    s = re.sub(r'\bManufactrs\s+Of\s+Weldless\s+Steel\s+Tubes\b', 'Manufacturers Of Weldless Steel Tubes', s, flags=re.I)
    s = re.sub(r'\bGrease\s+Manufactr\b', 'Grease Manufacturer', s, flags=re.I)
    s = re.sub(r'\bHat\s+Manufactrs\b', 'Hat Manufacturers', s, flags=re.I)
    s = re.sub(r'\bBoot\s+Manufactr\.?\b', 'Boot Manufacturer', s, flags=re.I)
    s = re.sub(r'\bManufactrs\s+Agt\b', 'Manufacturers\' Agent', s, flags=re.I)
    s = re.sub(r'\bBuilders\'?\s+Mercht?&Brick\s+Manufactr\b', 'Builders\' Merchant & Brick Manufacturer', s, flags=re.I)
    s = re.sub(r'\bbuilders\'\s+mer\.\s+&\s+brick\s+manufactr\.?\b', 'Builders\' Merchant & Brick Manufacturer', s, flags=re.I)
    s = re.sub(r'\baerated\s+water\s+manufactrs,?\s*—?T\.\s*Penny,?\s*manager\b', 'Aerated Water Manufacturers (T. Penny, mgr.)', s, flags=re.I)
    s = re.sub(r'\bCurrier\s+Leather\s+Merchant\s+Saddler\s+&\s+Harness\s+Manufactr\b', 'Currier, Leather Merchant, Saddler & Harness Manufacturer', s, flags=re.I)

    # 22. Boarding House
    s = re.sub(r'\bBoard(?:ing|g)\.?\s+Ho\.?\b', 'Boarding House', s, flags=re.I)
    s = re.sub(r'\bBoardg\s+House\b', 'Boarding House', s, flags=re.I)

    # 23. Ironmongers
    s = re.sub(r'\b(?:Ironm(?:o|n|g)?ngrs|Ironmngers|Ironmgers|irnmngrs)\b', 'Ironmongers', s, flags=re.I)

    # 24. Ship Chandlers
    s = re.sub(r'\bShip\s+Ch\'?rs\b', 'Ship Chandlers', s, flags=re.I)
    s = re.sub(r'\bShip\s+Chan\.?\b', 'Ship Chandlers', s, flags=re.I)

    # 25. Railway Guard
    s = re.sub(r'\bRailway\s+Gu\'?rd\b', 'Railway Guard', s, flags=re.I)

    return s

def handle_trapped_names_batch2(row: dict) -> bool:
    tr = row.get('trade', '')
    yr = row.get('year', '')
    st = row.get('street', '')
    no = row.get('house_number', '')

    # 1882 Commercial Road 9: Jones J. | Andrews, drapr
    if yr == '1882' and 'Commercial Road' in st and no == '9' and 'Andrews' in tr:
        row['surname'] = 'Jones'
        row['forename'] = 'J. Andrews'
        row['trade'] = 'Draper'
        return True

    # 1886 Commercial Road 9: Jones J. | Andrews, drapr
    if yr == '1886' and 'Commercial Road' in st and no == '9' and 'Andrews' in tr:
        row['surname'] = 'Jones'
        row['forename'] = 'J. Andrews'
        row['trade'] = 'Draper'
        return True

    # 1900 Commercial Street 158: Jones J. | Andrews, drapr
    if yr == '1900' and 'Commercial Street' in st and no == '158' and 'Andrews' in tr:
        row['surname'] = 'Jones'
        row['forename'] = 'J. Andrews'
        row['trade'] = 'Draper'
        return True

    # 1887 Commercial Road 46: Wm. | Welcome Home | Llewellyn, min. water mnf.
    if yr == '1887' and 'Commercial Road' in st and no == '46' and 'Llewellyn' in tr:
        row['surname'] = 'Llewellyn'
        row['forename'] = 'Wm.'
        row['building_name'] = 'Welcome Home'
        row['trade'] = 'Mineral Water Manufacturer'
        return True

    # 1890 Tunnel Terrace 14: L. | Lockyear, photographr
    if yr == '1890' and 'Tunnel' in st and no == '14' and 'Lockyear' in tr:
        row['surname'] = 'Lockyear'
        row['forename'] = 'L.'
        row['trade'] = 'Photographer'
        return True

    # 1895 Dolphin Street 75: Mayne -, boarding ho.
    if yr == '1895' and 'Dolphin' in st and no == '75' and 'Mayne' in tr:
        row['surname'] = 'Mayne'
        row['forename'] = ''
        row['trade'] = 'Boarding House'
        return True

    # 1898 Clarence Place 12: C | M. | Bartlett, photogrphr
    if yr == '1898' and 'Clarence' in st and no == '12' and 'Bartlett' in tr:
        row['surname'] = 'Bartlett'
        row['forename'] = 'C. M.'
        row['trade'] = 'Photographer'
        return True

    # 1898 Commercial Street 157: W. | Wesley Hairdr'sing Sal'n WESLEY CHAMBERS | Moseley, proptr
    if yr == '1898' and 'Commercial Street' in st and no == '157' and 'Moseley' in tr:
        row['surname'] = 'Moseley'
        row['forename'] = 'W.'
        row['building_name'] = 'Wesley Chambers'
        row['trade'] = 'Proprietor, Wesley Hairdressing Saloon'
        return True

    # 1899 Commercial Street 107: Abbott & | ironmngrs., Baker
    if yr == '1899' and 'Commercial Street' in st and no == '107' and 'Baker' in tr:
        row['surname'] = 'Abbott & Baker'
        row['forename'] = ''
        row['trade'] = 'Ironmongers'
        return True

    # 1901 Commercial Street 107: Abbott & Baker, ironmngrs
    if yr == '1901' and 'Commercial Street' in st and no == '107' and 'Abbott & Baker' in tr:
        row['surname'] = 'Abbott & Baker'
        row['forename'] = ''
        row['trade'] = 'Ironmongers'
        return True

    # 1901 Corporation Road: Binning Wm. | drapr, Thalaba h
    if yr == '1901' and 'Corporation' in st and 'Thalaba' in tr:
        row['surname'] = 'Binning'
        row['forename'] = 'Wm.'
        row['building_name'] = 'Thalaba House'
        row['trade'] = 'Draper'
        return True

    # 1902 High Street: W. H. | EMLYN CHAMBERS | Stephens, photogr'pr
    if yr == '1902' and 'High Street' in st and 'Stephens' in tr:
        row['surname'] = 'Stephens'
        row['forename'] = 'W. H.'
        row['building_name'] = 'Emlyn Chambers'
        row['trade'] = 'Photographer'
        return True

    # 1906 High Street: W. | Emlyn Chambers | Stephens, photogr'pr
    if yr == '1906' and 'High Street' in st and 'Stephens' in tr:
        row['surname'] = 'Stephens'
        row['forename'] = 'W.'
        row['building_name'] = 'Emlyn Chambers'
        row['trade'] = 'Photographer'
        return True

    # 1910 Commercial Street 7 & 8: Ltd. | W. A. & Co. | Baker, ironmerchts., ironmngrs.
    if yr == '1910' and 'Commercial Street' in st and ('7' in no or '8' in no) and 'Baker' in tr:
        row['surname'] = 'Baker'
        row['forename'] = 'W. A. & Co. Ltd.'
        row['trade'] = 'Iron Merchants & Ironmongers'
        return True

    # 1910 Dock-street 126: boarding ho, E., Seranno
    if yr == '1910' and 'Dock' in st and no == '126' and 'Seranno' in tr:
        row['surname'] = 'Seranno'
        row['forename'] = 'E.'
        row['trade'] = 'Boarding House'
        return True

    # 1920 Market Arcade: Dura, photographer
    if yr == '1920' and 'Market Arcade' in st and 'Dura' in tr:
        row['surname'] = 'Dura'
        row['forename'] = ''
        row['trade'] = 'Photographer'
        return True

    # 1878 Grenville Street: Thomas junr | Richards, coal and pitwood mrcht
    if yr == '1878' and 'Grenville' in st and 'Richards' in tr:
        row['surname'] = 'Richards'
        row['forename'] = 'Thomas junr.'
        row['trade'] = 'Coal & Pitwood Merchant'
        return True

    # 1882 Grenville Street: Thomas junr. | Richards, coal and pitwood mcht
    if yr == '1882' and 'Grenville' in st and 'Richards' in tr:
        row['surname'] = 'Richards'
        row['forename'] = 'Thomas junr.'
        row['trade'] = 'Coal & Pitwood Merchant'
        return True

    # 1908 Chepstow Road 162: Dunstan | H. G. coal mrcht, 82 Greenland Misses M. & S. fancy goods dealers
    if yr == '1908' and 'Chepstow' in st and no == '162' and 'Dunstan' in row.get('surname', ''):
        row['surname'] = 'Dunstan'
        row['forename'] = 'H. G.'
        row['trade'] = 'Coal Merchant'
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
        handle_trapped_names_batch2(r)

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
