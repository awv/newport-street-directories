import csv
import json
import re
from collections import defaultdict

# Define complete mapping dictionary
RENAME_MAP = {
    # Streets to be renamed
    "Alma Street (Upper)": "Upper Alma Street",
    "Baneswell road": "Baneswell Road",
    "Calne": "Calne Place",
    "Collingwood St": "Collingwood Street",
    "E S Arundel Road": "Arundel Road",
    "Edward VII. Avenue": "Edward VII Avenue",
    "Edward VII. Crescent": "Edward VII Crescent",
    "George Street (Lower)": "Lower George Street",
    "Jayne'S Buildings": "Jayne's Buildings",
    "Queen'S Buildings": "Queen's Buildings",

    # Streets to be merged
    "Aragon Street, C": "Aragon Street",
    "Bishop Street, B.t": "Bishop Street",
    "Cambria Road": "Cambrian Road",
    "Caldicot": "Caldicot Street",
    "Cambria": "Cambria Place",
    "Carisbrook Rd": "Carisbrooke Road",
    "Carpenters’ Lane": "Carpenter's Arms Lane",
    "Caston Place": "Caxton Place",
    "Commercial St": "Commercial Street",
    "Constables'": "Constables Lane",
    "Coomassie": "Coomassie Street",
    "Coowassie Street": "Coomassie Street",
    "Court-y-bella Street": "Courtybella Street",
    "Courtybella St": "Courtybella Street",
    "Courtybella": "Courtybella Street",
    "Dorset": "Dorset Place",
    "Downing": "Downing Street",
    "Duckpool": "Duckpool Road",
    "East Market St": "East Market Street",
    "Factroy Road": "Factory Road",
    "Ford Street, B": "Ford Street",
    "Frederick Street, P": "Frederick Street",
    "Harryh Street": "Harrhy Street",
    "Ifton Street, L": "Ifton Street",
    "James Street, P": "James Street",
    "Jeddo Street, P": "Jeddo Street",
    "Kensington Pl": "Kensington Place",
    "Lime Street, P": "Lime Street",
    "Line Street": "Lime Street",
    "Llanarth Street. D": "Llanarth Street",
    "Llanthamthi Street": "Llanthewy Road",
    "Llanthanthi": "Llanthewy Road",
    "Llewellin Street, L": "Llewellyn Street",
    "London Street, M": "London Street",
    "Lord Street, B.t": "Lord Street",
    "Lords Street": "Lord Street",
    "Marion Street, P": "Marion Street",
    "Marian Street, Pill": "Marion Street",
    "Mendalgfief Road": "Mendalgief Road",
    "New Street, P": "New Street",
    "New Ruperra St": "New Ruperra Street",
    "Potter Street, P": "Potter Street",
    "Potter'S Parade, P": "Potters Parade",
    "Price": "Price Street",
    "Prince": "Prince Street",
    "Scard Street. D": "Scard Street",
    "Screw Packet Rd. C": "Screw Packet Road",
    "Serpentine Road. C": "Serpentine Road",
    "Shaftesbury St": "Shaftesbury Street",
    "South Market St": "South Market Street",
    "St. Edward Street D 5/60": "St. Edward Street",
    "St. Mark's Cres": "St. Mark's Crescent",
    "St. Stephen’s Road. E": "St. Stephen's Road",
    "St. Vincent’s Road. C": "St. Vincent Road",
    "St. Vincent's Road": "St. Vincent Road",
    "St. Woolos Place. D": "St. Woolos Place",
    "St. Woolos Road. D": "St. Woolos Road",
    "Summer Hill Av": "Summerhill Avenue",
    "Summer Hill Avenue": "Summerhill Avenue",
    "Temple Street, P": "Temple Street",
    "Tgare Street": "Tregare Street",
    "Tredegar Street, P": "Tredegar Street",
    "Triley Street, M": "Triley Street",
    "Trinity Place, P": "Trinity Place",
    "Watchhouse Par. P": "Watchhouse Parade",
    "Water'S Lane": "Waters Lane",
    "Wednesbury St": "Wednesbury Street",
    "West Market St": "West Market Street",
    "Westville": "Westville Road",
    "Whitby Place, B.t": "Whitby Place",
    "Williams Street, P": "Williams Street",
    "Windsor Terrace, B": "Windsor Terrace",
    "Withey": "Withey Bed",
    "Witham": "Witham Street",
    "Wolseley Street, P": "Wolseley Street",
    "Wolesly": "Wolseley Street",

    # Misc & Specific fixes
    "Caxton Street": "Caxton Place",
    "Clytha Council": "Clytha Park Road",
    "Clythrough Road": "Clytha Square",
    "Rock Dale": "Rockfield Road",
    "Eveswell Park": "Eveswell Park Road",
    "Eseswell Park": "Eveswell Park Road",
    "Eswewell Park": "Eveswell Park Road",

    # Not a street mappings
    "Chapel": "Chapel Street",
    "Cattle Market": "Commercial Road",
    "Christchurch Cemetery": "Christchurch Road",
    "Corporation Baths And Gymnasium": "Carlisle Place",
    "Corporation Market Yard": "Commercial Road",
    "Corporation Yard": "Commercial Road",
    "Edwards Ltd., 'Sports' Outfitters, 64 Commercial Street. Tel. 531": "Commercial Street",
    "Edwards Ltd., Gunmakers & Sports' Outfitters, 64 Commercial Street": "Commercial Street",
    "F.r.c.s.i": "Commercial Street",
    "F.s.i": "Commercial Street",
    "Francis' Dye Works, 26 Church Road Maindee": "Church Road",
    "Francis' Dye Works, 26 Church Road, Maindee. Estab": "Church Road",
    "Francis' Dye Works, 26 Church Road, Maindee. Estab. 1890": "Church Road",
    "Francis' Dye Works, 26 Church Road, Mandee. Estab. 1890": "Church Road",
    "G.W.R": "High Street",
    "Gibbon H. railway gu'rd": "Railway Street",
    "Geo. Greenland & Sons, Proprietors. Telephone 2416": "Commercial Street",
    "Geo. Greenland & Sons, Proprietors. Nat. Tel. 0180": "Commercial Street",
    "H. C. P": "Commercial Street",
    "Herbert Edwards Ltd": "Commercial Street",
    "Higher": "High Street",
    "Holy Cross": "St. Woolos Road",
    "Holy Trinity": "Trinity Place",
    "Hughing": "High Street",
    "L. & N.w.r": "High Street",
    "L.r.c.p": "Commercial Street",
    "Langmaid, House Agent, Newport And Blackwood": "High Street",
    "Langmaid, Western Mail Chambers, High Street, Newport": "High Street",
    "Largest Furniture Showrooms In South Wales": "Commercial Street",
    "M.b., B.ch": "Commercial Street",
    "M.o., S.b. & A. I. Office": "Commercial Street",
    "M.o., S.b., A. & I": "Commercial Street",
    "M.r.c.s": "Commercial Street",
    "Maindee Schools": "Maindee",
    "Mourning Orders Promptly Attended To. Telephone 2080": "Commercial Street",
    "Newport Elementary": "Commercial Street",
    "P. E. Gane Ltd., 161–162 Commercial Street, Newport": "Carlisle Place",
    "P. E. Gane Ltd., Commercial Street, Newport": "Commercial Street",
    "P. E. Gane Ltd., Furnishers, Commercial Street, Newport": "Commercial Street",
    "Poole G. T": "Commercial Street",
    "Pillgwenlly Post Office T. & M.o., S.b., And A. And I. Office": "Commercial Road",
    "R. H. Johns Ltd., Paper Merchants, 46 Commercial Street, Newport": "Commercial Street",
    "R. H. Johns Ltd., Printers & Stationers, 46 Commercial St., Newport": "Commercial Street",
    "R.a.o.b": "Commercial Street",
    "R.f.a": "Commercial Street",
    "S. John Baptist": "Church Street",
    "St. James' Church": "St. James Street",
    "St. Mary Street Baptist": "St. Mary Street",
    "St. Mary Street Baptist Chapel": "St. Mary Street",
    "St. Matthew'S Church": "St. Matthew Street",
    "t.s.o": "Commercial Street",
    "Telephone": "Commercial Street",
    "The Steam Laundry Co., Bath Street": "Bath Street",
    "The Newport Steam Laundry Co., Bath Street": "Bath Street",
    "The Newport Steam Laundry Co., Bath Street Ro": "Bath Street",
    "The Provision Market": "Market Street",
    "Town Hall": "Commercial Street",
    "Trapnell": "Commercial Street",
    "Tredegar Corn Exchange": "Commercial Street",
    "Victoria Hall": "Victoria Road"
}

with open("edge_cases.json", "r", encoding="utf-8") as f:
    ec = json.load(f)

overrides = ec.get("overrides", [])

# Add overrides for each rename
added_count = 0
for src, dst in RENAME_MAP.items():
    overrides.append({
        "reason": f"Batch audit: Map '{src}' to '{dst}'",
        "match": {
            "street": src
        },
        "apply": {
            "street": dst
        }
    })
    added_count += 1

# Add special override for Arlington Street 1893 -> Stow Hill
overrides.append({
    "reason": "Batch audit: Reassign 1893 Arlington Street records to Stow Hill (Arlington Terrace)",
    "match": {
        "street": "Arlington Street",
        "year": "1893"
    },
    "apply": {
        "street": "Stow Hill"
    }
})
added_count += 1

ec["overrides"] = overrides

with open("edge_cases.json", "w", encoding="utf-8") as f:
    json.dump(ec, f, indent=2, ensure_ascii=False)

print(f"Successfully added {added_count} batch overrides to edge_cases.json!")
