# 📋 Newport Street Audit — Master Action Register

This document tracks all historical street audit findings, required database merges, resident-bleed corrections, and OCR cleanups identified during reference book checks (*Current Newport Streets* & *Lost Newport Streets*).

*Last updated: 2026-10-12*  
*Total Master Streets in Registry: 1,583*  
*Verified & Locked: 922*

---

## 0. Resolved & Deployed Fixes (Archive Cleaned)

| Issue | Original Slug | Year(s) | Records | Resolution Applied |
| :--- | :--- | :--- | :--- | :--- |
| **Wallace Street** | `wallace-street` | 1900–1903 | 73 | Earlier spelling variant of verified **Wallis Street** (Castle St to King's Parade / Town Dock). Occupants (O'Shea, McCarthy) match. Merged. |
| **Webley Rd** | `webley-rd` | 1886 | 14 | Parsing artifact. Resident Richard M. Webley reassigned to **Baldwin Street**, narrative text purged, and Nos. 20–28 & Queen's Hotel reassigned to **Baneswell Road**. |
| **Wellington Rd** | `wellington-rd` | 1902 | 23 | Abbreviation variant merged into verified canonical **Wellington Road**. |
| **White** | `white` | 1925 | 6 | Clipped header merged into verified canonical **White Lion Court** (James Edwards No. 1, Frederick Edmonds No. 2 match 1927). |
| **William Street** | `william-street` | 1920 | 4 | Dropped 's' merged into verified canonical **Williams Street** (Pugsley No. 41, Bird No. 42 match 1925). |
| **Woodland** | `woodland` | 1920 | 14 | Dropped 'Road' merged into canonical **Woodland Road** (John E. Southall No. 5, Walter J. Redshaw No. 1 match Woodland Road). |
| **Woodland Park** | `woodland-park` | 1886–1925 | 36 | Early Victorian estate road name merged into canonical **Woodland Park Road** (*Methven* - T.B.R. Wilson, *Rougemont* - A.H. Tapson match Woodland Park Road). |
| **Worden Road** | `worden-road` | 1936 | 81 | OCR misread 'M' as 'W'. Reassigned all 81 records (Alex M. Martin at No. 1a *Morden House*, Wm Morris at No. 1 *The Glynn*, Ethel Morris at No. 13 *Llandogo House*) to canonical **Morden Road**. |
| **Phillips Street** | `phillips-street` | 1899, 1902, 1903, 1920 | 112 | Spelling variant merged into verified canonical **Phillip Street**. |
| **Princes Street** | `princes-street` | 1886 | 15 | Plural variant merged into verified canonical **Prince Street**. |
| **Penney Crescent** | `penney-crescent` | 1971 | 72 | Normalized to verified canonical **Penny Crescent**. |
| **Penylan Road** | `penylan-road` | Multi | 216 | Normalized to verified Welsh canonical **Pen-y-lan Road**. |
| **Allen Septimus, Mount view** | `allen-septimus-mount-view` | 1902 | 30 | Resident bleed: Septimus Allen at Mount View. Odd numbered villas Nos. 27–79 (Hillcrest, Brynhyfryd, Glenholme, etc.) reassigned to **Llanthewy Road**. |
| **Anssesy Road** | `anssesy-road` | 1971 | 23 | OCR misread ('ne' as 'ss'). Reassigned Nos. 1–22 (Walton & Son, Malmloff, Bulley) to canonical **Annesley Road**. |
| **Beattie George** | `beattie-george` | 1971 | 41 | Ad header bleed (*George Beattie, coal & coke merchant*). Split & reassigned: 15 properties (Nos. 33–37, 75–78, Glencairn, Clyro Villa) to **Caerau Road**; 26 properties (Nos. 1–15, 38–50) to **Caerleon Road**. |
| **Bolt Road** | `bolt-road` | 1913 | 11 | Typesetter abbreviation/truncation. Properties (Nos. 1–3: Prosser, Hutchins, Newton) reassigned to canonical **Bolton Road**. |
| **Bristol St** | `bristol-st` | 1886 | 2 | Abbreviation expanded to canonical **Bristol Street**. |
| **Broadwell Gardens / Brodawel Gardens** | `broadwell-gardens` / `brodawel-gardens` | 1890–1910 | 225 | Spelling variants merged into canonical **Brodawell Gardens** (Nos. 1–62 verified). |
| **Metro. Bank Chambers** | `metro-bank-chambers` | 1902 | 60 | Merged into canonical **Metropolitan Bank Chambers**. |
| **Newport House** | `newport-house` | 1971 | 68 | Commercial block at Nos. 48–51 Commercial Street (Eastern Carpet Stores, John Hall Tools, etc.). Reassigned to **Commercial Street**. |
| **Llanvair Road** | `llanfair-road` | 1925 | 55 | Welsh/English orthography normalized to canonical **Llanvair Road**. |
| **Public Park** | `public-park` | 1902, 1903 | 46 | Park Square park entrance heading bleed. Reassigned all 46 properties (Moon, Peters, etc.) to **Park Square**. |
| **Rivers de** | `rivers-de` | 1927 | 45 | Truncation of *Riverside-continued*. Reassigned all 45 properties to **Riverside**. |
| **Rev DD. rd** | `rev-dd-rd` | 1903 | 42 | Header bleed from *Rev. D. D. Morgan* living at No. 4 Coldra Road. Reassigned to **Coldra Road** and **Clytha Park Road**. |
| **Court** | `court` | 1886 | 29 | Truncation of internal courtyards *Court A*, *Court B*, *Court D* on Charles Street. Reassigned 29 households to **Charles Street**. |
| **Moreland Avenue** | `moreland-avenue` | 1936 | 25 | Typo merged into canonical **Moorland Avenue**. |
| **Maple Crescent (1913)** | `maple-crescent` | 1913 | 21 | Typesetter omitted *Marion Street* header. Reassigned Nos. 1–9 (Redman, Berry, Manning, Gould, Sullivan) to authentic **Marion Street**. |
| **Mellon Square** | `mellon-square` | 1893, 1898, 1899 | 90 | Normalized to canonical **Mellon's Square**. |
| **House** | `house` | 1927 | 18 | Split from *TREDEGAR HALL PICTURE HOUSE* on Stow Hill. Reassigned all 18 records (Constitutional Club, Caerleon Chambers) to **Stow Hill**. |
| **Morgan A** | `morgan-a` | 1898 | 18 | Header bleed from contractor *A. S. Morgan* at *Port View*, Fields Road. Reassigned all 18 villas to **Fields Road**. |
| **Jeffreys Street** | `jeffreys-street` | 1898, 1899, 1902 | 16 | Extra 's' OCR variant merged into canonical **Jeffrey Street**. |
| **Lloyd Road** | `lloyd-road` | 1971 | 15 | OCR corruption of Welsh *Llwynderi Road* ("From 42 Oakfield road to Edward VII avenue"). Reassigned to **Llwynderi Road**. |
| **Millman Street** | `millman-street` | 1898 | 12 | Double 'l' spelling variant merged into canonical **Milman Street**. |
| **Kingsm** | `kingsm` | 1927 | 10 | Truncation of *Kingsmill Terrace*. Reassigned to **Kingsmill Terrace**. |
| **L.d.s.r.c** | `l-d-s-r-c` | 1971 | 6 | Split from dentist title *L.D.S.R.C.S.* at Victoria Chambers. Reassigned to **Clytha Park Road**. |
| **M.r.s** | `m-r-s` | 1971 | 20 | Split from optician title *M.R.S.H.* at No. 3 Baneswell Road. Reassigned to **Baneswell Road**. |
| **Key's Buildings** | `key-s-buildings` | 1902 | 4 | Merged into canonical **Keyse's Buildings**. |
| **Llanvellay Road** | `llanvellay-road` | 1925 | 4 | OCR corruption of 'p' as 'll'. Canonical historical thoroughfare off Constance Street is **Llanvapley Road**. |
| **Mrs Titus, Oak view** | `mrs-titus-oak-view` | 1902 | 1 | Resident Mrs. Titus Lewis at No. 45 *Oak View*, Gibbs Road. Reassigned to **Gibbs Road**. |
| **Dewstreet Street** | `dewstreet-street` | 1913 | 107 | OCR typo and header bleed resolved. The heading *DEWSTREET STREET (Off Corporation-road)* was a misreading of **Dewstow Street** (Nos. 1–87 odd, 80–2 even: 84 records reassigned to **Dewstow Street**). Line 6947 bled into *DEW DEWSLAND PARK ROAD* (23 villa records Nos. 2–42 even reassigned to **Dewsland Park Road**). Pseudo-street purged. |
| **Barnardtown** | `barnardtown` | 1887, 1893, 1894, 1898, 1927 | 192 | Disentangled & purged. Barnardtown was an area description, not a street. All 192 properties redistributed across source streets: 1887 $\rightarrow$ Baneswell Road (Bank Chambers); 1893 $\rightarrow$ Queen's Buildings (9, 11, 12) & Barnard Street (1–21); 1894 $\rightarrow$ Barrack Hill; 1898 $\rightarrow$ Barnard Street (1–7) & Barrack Hill (28–36, 100–134); 1927 $\rightarrow$ Church Road (Maindee) & Church Street (Pillgwenlly). |
| **A. H. St** | `a-h-st` | 1903 | 5 | Root-cause fixed in `parse_1903.py`. Generated by resident line `Duffield | A. H. St. | John's h`. Residents and Talbot Inn reunited on `St. Mary Street`. |
| **Virgin Street** | `virgin-street` | 1903 | 118 | Header bleed from *CHURCH OF ST. MARY THE VIRGIN* on Corporation Road. Reassigned all 118 properties (Nos. 199–280+, Salisbury Constitutional Club) to **Corporation Road**. |
| **Capet Street** | `capet-street` | 1971 | 143 | OCR typo ('t' for 'l'). Reassigned 143 properties to canonical **Capel Street**. |
| **Clevedon** | `clevedon` | 1920 | 23 | Confirmed from raw scan (1920 line 20071 `CLEVEDON TERRACE.-`). Reassigned to **Clevedon Terrace**. |
| **Wesleyan Miss'N Chapel** | `wesleyan-miss-n-chapel` | 1900 | 32 | Parser split at chapel header. Reassigned all 32 properties (Nos. 1–68, Mylan, Thomas, etc.) to **Price Street**. |
| **Victoria Ivor Place** | `victoria-ivor-place` | 1886 | 32 | Sub-terrace bleed on Victoria Avenue. Reassigned all 32 properties to **Victoria Avenue**. |
| **Clifford Crescent** | `clifford-crescent` | 1886, 1920 | 32 | Normalized spelling to canonical **Clyffard Crescent**. |
| **Barrak Hill** | `barrak-hill` | 1886 | 27 | Merged into **Barrack Hill**. |
| **Cambrian cottages** | `cambrian-cottages` | 1886 | 36 | Merged into **Cambria Cottages**. |
| **for Old Dock** | `for-old-dock` | 1903 | 17 | Text bleed from *agent and collector for Old Dock*. Reassigned all 17 businesses (Caledonian Hotel, consulates, Lloyd's agency, Richmond Hotel) to **Dock Street**. |
| **pool Road** | `pool-road` | 1886 | 11 | Line split on *From Chepstow-rd. to Duck-pool road*. Reassigned 11 houses to **Fair Oak Terrace**. |
| **Vue Court** | `vue-court` | 1903 | 15 | OCR split on Rev. Wrenford's house *Belle Vue court*. Reassigned all 15 records (Hospital, Dr Paton) to **Cardiff Road**. |
| **Shaftsbury Park** | `shaftsbury-park` | 1920 | 10 | Return header *SHAFTSBURY PARK (cross and return)* on Evans Street. Reassigned 10 houses (even numbers 4–20) to **Evans Street**. |
| **St. James Street** | `st-james-street` | 1920 | 7 | Header bleed from *ST. JAMES' CHURCH* on Commercial Street. Reassigned all 7 records (Town Hall, Friars Chambers, Tabernacle) to **Commercial Street**. |
| **Cenfed Street** | `cenfed-street` | 1927 | 6 | Merged into **Cenfedd Street**. |
| **Gymnasium** | `gymnasium` | 1927 | 5 | Header bleed from *BATHS AND GYMNASIUM*. Reassigned to **Stow Hill**. |
| **County Police Court** | `county-police-court` / `marshes-county-police-court` | 1902, 1903 | 7 | Header bleed on Queen's Hill. Reassigned to **Queen's Hill**. |
| **Brynderyn Road** | `brynderyn-road` | 1886 | 4 | Victorian spelling variant. Reassigned to **Brynderwen Road**. |
| **and Fairoak Avenue** | `and-fairoak-avenue` | 1902 | 4 | Cross-street line break on Duckpool Road. Reassigned 4 records (Edwin Turner, grocer, Barnard Town Post Office) to **Duckpool Road**. |
| **at Eastern Dry Docks** | `at-eastern-dry-docks` | 1902, 1903 | 3 | Sub-wharf reference. Reassigned to **The Wharves**. |
| **Circus** | `circus` | 1886 | 2 | Landmark bleed (*Fossett's Circus*). Reassigned to **Dock Street**. |
| **Carpenters' Arms** | `carpenters-arms` | 1971 | 2 | Merged into **Carpenter's Arms Lane**. |
| **Chesterfield** | `chesterfield` | 1913 | 1 | Merged into **Chesterfield Street**. |
| **Newport Savings' Bank** | `newport-savings-bank` | 1886 | 1 | Building header at No. 4 Stow Hill. Reassigned to **Stow Hill**. |
| **Victoria Street (1882)** | `victoria-street` | 1882 | 1 | Purged orphan cross-reference text (*Ley-street West-st., Blewitt*). |
| **Villa / Resident Bleeds** | Various | 1886, 1902, 1903 | 89 | Reassigned: *Bryant A. T., The Grove* $\rightarrow$ **Somerset Road**; *Davies Wm., Sea view* & *Francis Wm., South view* & *Parkes Wm., Fair view* $\rightarrow$ **Waterloo Road**; *Parfitt Stanley, Field view* $\rightarrow$ **Somerton Road**; *Smith W. A., Fair view* $\rightarrow$ **Caerau Road**; *Hill Henry, High view* $\rightarrow$ **Penylan Road**; *Summers Rev. J. F.* $\rightarrow$ **Clytha Park Road**. |
| **Earlier 14 Canonical Merges** | Various | Multi | 385 | Cleaned and merged: `Roberts Street` $\rightarrow$ `Robert Street`, `Mansell Street` $\rightarrow$ `Mansel Street`, `Manchester St` $\rightarrow$ `Manchester Street`, `Summerhill Av` $\rightarrow$ `Summerhill Avenue`, `Sterndale Road` $\rightarrow$ `Sterndale Bennett Road`, `Marshes` $\rightarrow$ `Marshes Road`, `Brynderwyn Road` $\rightarrow$ `Brynderwen Road`, `Shaffersbury Street` $\rightarrow$ `Shaftesbury Street`, `St. Mary St` $\rightarrow$ `St. Mary Street`, `Stow Park Park Circus` $\rightarrow$ `Stow Park Circus`, `Protheroes Row` $\rightarrow$ `Protheroe's Row`, `Corporation Rd` $\rightarrow$ `Corporation Road`, `Marshes-wyndham Terrace` $\rightarrow$ `Marshes Road`, `Hale Mrs, 1 Vine Place` $\rightarrow$ `Vine Place`. |

## 1. Confirmed Genuine Distinctions (DO NOT MERGE)

These streets have similar names but are confirmed to be separate, distinct historical thoroughfares:

| Street Name | Slug | Years / Records | Book Citation / Notes |
| :--- | :--- | :--- | :--- |
| **Albany Road** | `albany-road` | 1902 (40 recs) | Confirmed distinct from *Albany Street*. |
| **Albany Street** | `albany-street` | 1887–1971 (408 recs) | Primary commercial & residential arterial of Crindau Quarter. |

---

## 2. Street Merges & Canonical Name Unifications

These entries are OCR spelling variants or abbreviations of existing canonical streets and will be merged into their parent street:

| Current Entry | Merge Target (Canonical) | Years Affected | Record Count | Notes / Audit Reason |
| :--- | :--- | :--- | :--- | :--- |
| `mansell-street` | **Mansel Street** | 1920 | 23 | Single 'l' is the correct historical spelling. |
| `protheroes-row` | **Protheroe's Row** | 1878, 1886, 1898, 1902, 1903 | 61 | Add apostrophe canonicalization. |
| `corporation-rd` | **Corporation Road** | 1903 | 4 | Expand abbreviation. |
| `manchester-st` | **Manchester Street** | 1902, 1903 | 85 | Expand abbreviation. |
| `brynderwyn-road` | **Brynderwen Road** | 1902 | 14 | OCR vowel swap ('y' $\rightarrow$ 'e'). |
| `shaffersbury-street` | **Shaftesbury Street** | 1903 | 13 | OCR typo correction. |
| `marshes-wyndham-terrace` | **Marshes Road** | 1886 | 38 | Wyndham Terrace was an embedded mid-road terrace on Marshes Road. |
| `hale-mrs-1-vine-place` | **Vine Place** | 1902 | 17 | Header bleed combining resident name and street; reassign residents to Vine Place. |
| `roberts-street` | **Robert Street** | 1894 | 54 | OCR extra 's' on Robert Street. |
| `st-mary-st` | **St Mary Street** | 1903 | 64 | Expand abbreviation. |
| `stow-park-park-circus` | **Stow Park Circus** | 1927 | 10 | OCR duplicated word 'park'. |
| `summerhill-av` | **Summerhill Avenue** | 1971 | 87 | Expand abbreviation. |
| `sterndale-road` | **Sterndale Bennett Road** | 1971 | 32 | Full composer name on estate (Sterndale Bennett). |

---

## 3. Resident & Villa Bleeds (Person / House Name Misparsed as Street)

These entries contain resident names or private villa/house names that were mistakenly OCR-parsed as street headings. The residents and properties need to be reassigned to their actual parent street:

| Errant Street Name | Slug | Year(s) | Records | Sample Occupants / Clues |
| :--- | :--- | :--- | :--- | :--- |
| `bryant-a-t-the-grove` | `bryant-a-t-the-grove` | 1903 | 24 | Person name *A. T. Bryant*, villa *The Grove*. |
| `davies-wm-sea-view` | `davies-wm-sea-view` | 1903 | 2 | Person name *Wm Davies*, house *Sea View*. |
| `francis-wm-south-view` | `francis-wm-south-view` | 1903 | 1 | Person name *Wm Francis*, house *South View*. |
| `hill-henry-high-view` | `hill-henry-high-view` | 1902, 1903 | 14 | Person name *Henry Hill*, house *High View*. |
| `parfitt-stanley-s-field-view` | `parfitt-stanley-s-field-view` | 1903 | 6 | Person name *Stanley Parfitt*, house *Field View*. |
| `parkes-wm-fair-view` | `parkes-wm-fair-view` | 1903 | 24 | Person name *Wm Parkes*, house *Fair View*. |
| `smith-w-a-fair-view` | `smith-w-a-fair-view` | 1886 | 17 | Person name *W. A. Smith*, house *Fair View*. |
| `summers-rev-j-f-st` | `summers-rev-j-f-st` | 1903 | 9 | Clergyman bleed: *Rev. J. F. Summers*, St. John's Vicarage. |

---

## 4. Public Buildings & Institutions (Not Standalone Streets)

These entries represent prominent buildings, courts, or chapels that should either be classified under their containing street or tagged as institutions:

| Institution Name | Slug | Year(s) | Records | Action Required |
| :--- | :--- | :--- | :--- | :--- |
| `county-police-court` | `county-police-court` | 1903 | 2 | Reassign to parent street (Commercial Street / Marshes Road). |
| `marshes-county-police-court` | `marshes-county-police-court` | 1902 | 5 | Reassign to Marshes Road. |
| `gymnasium` | `gymnasium` | 1927 | 5 | Reassign to containing street. |
| `newport-savings-bank` | `newport-savings-bank` | 1886 | 1 | Reassign to parent street. |
| `wesleyan-miss-n-chapel` | `wesleyan-miss-n-chapel` | - | 0 | Header artifact; purge or tag as non-street. |
| `newport-house` | `newport-house` | 1971 | 68 | Investigate containing street (likely a block/flats development). |

---

## 5. OCR Fragments & Truncations (Under Investigation)

Raw OCR header corruptions or truncated street names requiring trace back to raw TSVs:

| Fragment / String | Slug | Year(s) | Records | Investigation Note |
| :--- | :--- | :--- | :--- | :--- |
| `and-fairoak-avenue` | `and-fairoak-avenue` | 1902 | 4 | OCR bleed (likely *Fair Oak Avenue* or cross-street connector). |
| `at-eastern-dry-docks` | `at-eastern-dry-docks` | 1902, 1903 | 3 | Dock pointer/cross-reference. |
| `brynderyn-road` | `brynderyn-road` | 1886 | 4 | No record of this spelling in 1886 reference book. |
| `court` | `court` | 1886 | 29 | Truncated name (e.g. *Court Street*, *Court Road*, or numbered court). |
| `for-old-dock` | `for-old-dock` | 1903 | 17 | Navigation/directory pointer to Old Dock. |
| `house` | `house` | 1927 | 18 | Truncated building/street name. |
| `kingsm` | `kingsm` | 1927 | 10 | Truncation of *Kingsmill Terrace*. |
| `l-d-s-r-c` | `l-d-s-r-c` | - | 0 | Abbreviation artifact. |
| `m-r-s` | `m-r-s` | - | 0 | Title/abbreviation artifact. |
| `marshes` | `marshes` | 1925 | 95 | Truncation of *Marshes Road*. |
| `pool-road` | `pool-road` | 1886 | 11 | Likely truncation of *Duckpool Road*. |
| `public-park` | `public-park` | 1902, 1903 | 46 | Park lodges/keepers or border entries. |
| `rev-dd-rd` | `rev-dd-rd` | 1903 | 42 | Severe OCR corruption of street name. |
| `rivers-de` | `rivers-de` | 1927 | 45 | Truncation of *Riverside* / *Riverside Drive*. |
| `shaftsbury-park` | `shaftsbury-park` | 1920 | 10 | Shaftesbury Park lodges/keepers. |
| `st-james-street` | `st-james-street` | 1920 | 7 | Audit note: Check if this should actually be *St James Road*. |
| `victoria-ivor-place` | `victoria-ivor-place` | 1886 | 32 | Audit note: Victoria Place / Ivor Place column bleed. |
| `victoria-street` | `victoria-street` | 1882 | 1 | Audit note: Does not exist (contains cross-reference text). |
| `virgin-street` | `virgin-street` | 1903 | 118 | Header bleed: Parsed from *CHURCH OF ST. MARY THE VIRGIN*. |
| `vue-court` | `vue-court` | 1903 | 15 | Audit note: Does not exist in street directory. |

---

## 6. Workflow & Execution Plan

1. **User Continues Auditing**:
   - Work through letters in `streets_audit.html` with physical reference books.
   - Click **Approve** on confirmed streets.
   - Add notes or edit canonical names as needed.
   - Download updated `master_streets.json` periodically.
2. **Automated Tracking**:
   - `apply_street_audit.py` ingests newly downloaded files and updates this register.
3. **Batch Execution (When Ready)**:
   - When the audit milestone is reached, batch cleaning rules will be compiled into `clean_csv.py` to merge aliases, reassign villa bleeds, and resolve OCR fragments in one unified build.
