#!/usr/bin/env python3
"""
fix_1925_screenshot_anomalies.py
Directly repairs the legacy OCR column-drift rows in 1925 highlighted in the user's screenshot.
"""

import csv
import re

DATA_CSV = "data.csv"

def run():
    print(f"Reading {DATA_CSV} to fix 1925 anomalies...")
    rows = []
    fieldnames = []
    with open(DATA_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            rows.append(r)

    repaired = 0
    for r in rows:
        if r["year"] != "1925":
            continue

        st = r["street"]
        hn = r["house_number"]
        sn = r["surname"]
        fn = r["forename"]
        tr = r["trade"]
        bldg = r["building_name"]

        # 1. Commercial Road #168
        if "Commercial Road" in st and hn == "168" and "news-agent" in fn:
            r["forename"] = "Herb. E."
            r["surname"] = "Griffiths"
            r["trade"] = "News-agent & Wholesale/Retail Tobacconist"
            repaired += 1

        # 2. Alma Street #110
        elif "Alma Street" in st and hn == "110" and "Fitter" in fn:
            r["forename"] = "James"
            r["surname"] = "Gibbs"
            r["trade"] = "Fitter's Helper"
            repaired += 1

        # 3. Bridge Street estate agent
        elif "Bridge Street" in st and "estate agent" in fn.lower():
            r["building_name"] = "Estate Agent House & Auctioneers"
            r["forename"] = ""
            r["surname"] = ""
            r["trade"] = "Estate Agent & Auctioneer"
            repaired += 1

        # 4. Commercial Street Consular Agent
        elif "Commercial Street" in st and "Consular Agent" in fn:
            r["building_name"] = "Italian Consulate"
            r["forename"] = "Salvatore"
            r["surname"] = "Guiffrida"
            r["trade"] = "Italian Consular Agent"
            repaired += 1

        # 5. New Road #22 Evans butcher
        elif "New Road" in st and "butcher" in fn.lower():
            r["forename"] = "Mrs"
            r["surname"] = "Evans"
            r["trade"] = "Butcher"
            repaired += 1

        # 6. Church Road Town Clerk's office
        elif "Church Road" in st and "Treharne" in fn:
            r["building_name"] = "Town Clerk's Office"
            r["forename"] = "O. Treharne"
            r["surname"] = "Morgan"
            r["trade"] = "Town Clerk"
            repaired += 1

        # 7. Church Road Justices Clerk's office
        elif "Church Road" in st and "Clerk's office" in fn:
            r["building_name"] = "Justices' Clerk's Office"
            r["forename"] = ""
            r["surname"] = ""
            r["trade"] = "Justices' Clerk"
            repaired += 1

        # 8. Church Street confectioner
        elif "Church Street" in st and fn.lower().startswith("confectioner"):
            r["forename"] = "M. E."
            r["surname"] = ""
            r["trade"] = "Confectioner"
            repaired += 1

        # 9. Coldra Road #14 timekeeper
        elif "Coldra Road" in st and "timekeeper" in fn.lower():
            r["forename"] = "Harry"
            r["surname"] = "Rees"
            r["trade"] = "Timekeeper"
            repaired += 1

        # 10. Crindau Road #6 gasfitter
        elif "Crindau Road" in st and "gasfitter" in fn.lower():
            r["forename"] = "W."
            r["surname"] = "Taylor"
            r["trade"] = "Gasfitter"
            repaired += 1

        # 11. Dock Street Sunclad factory
        elif "Dock Street" in st and "Sunclad" in fn:
            r["building_name"] = "Sunclad Factory"
            r["forename"] = ""
            r["surname"] = "South Wales Tobacco Co. (1913) Ltd"
            r["trade"] = "Tobacco Manufacturers"
            repaired += 1

        # 12. Bryngwyn Road Nurse
        elif "Bryngwyn Road" in st and "nurse" in fn.lower():
            r["building_name"] = ""
            r["forename"] = ""
            r["surname"] = "Cer"
            r["trade"] = "Nurse"
            repaired += 1

        # 13. General pattern: "W. Gasfitter Taylor" or "timekeeper Rees"
        elif "timekeeper" in fn.lower():
            r["trade"] = "Timekeeper"
            r["forename"] = re.sub(r'timekeeper\s*\d*', '', fn, flags=re.I).strip()
            repaired += 1

        elif "gasfitter" in fn.lower():
            r["trade"] = "Gasfitter"
            r["forename"] = re.sub(r'gasfitter', '', fn, flags=re.I).strip()
            repaired += 1

    print(f"Repaired {repaired} anomaly records in 1925!")

    with open(DATA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    run()
