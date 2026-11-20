# Stratified Random Scan Accuracy Audit (`1878–1971`)

- **Date:** 2026-11-13
- **Sample:** 50 records drawn with `scripts/random_scan_audit.py` (`seed=42`) stratified across 4 eras:
  - `1878–1895`: 12 records
  - `1898–1913`: 13 records
  - `1915–1936`: 15 records
  - `1971`: 10 records
- **Verifiable records:** **49 / 50** (1 record, `#26` `1925 Caerau Crescent`, could not be verified because pages `395–399` are absent between `IMG_8357.jpeg` p.394 and `IMG_8358.jpeg` p.400 in `original_scans/Johns Directory 1925/`).

---

## Summary Scorecard

| Scope | Verifiable | Exact Match | Minor Variant / Parse Quirk | Substantively Right | Field / Record Error | Street / Boundary Error |
|---|---:|---:|---:|---:|---:|---:|
| `1878–1895` | 12 | 11 (91.7%) | 0 (0.0%) | **11 (91.7%)** | 1 (8.3%) | 0 (0.0%) |
| `1898–1913` | 13 | 11 (84.6%) | 1 (7.7%) | **12 (92.3%)** | 1 (7.7%) | 0 (0.0%) |
| `1915–1936` | 14 | 11 (78.6%) | 2 (14.3%) | **13 (92.9%)** | 1 (7.1%) | 0 (0.0%) |
| **Pre-1971 Subtotal (`1878–1936`)** | **39** | **33 (84.6%)** | **3 (7.7%)** | **36 (92.3%)** | **3 (7.7%)** | **0 (0.0%)** |
| `1971` | 10 | 6 (60.0%) | 0 (0.0%) | **6 (60.0%)** | 4 (40.0%) | 0 (0.0%) |
| **Overall (`1878–1971`)** | **49** | **39 (79.6%)** | **3 (6.1%)** | **42 (85.7%)** | **7 (14.3%)** | **0 (0.0%)** |

---

## Key Takeaways

1. **Zero street/boundary errors** across all 49 verified records (`0 / 49`).
2. **Pre-1971 (`1878–1936`) is very solid (`92.3%` substantively right, `84.6%` exact).** The 3 errors found were isolated field-level issues (`#11` missing trade, `#17` wrong resident at `1898 Jeddo St 35`, `#30` misparsed `1927 Caerleon Rd 83`).
3. **`1971` has a much higher parse-error rate (`4 / 10`),** driven by two systematic patterns that are easy to sweep globally across `1971`:
   - **Blank/unoccupied house numbers** (`#43` `110`, `#49` `18`) parsed into `forename` instead of `house_number`.
   - **Wrapped continuation lines** (`#46` `fruirs` from `1a, Bryant Fruit Store, fruiterers`) becoming standalone rows.

---

## Full Sample Log

