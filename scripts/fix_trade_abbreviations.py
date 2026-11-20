#!/usr/bin/env python3
"""Expand abbreviated/OCR trade strings in data.csv and volume_csvs/."""

import csv
import re
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
    (re.compile(r"\bB\.?\s*&\s*M\.?\s*R\.?(?=\b|\s|$)", re.I), "Brecon & Merthyr Railway"),
]

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


def fix_trade(trade: str) -> str:
    t = trade
    for pat, rep in REPLACEMENTS:
        t = pat.sub(rep, t)
    return t


def process_csv(path: Path) -> int:
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
    total = process_csv(DATA_CSV)
    print(f"Updated {total} rows in {DATA_CSV.name}.")

    for vol_csv in sorted(VOL_DIR.glob("*_cleaned.csv")):
        vc = process_csv(vol_csv)
        if vc:
            print(f"Updated {vc} rows in {vol_csv.name}.")


if __name__ == "__main__":
    main()
