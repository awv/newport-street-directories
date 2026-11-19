#!/usr/bin/env python3
"""Build data/trade_glossary.json by enriching curated Newport trade definitions with live stats from data/trades.json."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRADES_JSON = ROOT / "data" / "trades.json"
OUT_JSON = ROOT / "data" / "trade_glossary.json"

# (term, family, archaic, variants, description)
GLOSSARY_ENTRIES = [
    # Maritime & Docks
    ("Coal Trimmer", "Maritime & Docks", True, ["Trimmer", "Coal Trmr"], "Loaded and evenly distributed coal inside ship holds at Newport Docks so vessels stayed balanced and coal would not shift at sea."),
    ("Hobbler", "Maritime & Docks", True, ["Dock Hobbler"], "Casual dockside worker who assisted with mooring, unmooring, and handling ropes for vessels entering and leaving the Usk and Newport Docks."),
    ("Tidewaiter", "Maritime & Docks", True, ["Tide Surveyor"], "Customs officer who boarded incoming merchant ships on the tide to inspect cargo and prevent smuggling before duties were paid."),
    ("Stevedore", "Maritime & Docks", False, [], "Dockworker or contractor responsible for loading and stowing cargo efficiently inside a ship's hold."),
    ("Rigger", "Maritime & Docks", False, ["Ship Rigger"], "Skilled maritime worker who fitted, repaired, and maintained the standing and running rigging, ropes, and spars of sailing ships."),
    ("Shipwright", "Maritime & Docks", False, ["Ship Carpenter"], "Skilled carpenter specializing in building, repairing, and caulking wooden hulls and decks of ships."),
    ("Wharfinger", "Maritime & Docks", True, [], "Keeper or manager of a river or dock wharf, overseeing the landing, storage, and dispatch of cargo and collecting wharfage dues."),
    ("Lighterman", "Maritime & Docks", True, ["Boatman", "Waterman"], "Operator of a flat-bottomed barge (lighter) ferrying coal, iron, and goods between wharves along the River Usk and larger ships."),
    ("Pilot", "Maritime & Docks", False, ["Dock Pilot", "Pilot'S Man", "Pilot'S Assistant"], "Licensed mariner with expert knowledge of the Bristol Channel and River Usk tides who guided ships safely into Newport Docks."),
    ("Master Mariner", "Maritime & Docks", False, ["Mariner", "Seaman"], "Certified captain qualified to command a merchant vessel; 'Mariner' and 'Seaman' denoted crew serving aboard merchant ships."),
    ("Sailmaker", "Maritime & Docks", True, [], "Craftsman who cut, stitched, and repaired heavy canvas sails, awnings, and tarpaulins for sailing vessels."),
    ("Dock Labourer", "Maritime & Docks", False, ["Docker", "Dockman"], "General dockside labourer employed loading and unloading timber, iron, pitprops, and general cargo at Alexandra and Town Docks."),
    ("Tug Driver", "Maritime & Docks", True, ["Tug Boat"], "Operator or engineer aboard steam tugboats towing sailing ships and barges through the River Usk and Bristol Channel."),
    ("Coal Tipper", "Maritime & Docks", True, ["Tipper"], "Dockside operator of hydraulic coal tips that lifted entire railway wagons and tipped coal down chutes into ships' holds."),
    ("Hoistman", "Maritime & Docks", True, [], "Operator of hydraulic or electric coal hoists raising loaded coal wagons at Newport's Alexandra Docks."),
    ("Donkeyman", "Maritime & Docks", True, [], "Crewman or dock worker tending small auxiliary 'donkey' steam engines used to power winches, pumps, and cargo gear."),
    ("Shipbroker", "Maritime & Docks", False, ["Shipbrokers"], "Maritime agent arranging ship charters, cargo space, insurance, and port clearance for vessels trading out of Newport."),
    ("Marine Store Dealer", "Maritime & Docks", True, ["Marine Stores"], "Merchant buying and reselling old rope, canvas, scrap iron, rags, and salvaged ships' fittings."),
    ("Ropemaker", "Maritime & Docks", True, [], "Craftsman twisting hemp and manila fibres into heavy hawsers, rigging, and mooring lines for ships."),
    ("Bridgeman", "Maritime & Docks", True, [], "Attendant operating swing bridges, dock gates, or toll bridges across the River Usk and dock entrances."),

    # Metal & Iron Workers
    ("Puddler", "Metal & Iron Workers", True, [], "Highly skilled ironworker who stirred molten pig iron in a reverberatory furnace to burn off carbon and produce wrought iron."),
    ("Ironworker", "Metal & Iron Workers", False, ["Iron Worker", "Ironwkr", "I'worker"], "Worker in Newport's iron and steel mills, foundries, or rolling works producing rails, bars, and structural iron."),
    ("Steelworker", "Metal & Iron Workers", False, ["steel worker", "steelwkr"], "Worker employed in steelmaking furnaces and rolling mills, increasingly replacing wrought iron from the late 19th century."),
    ("Moulder", "Metal & Iron Workers", False, ["Iron Moulder", "Brass Moulder"], "Foundry worker who packed sand moulds around patterns to cast molten iron or brass into machinery parts and pipes."),
    ("Boilermaker", "Metal & Iron Workers", False, [], "Metalworker who shaped, riveted, and repaired heavy iron and steel plates for steam locomotives, marine boilers, and ships."),
    ("Fitter", "Metal & Iron Workers", False, ["Engineer Fitter", "Signal Fitter", "Fitter'S Helper"], "Precision metalworker who assembled, filed, and fitted machined metal parts for engines, railway gear, and dock machinery."),
    ("Striker", "Metal & Iron Workers", True, ["Blacksmith'S Striker"], "Blacksmith's assistant who swung a heavy sledgehammer on hot iron while the smith shaped it with tongs and a hand hammer."),
    ("Roller", "Metal & Iron Workers", True, [], "Mill worker who fed red-hot iron or steel billets through heavy powered rollers to form bars, rails, or plates."),
    ("Doubler", "Metal & Iron Workers", True, [], "Skilled South Wales tinplate mill worker who folded hot rolled iron or steel sheets double with tongs before reheating and rolling."),
    ("Annealer", "Metal & Iron Workers", True, [], "Mill worker who heat-treated rolled steel and tinplate sheets in annealing pots to soften the metal for further processing."),
    ("Pickler", "Metal & Iron Workers", True, [], "Tinplate worker who dipped rolled iron or steel sheets into acid vats to remove oxide scale before coating with tin."),
    ("Shearer", "Metal & Iron Workers", True, [], "Mill worker operating heavy powered shears to trim hot or cold rolled iron and steel sheets to size."),
    ("Rivetter", "Metal & Iron Workers", True, ["Rivet Maker"], "Shipyard or boiler-shop worker who hammered red-hot iron rivets to fasten steel plates together."),
    ("Scaler", "Metal & Iron Workers", True, [], "Shipyard or dockside worker who chipped rust, barnacles, and limescale from ship hulls and marine boilers."),
    ("Patternmaker", "Metal & Iron Workers", True, [], "Highly skilled woodworker crafting exact wooden patterns used by foundry moulders to cast metal parts."),
    ("Machinist", "Metal & Iron Workers", False, [], "Worker operating power-driven lathes, drills, and milling machines in engineering workshops."),
    ("Millwright", "Metal & Iron Workers", True, [], "Master mechanic who installed, aligned, and repaired heavy shafting, gearing, and steam-driven mill machinery."),
    ("Coppersmith", "Metal & Iron Workers", True, [], "Smith shaping copper pipes, stills, and fittings for breweries, ships, and locomotives."),
    ("Farrier", "Metal & Iron Workers", True, [], "Specialist equine blacksmith who shod horses and treated hoof and leg ailments."),
    ("Furnaceman", "Metal & Iron Workers", False, [], "Worker tending blast or reheating furnaces, regulating fuel, air blast, and molten metal tapping."),
    ("Wiredrawer", "Metal & Iron Workers", True, ["Wire Drawer"], "Metalworker who pulled heated iron or steel rods through progressively smaller dies to produce wire."),
    ("Acetylene Burner", "Metal & Iron Workers", False, ["Acet Br", "Acet. Brnr"], "Metalworker using an oxy-acetylene torch to cut or weld steel plates in shipyards, boiler shops, and scrap yards."),
    ("Boiler Cleaner", "Metal & Iron Workers", True, ["Blr Cleaner"], "Worker who crawled inside cooled steam boilers to chip away limescale, soot, and sediment from flues and tubes."),
    ("Blacksmith", "Metal & Iron Workers", False, ["Smith", "Shoeing Smith"], "Metalsmith forging wrought iron tools, chains, hinges, and horseshoes at a hearth and anvil."),
    ("Tinplate Worker", "Metal & Iron Workers", True, ["Tinman", "Brazier", "Tinsmith"], "Craftsman working sheet iron coated with tin to make cans, kettles, lanterns, and domestic utensils."),

    # Railway
    ("G.W.R.", "Railway", False, ["Great Western Railway", "GWR"], "Employee of the Great Western Railway, which operated Newport High Street station, goods yards, and major South Wales coal routes."),
    ("Platelayer", "Railway", True, ["Ganger"], "Railway trackman responsible for laying, aligning, and maintaining rails and sleepers; a 'Ganger' supervised a track gang."),
    ("Shunter", "Railway", False, ["shunter G.W.R."], "Railway yard worker who coupled, uncoupled, and directed wagons onto sidings to assemble coal and freight trains."),
    ("Pointsman", "Railway", True, [], "Early railway worker stationed beside track junctions to throw hand levers switching trains onto sidings."),
    ("Engineman", "Railway", True, [], "Operator tending stationary steam engines for dock hydraulics, waterworks, or colliery winding gear."),
    ("Guard", "Railway", False, ["Railway Guard", "Goods Guard", "Dock Guard"], "Official in charge of a passenger or freight train's safety, braking van, and timetable compliance."),
    ("Ballast Guard", "Railway", True, ["Ballast Grd"], "Guard assigned to railway engineering trains hauling crushed stone (ballast) used to pack and level track beds."),
    ("Signalman", "Railway", False, [], "Operator stationed in a signal box pulling mechanical levers to set points and semaphore signals for safe train movements."),
    ("Porter", "Railway", False, ["Railway Porter"], "Station worker handling passenger luggage, parcels, and platform duties."),
    ("Engine Driver", "Railway", False, ["Loco. Driver"], "Driver of a steam locomotive on main lines, colliery branches, or dock sidings (also used for stationary steam engine operators)."),
    ("Fireman", "Railway", False, ["Stoker"], "Locomotive or boiler crew member who shovelled coal into the firebox and monitored steam pressure and water levels."),

    # Crafts & Artisans
    ("Cordwainer", "Crafts & Artisans", True, ["Shoemaker", "Bootmaker"], "Traditional shoemaker working with fine new leather (distinct from a cobbler, who repaired old shoes)."),
    ("Cooper", "Crafts & Artisans", True, [], "Craftsman who built and repaired wooden casks, barrels, and tubs bound with iron hoops for beer, butter, and dry goods."),
    ("Fellmonger", "Crafts & Artisans", True, [], "Dealer who separated wool from sheepskins and prepared hides for tanners and leather dressers."),
    ("Currier", "Crafts & Artisans", True, [], "Leather craftsman who shaved, greased, and dyed rough tanned hides to make supple leather for boots and saddlery."),
    ("Tanner", "Crafts & Artisans", True, [], "Craftsman soaking raw animal hides in lime and oak-bark pits to preserve and convert them into leather."),
    ("Cabinetmaker", "Crafts & Artisans", False, [], "Skilled woodworker crafting fine domestic furniture, chests, sideboards, and veneered cabinetry."),
    ("Maltster", "Crafts & Artisans", True, [], "Craftsman steeping, germinating, and kilning barley into malt to supply Newport's breweries."),
    ("Saddler", "Crafts & Artisans", True, ["Harness Maker"], "Leatherworker crafting and repairing horse saddles, collars, bridles, and cart harnesses."),
    ("Wheelwright", "Crafts & Artisans", True, [], "Woodworker and smith who built and repaired wooden spoked wheels rimmed with iron tyres for carts and carriages."),
    ("Tailor", "Crafts & Artisans", False, [], "Maker of bespoke men's suits, coats, and waistcoats."),
    ("Tailoress", "Crafts & Artisans", True, ["Trss"], "Female garment maker employed in tailoring workshops or from home, often specializing in waistcoats, trousers, or finishing."),
    ("Dressmaker", "Crafts & Artisans", False, [], "Maker of women's and children's dresses, blouses, and tailored daywear."),
    ("Milliner", "Crafts & Artisans", True, [], "Designer, maker, and trimmer of women's hats, bonnets, and headwear."),
    ("Upholsterer", "Crafts & Artisans", False, [], "Craftsman padding, springing, and covering chairs, sofas, and curtains."),
    ("Bookbinder", "Crafts & Artisans", False, [], "Craftsman folding, sewing, and binding printed sheets into leather or cloth-covered books and ledgers."),
    ("Printer", "Crafts & Artisans", False, ["Compositor"], "Typesetter and press operator producing newspapers, handbills, and commercial stationery."),
    ("Watchmaker", "Crafts & Artisans", False, ["Watchmaker And Jeweller"], "Skilled craftsman assembling, cleaning, and repairing pocket watches, clocks, and chronometers."),
    ("Basketmaker", "Crafts & Artisans", True, [], "Weaver of willow wicker baskets, hampers, and industrial skeps for docks, markets, and bakeries."),
    ("Brushmaker", "Crafts & Artisans", True, [], "Maker of bristle brooms, scrubbing brushes, and industrial brushes."),

    # Building & Construction
    ("Carpenter", "Building & Construction", False, ["Joiner"], "Woodworker framing roofs, floors, and structural timber; 'Joiners' focused on finer interior doors, stairs, and window frames."),
    ("Mason", "Building & Construction", False, ["Stonemason", "Mason'S Labourer"], "Craftsman cutting, dressing, and laying stone blocks for buildings, bridges, and dock walls."),
    ("Bricklayer", "Building & Construction", False, ["Brklr"], "Tradesman laying bricks and mortar for houses, chimneys, factories, and arches."),
    ("Plasterer", "Building & Construction", False, ["Plastr", "Plastr'R"], "Tradesman applying lime or gypsum plaster to interior walls, lath-and-plaster ceilings, and decorative cornices."),
    ("Painter", "Building & Construction", False, ["Decorator", "Ship Painter", "Coach Painter"], "House, ship, or coach painter applying protective paints, varnishes, and wallpaper."),
    ("Plumber", "Building & Construction", False, ["Gas Fitter"], "Tradesman installing lead water pipes, roof flashings, sanitation, and early town gas piping."),
    ("Glazier", "Building & Construction", False, [], "Tradesman cutting and fitting glass panes into wooden and iron window frames."),
    ("Electrician", "Building & Construction", False, [], "Technician wiring electric lighting, bells, and power equipment from the late Victorian era onward."),
    ("Gas Worker", "Building & Construction", False, ["Gas Works"], "Worker at Newport's gasworks retorts and purifiers producing coal gas for street lamps and homes."),
    ("Builder", "Building & Construction", False, [], "Building contractor coordinating bricklayers, carpenters, and masons on housing and commercial developments."),
    ("Sawyer", "Building & Construction", True, [], "Timber worker cutting logs into planks using either a two-man pit saw or steam-powered sawmill."),
    ("Coach Builder", "Building & Construction", True, ["Coachbuilder", "Carriage Builder", "Wagon Builder"], "Craftsman constructing wooden bodies for horse-drawn coaches, carts, and railway wagons."),

    # Shopkeepers & Retail
    ("Victualler", "Shopkeepers & Retail", True, ["Licensed Victualler", "Beer Retailer"], "Licensed keeper of an inn, tavern, or public house authorized to sell alcoholic drink and food."),
    ("Chandler", "Shopkeepers & Retail", True, ["Ship Chandler", "Tallow Chandler"], "Originally a maker/seller of candles; in Newport, 'Ship Chandlers' supplied vessels with rope, oil, paint, and provisions."),
    ("Poulterer", "Shopkeepers & Retail", True, [], "Retailer selling poultry, rabbits, and game."),
    ("Provision Dealer", "Shopkeepers & Retail", False, ["Grocer"], "Shopkeeper selling staple foods such as bacon, butter, cheese, tea, sugar, and flour."),
    ("Draper", "Shopkeepers & Retail", True, ["Linen Draper", "Woollen Draper"], "Retailer of cloth, textiles, haberdashery, and household linens."),
    ("Hosier", "Shopkeepers & Retail", True, ["Hosiers"], "Retailer of knitted stockings, socks, gloves, and undergarments."),
    ("Hatter", "Shopkeepers & Retail", True, ["Hatters"], "Maker or retailer of men's silk top hats, bowlers, and caps."),
    ("Pawnbroker", "Shopkeepers & Retail", True, ["Pawnbroker And Outfitter", "Pawnbrokers & Outfitters"], "Licensed lender advancing small cash loans against pledged household goods, watches, or clothing."),
    ("Hairdresser", "Shopkeepers & Retail", False, [], "Barber and hairdresser cutting hair, shaving, and often selling tobacco or perfumery."),
    ("Fruiterer", "Shopkeepers & Retail", False, [], "Shopkeeper specializing in fresh and dried fruit."),
    ("Milkman", "Shopkeepers & Retail", False, ["Dairyman"], "Dairy vendor delivering fresh milk by churn and ladle along street rounds."),
    ("Miller", "Shopkeepers & Retail", True, [], "Operator of a water or steam corn mill grinding wheat and oats into flour and animal feed."),
    ("Hawker", "Shopkeepers & Retail", True, [], "Itinerant street trader travelling door-to-door selling household wares, produce, or haberdashery."),
    ("Herbalist", "Shopkeepers & Retail", True, [], "Practitioner and shopkeeper selling botanical remedies, tonics, and dried medicinal herbs."),
    ("Outfitter", "Shopkeepers & Retail", True, [], "Retailer selling ready-made clothing, hats, boots, and seafarers' kit."),
    ("Ironmonger", "Shopkeepers & Retail", False, [], "Hardware merchant selling tools, nails, locks, grates, and domestic metalware."),
    ("Chemist", "Shopkeepers & Retail", False, ["Druggist", "Pharmaceutical Chemist"], "Pharmacist compounding and selling medicines, tinctures, and household chemicals."),
    ("Tobacconist", "Shopkeepers & Retail", False, [], "Shopkeeper selling pipe tobacco, snuff, cigars, and matches."),
    ("Confectioner", "Shopkeepers & Retail", False, [], "Maker and seller of sweets, pastries, cakes, and sugar confectionery."),
    ("Greengrocer", "Shopkeepers & Retail", False, [], "Retailer of fresh vegetables, fruit, and potatoes."),
    ("Butcher", "Shopkeepers & Retail", False, ["Pork Butcher"], "Tradesman slaughtering livestock or dressing and selling meat."),
    ("Baker", "Shopkeepers & Retail", False, ["Grocer & Baker"], "Tradesman baking bread, rolls, and biscuits in brick ovens."),
    ("Fishmonger", "Shopkeepers & Retail", False, [], "Retailer selling fresh and cured fish."),
    ("Newsagent", "Shopkeepers & Retail", False, ["Stationer"], "Shopkeeper selling newspapers, periodicals, books, and writing paper."),
    ("Ice Cream Vendor", "Shopkeepers & Retail", False, ["Ice Crm Vr"], "Street or shop vendor selling homemade ice cream, often from handcarts."),

    # Transport & Drivers
    ("Haulier", "Transport & Drivers", False, ["Carter"], "Carrier using horse-drawn wagons or carts to haul coal, stone, timber, and goods between docks, stations, and yards."),
    ("Coachman", "Transport & Drivers", True, ["Cab Driver", "Cabman", "Cab Proprietor"], "Driver of private horse-drawn carriages, hackney cabs, or owner of cab horses for hire."),
    ("Tram Driver", "Transport & Drivers", True, ["Tram Dr", "Motorman"], "Driver of horse-drawn or electric street tramcars operated by Newport Corporation."),
    ("Tram Conductor", "Transport & Drivers", True, ["Tram Con."], "Conductor collecting fares and managing passengers aboard Newport's street trams."),
    ("Bus Conductor", "Transport & Drivers", False, ["Bus Cond"], "Conductor collecting fares and signalling stops on motor omnibuses."),
    ("Crane Driver", "Transport & Drivers", False, ["Craneman"], "Operator of hydraulic or steam cranes hoisting coal wagons and cargo at Newport Docks."),
    ("Motor Driver", "Transport & Drivers", False, ["Lorry Driver", "Chauffeur", "Taxi Driver"], "Early 20th-century term for drivers of petrol lorries, delivery vans, taxis, and private motor cars."),

    # Clerical & Commercial
    ("Clerk", "Clerical & Commercial", False, ["Accountant", "Cashier"], "Office worker keeping ledgers, correspondence, shipping manifests, and wages for merchants, solicitors, and docks."),
    ("Weighman", "Clerical & Commercial", True, [], "Weighbridge clerk recording the tonnage of coal wagons, iron, and cargo at docks and works."),
    ("Checker", "Clerical & Commercial", False, ["Tally Clerk"], "Goods-yard or dockside clerk counting and verifying cargo crates, timber, and wagon loads."),
    ("Timekeeper", "Clerical & Commercial", False, [], "Factory or dock gatekeeper logging workers' arrival, departure, and shift hours for payroll."),
    ("Warehouseman", "Clerical & Commercial", False, ["Storekeeper", "Packer"], "Worker receiving, storing, packing, and dispatching wholesale merchandise in warehouses."),
    ("Auctioneer", "Clerical & Commercial", False, ["Auctioneers"], "Licensed appraiser and public auctioneer selling property, livestock, and ships' cargoes."),
    ("Commercial Traveller", "Clerical & Commercial", False, ["Traveller"], "Sales representative travelling by rail between towns with sample cases to take wholesale orders for manufacturers."),
    ("Commercial Agent", "Clerical & Commercial", False, ["Com. Agent", "Agent"], "Local representative buying, selling, or shipping goods on commission for collieries, breweries, or manufacturers."),
    ("Insurance Agent", "Clerical & Commercial", False, [], "Agent selling life, fire, and marine policies and collecting weekly premiums door-to-door."),
    ("Coal Merchant", "Clerical & Commercial", False, ["Coal Dealer"], "Wholesale or retail merchant buying colliery coal by rail wagon and selling it for shipping or domestic grates."),
    ("Corn Merchant", "Clerical & Commercial", False, [], "Wholesale dealer in grain, oats, animal feed, and flour."),

    # Service & Domestic
    ("Ostler", "Service & Domestic", True, [], "Stableman at an inn or coaching house who fed, groomed, and cared for guests' horses."),
    ("Cellarman", "Service & Domestic", True, [], "Worker managing beer barrels, bottling, and wine cellars for a pub, hotel, or wine merchant."),
    ("Charwoman", "Service & Domestic", True, [], "Woman hired by the day to scrub floors, grates, and steps in offices and private homes."),
    ("Laundress", "Service & Domestic", True, [], "Woman earning a living washing, starching, and ironing linen and clothing by hand."),
    ("Gardener", "Service & Domestic", False, ["Market Gardener"], "Caretaker of private grounds, or a 'Market Gardener' growing vegetables and fruit for town sale."),
    ("Caretaker", "Service & Domestic", False, [], "Resident custodian responsible for locking, cleaning, and heating a public building, school, or chapel."),
    ("Chimney Sweep", "Service & Domestic", True, ["Sweep"], "Tradesman sweeping soot from domestic and bakery flues using jointed rods and brushes."),
    ("Boarding House", "Service & Domestic", False, [], "Householder providing lodging and meals for sailors, railwaymen, clerks, and commercial travellers."),
    ("Undertaker", "Service & Domestic", False, ["Undertakers"], "Funeral director arranging coffins, horse-drawn hearses, and burials."),

    # Professional & Civic
    ("Solicitor", "Professional & Civic", False, [], "Qualified lawyer advising clients on property, contracts, shipping disputes, and magistrates' court cases."),
    ("Surgeon", "Professional & Civic", False, ["Physician And Surgeon"], "Medical practitioner performing operations and general medical care."),
    ("Veterinary Surgeon", "Professional & Civic", False, [], "Animal doctor essential in an era reliant on pit ponies, haulage horses, and dairy cattle."),
    ("Dock Police", "Professional & Civic", False, ["Police", "Policeman", "Police Sergeant", "Police Inspector"], "Constable employed by the Alexandra Dock Company or Newport Borough Police to patrol quays, warehouses, and streets."),
    ("Lamplighter", "Professional & Civic", True, ["Lamplightr"], "Municipal worker walking a dusk-and-dawn round with a ladder or pole to light, trim, and extinguish gas street lamps."),
    ("Schoolmaster", "Professional & Civic", False, ["Teacher"], "Headteacher or master of a National, Board, or private academy."),

    # Labourers & Manual
    ("Labourer", "Labourers & Manual", False, ["Laborer"], "General manual worker hired for heavy lifting, digging, roadwork, or yard duties across town."),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> None:
    with open(TRADES_JSON, encoding="utf-8") as f:
        trades_data = json.load(f)

    # Index trades.json by lowercase trade string
    by_lower: dict[str, list[dict]] = {}
    for item in trades_data.get("trades", []):
        key = (item.get("t") or "").strip().lower()
        if key:
            by_lower.setdefault(key, []).append(item)

    enriched = []
    for term, family, archaic, variants, desc in GLOSSARY_ENTRIES:
        lookup_keys = [term.lower()] + [v.lower() for v in variants]
        total_count = 0
        years_set = set()
        best_sample = None
        best_sample_count = -1

        for k in lookup_keys:
            for item in by_lower.get(k, []):
                c = item.get("c", 0)
                total_count += c
                for y in item.get("y", []):
                    years_set.add(str(y))
                if c > best_sample_count and item.get("r"):
                    best_sample_count = c
                    r = item["r"]
                    # r = [year, street, house_number, building_name, forename, surname]
                    best_sample = {
                        "year": r[0],
                        "street": r[1],
                        "slug": slugify(r[1]),
                        "house_number": r[2],
                        "name": f"{r[4]} {r[5]}".strip(),
                    }

        years_sorted = sorted(years_set, key=lambda y: int(y) if y.isdigit() else 0)
        enriched.append({
            "term": term,
            "slug": slugify(term),
            "family": family,
            "archaic": archaic,
            "variants": variants,
            "description": desc,
            "count": total_count,
            "earliest": years_sorted[0] if years_sorted else "",
            "latest": years_sorted[-1] if years_sorted else "",
            "sample": best_sample,
        })

    enriched.sort(key=lambda x: x["term"].lower())
    out = {
        "total_terms": len(enriched),
        "families": sorted({e["family"] for e in enriched}),
        "terms": enriched,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    covered = sum(e["count"] for e in enriched)
    print(f"Wrote {OUT_JSON.name}: {len(enriched)} glossary terms covering {covered:,} directory records.")


if __name__ == "__main__":
    main()