| # | Era | Year | Street | `data.csv` Entry | Verified Scan | Grade | Notes |
|---:|---|---:|---|---|---|---|---|
| 01 | 1878–1895 | 1886 | Lower Cross Street | `11` \| `William Taylor` \| `Labourer` | `Johns Directory 1886/IMG_0215.jpeg` | Exact Match | `11 Taylor Wm. labourer` |
| 02 | 1878–1895 | 1878 | Old Green | `1` `King's Head Tap` \| `Samuel Fry` | `Johns Directory 1878/IMG_4883.jpeg` | Exact Match | `1 Fry Saml., Kings Head tap` |
| 03 | 1878–1895 | 1892 | Chepstow Road | `Richmond Villa` \| `Void` | `Johns Directory 1892/IMG_1004.jpeg` | Exact Match | `Richmond villa—void` |
| 04 | 1878–1895 | 1890 | Power Street | `69` \| `Sidney Hoskins` \| `Eng. D'Vr` | `Johns Directory 1890/IMG_6370.jpeg` | Exact Match | `69 Hoskins Sidney, eng. d'vr` |
| 05 | 1878–1895 | 1890 | Durham Road | `39` \| `William Veal` \| `Compositor` | `Johns Directory 1890/IMG_6348.jpeg` | Exact Match | `39 Veal Wm. compositor` |
| 06 | 1878–1895 | 1887 | Albert Terrace | `22` \| `Thomas Edwards` \| `Guard` | `Johns Directory 1887/IMG_6388.jpeg` | Exact Match | `22 Edwards Thos. guard` |
| 07 | 1878–1895 | 1886 | East Usk Road | `2` \| `William White` \| `Labourer` | `Johns Directory 1886/IMG_0206.jpeg` | Exact Match | `2 White Wm. labourer` |
| 08 | 1878–1895 | 1895 | Oxford Street | `18` \| `William Merryfield` \| `Carpenter` | `Johns Directory 1895/IMG_1150.jpeg` | Exact Match | `18 Merryfield Wm. carpenter` |
| 09 | 1878–1895 | 1886 | Canal Parade | `32` \| `Horatio Redmore` \| `Wtchmn` | `Johns Directory 1886/IMG_0188.jpeg` | Exact Match | `32 Redmore Hora. wtchmn` |
| 10 | 1878–1895 | 1894 | Canal Street | `2` \| `William James` \| `Carpenter` | `Johns Directory 1894/IMG_6538.jpeg` | Exact Match | `2 James William carpenter` |
| 11 | 1878–1895 | 1878 | Union Street | `9` \| `James Abbott` \| *(blank)* | `Johns Directory 1878/IMG_4889.jpeg` | **Field Error** | Scan has `9 Abbott James, labourer`; trade missing |
| 12 | 1878–1895 | 1878 | Station Street | `22` \| `L. Thomas` \| `Boys' School` | `Johns Directory 1878/IMG_4887.jpeg` | Exact Match | `22 Thomas L. boys' school` |
| 13 | 1898–1913 | 1900 | Arcades | `The. FENNELL'S Arcade Chambers` \| `- Frank Lewis` \| `Solicitor` | `Johns Directory 1900/IMG_8490.jpeg` | Minor Quirk | Header text concatenated into `building_name`; leading `- ` on `forename` |
| 14 | 1898–1913 | 1902 | Locke Street | `21` \| `Thomas Evans` \| `Cabinetmaker` | `Johns Directory 1902/IMG_6778.jpeg` | Exact Match | `21 Evans Thos. cabinetmakr` |
| 15 | 1898–1913 | 1902 | Victoria Place | `47` \| `G. Fuller` \| `Boot Repairer` | `Johns Directory 1902/IMG_6809.jpeg` | Exact Match | `47 Fuller G. boot repairer` |
| 16 | 1898–1913 | 1906 | Jones Street | `19` \| `George S. Parry` \| `Baker` | `Johns Directory 1906/IMG_2002.jpeg` | Exact Match | `19 Parry George S. baker` |
| 17 | 1898–1913 | 1898 | Jeddo Street | `35` \| `John Clarke` \| `Labourer` | `Johns Directory 1898/IMG_6863.jpeg` | **Record Error** | Scan shows `35 Brown Charles, rigger` |
| 18 | 1898–1913 | 1902 | Christchurch Road | `Charles Jenkins` \| `Roller` | `Johns Directory 1902/IMG_6735.jpeg` | Exact Match | `Jenkins Charles, roller` |
| 19 | 1898–1913 | 1908 | Bedford Road | `53` \| `Daniel Bowen` \| `Tailor` | `Johns Directory 1908/IMG_2059.jpeg` | Exact Match | `53 Bowen Daniel, tailor` |
| 20 | 1898–1913 | 1902 | Manchester Street | `26` \| `Albert Kerrell` \| `Dock Labourer` | `Johns Directory 1902/IMG_6781.jpeg` | Exact Match | `26 Kerrell Albert, dock labr` |
| 21 | 1898–1913 | 1908 | Lewis Street | `28` \| `William Davies` \| `Timekeeper` | `Johns Directory 1908/IMG_2127.jpeg` | Exact Match | `28 Davies Wm. timekeeper` |
| 22 | 1898–1913 | 1903 | Rose Street | `9` \| `Arthur G. Taylor` \| `Carpenter` | `Johns Directory 1903/IMG_7001.jpeg` | Exact Match | `9 Taylor Arthur G. carpentr` |
| 23 | 1898–1913 | 1898 | Brynderwen Road | `5 Pen-y-Dre` | `Johns Directory 1898/IMG_6829.jpeg` | Exact Match | `5 Pen-y-dre` |
| 24 | 1898–1913 | 1901 | Ebenezer Terrace | `Welsh Calvinistic Meth. (Ebenezer) Chapel (1829)` | `Johns Directory 1901/IMG_8633.jpeg` | Exact Match | `WELSH CALVINISTIC METH. (EBENEZER) CHAPEL (1829)` |
| 25 | 1898–1913 | 1908 | Caerau Road | `76 Ashley Villa` \| `W. L. Smith` | `Johns Directory 1908/IMG_2065.jpeg` | Exact Match | `76 Smith W. L., Ashley villa` |
| 26 | 1915–1936 | 1925 | Caerau Crescent | `William Baxter George` | *(p.395–399 missing)* | Scan Missing | Pages 395–399 absent between `IMG_8357` (394) & `IMG_8358` (400) |
| 27 | 1915–1936 | 1915 | Mendalgief Road | `98` \| `William Vodden` \| `Labourer` | `Johns Directory 1915/IMG_0342.jpeg` | Exact Match | `98 Vodden Wm. labourer` |
| 28 | 1915–1936 | 1936 | Somerset Road | `5` \| `Miss Mabel Ebdon` | `Johns Directory 1936/IMG_4765.jpeg` | Minor Variant | Scan has `5 Ebdon Mrs. Mabel` (`Miss` vs `Mrs.`) |
| 29 | 1915–1936 | 1915 | Chepstow Road | `89` \| `George Giddings` \| `Painter` | `Johns Directory 1915/IMG_0282.jpeg` | Exact Match | `89 Giddings Geo. painter, etc.` |
| 30 | 1915–1936 | 1927 | Caerleon Road | `house_number=Edith May` \| `forename=matron` | `Johns Directory 1927/IMG_4445.jpeg` | **Field Error** | Scan has `83 Board of Guardians' Children's Homes—Bailey, Edith May, matron` |
| 31 | 1915–1936 | 1925 | Bridge Street | `Midland Bank Chambers` \| `Albert Dunn` \| `Caretaker` | `Johns Directory 1925/IMG_8355.jpeg` | Exact Match | `MIDLAND BANK CHAMBERS` ... `Dunn Albert, caretaker` |
| 32 | 1915–1936 | 1936 | Llewellyn Street | `19` \| `Eli Dean` \| `Engine Driver` | `Johns Directory 1936/IMG_4754.jpeg` | Exact Match | `19 Dean Eli, engine driver` |
| 33 | 1915–1936 | 1936 | High Street | `Winchester Chambers—` \| `trade=Akers H. engraver` | `Johns Directory 1936/IMG_4703.jpeg` | Minor Quirk | Content matches `WINCHESTER CHAMBERS— Akers H., engraver`, shifted into `trade` |
| 34 | 1915–1936 | 1925 | East Usk Road | `22` \| `Edward Jones` \| `Labourer` | `Johns Directory 1925/IMG_8398.jpeg` | Exact Match | `22 Jones Edward, labourer` |
| 35 | 1915–1936 | 1936 | Jeddo Street | `59` \| `Robert Gwyer` \| `Pilotsman` | `Johns Directory 1936/IMG_4706.jpeg` | Exact Match | `59 Gwyer Robert, pilotsman` |
| 36 | 1915–1936 | 1925 | Commercial Road | `157 Hunters Tea Stores` | `Johns Directory 1925/IMG_8377.jpeg` | Exact Match | `157 Hunters Tea Stores` |
| 37 | 1915–1936 | 1927 | Marlborough Road | `10` \| `Godfrey A. Avery` \| `Mechc` | `Johns Directory 1927/IMG_4538.jpeg` | Exact Match | `10 Avery Godfrey A., mechc` |
| 38 | 1915–1936 | 1925 | Capel Crescent | `62` \| `Mrs. Martha Williams` | `Johns Directory 1925/IMG_8362.jpeg` | Exact Match | `62 Williams Mrs. Martha` |
| 39 | 1915–1936 | 1924 | Alma Street | `43` \| `William Phillips` \| `Guard` | `Johns Directory 1924/IMG_0732.jpeg` | Exact Match | `43 Phillips Wm. guard` |
| 40 | 1915–1936 | 1915 | King Street | `47` \| `E. A. Manning` \| `Painter` | `Johns Directory 1915/IMG_0330.jpeg` | Exact Match | `47 Manning E. A. painter` |
| 41 | 1971 | 1971 | Beatty Road | `68` \| `C. A Manley` | `Johns Directory 1971/IMG_6091.jpeg` | Exact Match | `68 Manley C. A` |
| 42 | 1971 | 1971 | Raglan Street | `53` \| `Mrs. F Essery` | `Johns Directory 1971/IMG_6261.jpeg` | Exact Match | `53 Essery Mrs. F` |
| 43 | 1971 | 1971 | Thompson Avenue | `forename=110` | `Johns Directory 1971/IMG_6294.jpeg` | **Field Error** | Blank/unoccupied `110` on scan parsed into `forename` |
| 44 | 1971 | 1971 | Cherwell Walk | `21` \| `Alfd Pring` | `Johns Directory 1971/IMG_6125.jpeg` | Exact Match | `21 Pring Alfd` |
| 45 | 1971 | 1971 | Masefield Vale | *(no number)* \| `Ivor G Davies` | `Johns Directory 1971/IMG_6230.jpeg` | **Field Error** | Scan has `9 Davies Ivor G`; missing `house_number` |
| 46 | 1971 | 1971 | Brynglas Road | `forename=fruirs` | `Johns Directory 1971/IMG_6105.jpeg` | **Field Error** | Wrapped `fruitrs` from `1a, Bryant Fruit Store, fruiterers` became a standalone row |
| 47 | 1971 | 1971 | Vancouver Drive | `48` \| `Irene Snow` | `Johns Directory 1971/IMG_6299.jpeg` | Exact Match | `48 Snow Irene` |
| 48 | 1971 | 1971 | Hollybush Avenue | `27` \| `Emrys Davies` | `Johns Directory 1971/IMG_6198.jpeg` | Exact Match | `27 Davies Emrys` |
| 49 | 1971 | 1971 | Malcolm Sargent Close | `forename=18` | `Johns Directory 1971/IMG_6223.jpeg` | **Field Error** | Blank/unoccupied `18` on scan parsed into `forename` |
| 50 | 1971 | 1971 | Windsor Terrace | `11` \| `Cyril W Clark` | `Johns Directory 1971/IMG_6310.jpeg` | Exact Match | `11 Clark Cyril W` |
