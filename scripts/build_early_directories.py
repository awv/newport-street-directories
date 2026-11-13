import json

# Compile complete accurate transcripts for 1822 Pigot directory
p1822 = {
  "year": 1822,
  "title": "Pigot & Co.’s London & Provincial New Commercial Directory for 1822-23",
  "county": "Monmouthshire",
  "town": "Newport",
  "narrative": "A CORPORATION town of Monmouthshire, delightfully seated on the river Usk, over which is a handsome stone bridge, with five arches. It has a good harbour, whence it has its name; and is 148 miles from London, 28 from Bristol, 15 from the New Passage, 12 from Caerphilly, and 12 from Cardiff. It carries on an extensive trade in coals and iron, 300,000 tons of the former, and 42,000 tons of the latter, being annually exported, and is a flourishing town, as will be seen from the shipping account, and a comparative view of the census. The town is governed by a mayor, in conjunction with another magistrate; the mayor and common council (say 12) form the corporation. There is a church, called St. Woolo’s, situated on the outskirt of the town. In the town are several places of worship for dissenters; also a masonic hall, a neat, respectable edifice, with a superior freestone front, erected in 1821, and cost nearly 500l.; and a charity school, designated the British School, in which a great number of boys are taught the principles of education, supported with a strong inculcation of moral duties. It also contains a work-house; and in 1818, an excellent market-house was erected, which cost about 3000l.\n\nMarket day is Saturday. The fairs held here are—Ascension Thursday, Nov. 6th, Aug. 15th, third Monday in the month a great market; at Stow, first Thursday after Whitsuntide, and another fair is established, but the day on which it is to be held is not fixed. In 1801, it contained 1,087 inhabitants; and in 1821, males 1,730, females 1,766—total 3,496; being an increase in 20 years of 2,409. Newport and Usk are represented in parliament by the Marquis of Worcester.\n\nPost-Office.—George Griffiths, Post Master.—Mail from London and all parts of the North of England, arrives at half-past three in the afternoon, and is despatched at nine in the morning.—Mail from South Wales arrives at half-past nine in the morning, and is despatched at three in the afternoon.",
  "post_office": {
    "post_master": "George Griffiths",
    "notes": "Mails to/from London, North of England, and South Wales"
  },
  "sections": [
    {
      "category": "Academies & Schools",
      "entries": [
        {"name": "King Mrs.", "trade": "Ladies’ boarding & day academy", "notes": ""},
        {"name": "M’Carthy Callaghen", "trade": "Gentlemen’s boarding and day academy", "notes": ""},
        {"name": "Sawyer Chas.", "trade": "Gentlemen’s day academy", "notes": ""},
        {"name": "Thomas Misses", "trade": "Ladies’ boarding and day academy", "notes": ""},
        {"name": "Williams Danl.", "trade": "Gentlemen’s boarding and day academy", "notes": ""}
      ]
    },
    {
      "category": "Attorneys & Legal",
      "entries": [
        {"name": "Brewer John", "trade": "Attorney", "notes": ""},
        {"name": "Phillips Thomas Jones", "trade": "Attorney", "notes": ""},
        {"name": "Prothero Thomas", "trade": "Attorney", "notes": ""},
        {"name": "Reece Richard Llewellin", "trade": "Attorney", "notes": ""},
        {"name": "Tripp John Richardson", "trade": "Attorney", "notes": ""}
      ]
    },
    {
      "category": "Auctioneers & Appraisers",
      "entries": [
        {"name": "Long Samuel H.", "trade": "Auctioneer & Appraiser", "notes": ""}
      ]
    },
    {
      "category": "Bankers",
      "entries": [
        {"name": "Buckle George and Co.", "trade": "Bankers", "notes": ""},
        {"name": "Forman and Fothergill", "trade": "Bankers", "notes": ""}
      ]
    },
    {
      "category": "Block & Pump Makers",
      "entries": [
        {"name": "Parrett James", "trade": "Block & Pump Maker", "notes": ""},
        {"name": "Taylor William", "trade": "Block & Pump Maker", "notes": ""}
      ]
    },
    {
      "category": "Booksellers & Stationers",
      "entries": [
        {"name": "Reed Samuel", "trade": "Bookseller & Stationer", "notes": ""},
        {"name": "Nicholas Edward", "trade": "Bookseller, Stationer & Printer", "notes": ""}
      ]
    },
    {
      "category": "Boot & Shoe Makers",
      "entries": [
        {"name": "Batten Thomas", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Lewis James", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Morris Morris", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Prosser John", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Spear Joseph & James", "trade": "Boot & Shoe Makers", "notes": ""}
      ]
    },
    {
      "category": "Brewers & Maltsters",
      "entries": [
        {"name": "Baverstock James Hinton", "trade": "Brewer", "notes": ""},
        {"name": "Jones Robert", "trade": "Brewer", "notes": ""},
        {"name": "Oliver George", "trade": "Brewer", "notes": ""},
        {"name": "Cobb John", "trade": "Maltster", "notes": ""},
        {"name": "Phillips Thomas Jones", "trade": "Maltster", "notes": ""},
        {"name": "Poulton Elizabeth", "trade": "Maltster", "notes": ""},
        {"name": "Williams John", "trade": "Maltster", "notes": ""}
      ]
    },
    {
      "category": "Builders & Carpenters",
      "entries": [
        {"name": "Batchelor Benjamin", "trade": "Builder", "notes": ""},
        {"name": "Waters & Jones", "trade": "Builders", "notes": ""}
      ]
    },
    {
      "category": "Cabinet Makers & Upholsterers",
      "entries": [
        {"name": "Francis Jonn.", "trade": "Cabinet Maker", "notes": ""},
        {"name": "Jones Samuel", "trade": "Cabinet Maker & Upholsterer", "notes": ""},
        {"name": "Morgan Jas.", "trade": "Cabinet Maker", "notes": ""},
        {"name": "Phillips Thomas", "trade": "Cabinet Maker & Upholsterer", "notes": ""}
      ]
    },
    {
      "category": "Coal Merchants & Colliery Masters",
      "entries": [
        {"name": "Edwards Thomas", "trade": "Coal Merchant & Master", "notes": ""},
        {"name": "Farquhar Robert & Co.", "trade": "Coal Merchants (of Pontypool)", "notes": "Wm. Williams, agent"},
        {"name": "George Watkin", "trade": "Coal Merchant (of Pontypool)", "notes": "Thos. Price, agent, Pillgwelly"},
        {"name": "Gething Robert", "trade": "Coal Merchant", "notes": ""},
        {"name": "Harper Moses", "trade": "Coal Merchant", "notes": ""},
        {"name": "Jenkins Richard", "trade": "Coal Merchant", "notes": ""},
        {"name": "Jones Orlando", "trade": "Coal Merchant", "notes": ""},
        {"name": "Jones William", "trade": "Coal Merchant", "notes": ""},
        {"name": "Leman J.", "trade": "Coal Merchant (of Bristol)", "notes": "Pillgwelly"},
        {"name": "Lewis Henry", "trade": "Coal Merchant", "notes": ""},
        {"name": "Penmain Company", "trade": "Coal Company", "notes": "Pillgwelly"},
        {"name": "Perkins Hopkin", "trade": "Coal Merchant", "notes": ""},
        {"name": "Powell & Williams", "trade": "Coal Merchants", "notes": ""},
        {"name": "Robinson & Edwards", "trade": "Coal Merchants", "notes": ""},
        {"name": "Verteg Hill Company", "trade": "Coal Company", "notes": ""},
        {"name": "Webb Thomas", "trade": "Coal Merchant", "notes": "Pillgwelly"},
        {"name": "Wedleake Thomas", "trade": "Coal Merchant", "notes": "Pillgwelly"}
      ]
    },
    {
      "category": "Confectioners & Bakers",
      "entries": [
        {"name": "Martin Joseph", "trade": "Confectioner", "notes": ""},
        {"name": "Napper Peter", "trade": "Confectioner", "notes": ""}
      ]
    },
    {
      "category": "Coopers",
      "entries": [
        {"name": "Dudley James", "trade": "Cooper", "notes": ""},
        {"name": "Jones Daniel", "trade": "Cooper", "notes": ""},
        {"name": "Lewellin Edmund", "trade": "Cooper", "notes": ""},
        {"name": "Luke James", "trade": "Cooper", "notes": ""}
      ]
    },
    {
      "category": "Corn & Iron Merchants",
      "entries": [
        {"name": "Robinson, Williams & Co.", "trade": "Corn & Iron Merchants", "notes": ""}
      ]
    },
    {
      "category": "Curriers & Leather Sellers",
      "entries": [
        {"name": "Harris John", "trade": "Currier", "notes": ""},
        {"name": "Sully John", "trade": "Currier", "notes": ""}
      ]
    },
    {
      "category": "Druggists & Grocers",
      "entries": [
        {"name": "Jones Abraham", "trade": "Druggist & Grocer", "notes": ""},
        {"name": "Morgan William", "trade": "Druggist & Grocer", "notes": ""}
      ]
    },
    {
      "category": "Fire & Life Insurance Offices",
      "entries": [
        {"name": "Norwich Union", "trade": "Insurance Office", "notes": "John Owen, Forman & Co.’s Bank"},
        {"name": "Royal Exchange (and Marine)", "trade": "Insurance Office", "notes": "Philip Phillips, agent (& clerk to commissioners of taxes & magistrates of Caldicot lower)"}
      ]
    },
    {
      "category": "Glass, China & Earthenware Dealers",
      "entries": [
        {"name": "Mullock Richard", "trade": "Glass, China & Earthenware Dealer", "notes": ""},
        {"name": "Watkins William", "trade": "Glass, China & Earthenware Dealer", "notes": ""}
      ]
    },
    {
      "category": "Grocers, Tea Dealers & Drapers",
      "entries": [
        {"name": "Armitage John", "trade": "Grocer & Draper", "notes": ""},
        {"name": "Clements John", "trade": "Grocer", "notes": ""},
        {"name": "Edmonds Edward", "trade": "Grocer & Draper", "notes": ""},
        {"name": "Griffiths Thomas", "trade": "Grocer & Baker", "notes": ""},
        {"name": "Jones Edmund", "trade": "Grocer", "notes": ""},
        {"name": "Jones David", "trade": "Grocer", "notes": ""},
        {"name": "Morgan Henry", "trade": "Grocer", "notes": ""},
        {"name": "Morgan Rowland", "trade": "Grocer", "notes": ""},
        {"name": "Nicholls John", "trade": "Grocer & Draper", "notes": ""},
        {"name": "Prosser Evan", "trade": "Grocer", "notes": ""},
        {"name": "Reece John", "trade": "Grocer", "notes": ""},
        {"name": "Taylor Mary", "trade": "Grocer", "notes": ""},
        {"name": "Thomas William", "trade": "Grocer & Draper", "notes": ""},
        {"name": "Vaughan Thomas", "trade": "Grocer & Draper", "notes": ""},
        {"name": "Young John", "trade": "Grocer", "notes": ""}
      ]
    },
    {
      "category": "Hat Manufacturers",
      "entries": [
        {"name": "Jones Thomas", "trade": "Hat Manufacturer", "notes": ""},
        {"name": "Lewellin John", "trade": "Hat Manufacturer", "notes": ""}
      ]
    },
    {
      "category": "Inns, Hotels & Posting Houses",
      "entries": [
        {"name": "Heath Cock", "proprietor": "Henry Jones", "trade": "Inn", "notes": ""},
        {"name": "King’s Head", "proprietor": "John Morgan", "trade": "Inn & Posting House", "notes": "Commercial & Posting establishment"},
        {"name": "Parrot", "proprietor": "James Morgan", "trade": "Inn", "notes": ""},
        {"name": "West Gate", "proprietor": "Ann Iggulden", "trade": "Inn & Posting House", "notes": "Historic hotel & posting establishment"}
      ]
    },
    {
      "category": "Iron Founders & Iron Masters",
      "entries": [
        {"name": "Astons William", "trade": "Iron Founder", "notes": ""},
        {"name": "Edwards Wm.", "trade": "Iron Founder (bar & rod iron manufacturer)", "notes": ""},
        {"name": "Bailey Joseph & Co.", "trade": "Iron Masters (of Nantyglo)", "notes": "Robert Sallows, agent"},
        {"name": "Frere Edw. & Co.", "trade": "Iron Masters (Clydach)", "notes": "Rd. Burton, agent"},
        {"name": "Hill & Son", "trade": "Iron Masters (of Blaenavon)", "notes": "Ed. Edmonds, agent"},
        {"name": "Leigh & George", "trade": "Iron Masters (of Pontypool)", "notes": "Robert Gething, agent"},
        {"name": "Tredegar Iron Comp.", "trade": "Iron Masters", "notes": "Robert B. Metcalfe, agent, Pillgwelly"}
      ]
    },
    {
      "category": "Ironmongers",
      "entries": [
        {"name": "Edwards Henry", "trade": "Ironmonger", "notes": ""},
        {"name": "Hawkins Thomas", "trade": "Ironmonger", "notes": ""},
        {"name": "Morgan Ann", "trade": "Ironmonger", "notes": ""}
      ]
    },
    {
      "category": "Linen & Woollen Drapers",
      "entries": [
        {"name": "Frost John", "trade": "Linen & Woollen Draper", "notes": "Future Chartist leader"},
        {"name": "Lowe William Henry", "trade": "Linen & Woollen Draper", "notes": ""},
        {"name": "Rogers Richard", "trade": "Linen & Woollen Draper", "notes": ""},
        {"name": "Wetherill Thomas", "trade": "Linen & Woollen Draper (& millinery)", "notes": ""}
      ]
    },
    {
      "category": "Plumbers, Glaziers & Painters",
      "entries": [
        {"name": "Nicholas Esther", "trade": "Plumber, Glazier & Painter", "notes": ""},
        {"name": "Nicholas John", "trade": "Plumber, Glazier & Painter", "notes": ""}
      ]
    },
    {
      "category": "Saddlers & Harness Makers",
      "entries": [
        {"name": "Brown Llewellin", "trade": "Saddler & Harness Maker", "notes": ""},
        {"name": "Griffiths George", "trade": "Saddler & Harness Maker", "notes": ""},
        {"name": "Morgan Samuel", "trade": "Saddler & Harness Maker", "notes": ""}
      ]
    },
    {
      "category": "Salt Merchants",
      "entries": [
        {"name": "Latch Joseph", "trade": "Salt Merchant", "notes": ""},
        {"name": "Williams Ann", "trade": "Salt Merchant", "notes": ""}
      ]
    },
    {
      "category": "Ship Chandlers & Builders",
      "entries": [
        {"name": "Jones William", "trade": "Ship Chandler", "notes": "Pillgwelly"},
        {"name": "Masterman Thomas", "trade": "Ship Chandler", "notes": "Pillgwelly"},
        {"name": "Johns Matthew & John", "trade": "Ship & Boat Builders", "notes": ""},
        {"name": "Cook & Turner", "trade": "Sail Makers", "notes": ""}
      ]
    },
    {
      "category": "Surgeons & Medical",
      "entries": [
        {"name": "Brewer William", "trade": "Surgeon", "notes": ""},
        {"name": "Davis Daniel Walter", "trade": "Surgeon", "notes": ""},
        {"name": "Hawkins James", "trade": "Surgeon", "notes": ""}
      ]
    },
    {
      "category": "Tailors & Drapers",
      "entries": [
        {"name": "Edwards Lewis", "trade": "Tailor & Draper", "notes": ""},
        {"name": "Morgan Morgan", "trade": "Tailor & Draper", "notes": ""},
        {"name": "Phillips Anthony", "trade": "Tailor & Draper", "notes": ""},
        {"name": "Roberts William", "trade": "Tailor & Draper", "notes": ""}
      ]
    },
    {
      "category": "Tallow Chandlers & Oilmen",
      "entries": [
        {"name": "Armitage John", "trade": "Tallow Chandler", "notes": ""},
        {"name": "Harrhy & Lewis", "trade": "Tallow Chandlers (& oilmen)", "notes": ""}
      ]
    },
    {
      "category": "Taverns & Public Houses",
      "entries": [
        {"name": "Blue Boar", "proprietor": "John Chessell", "trade": "Public House", "notes": ""},
        {"name": "Bush", "proprietor": "Evan Evans", "trade": "Public House", "notes": ""},
        {"name": "Bush & Britannia", "proprietor": "Wm. Williams", "trade": "Public House", "notes": ""},
        {"name": "Carpenters’ Arms", "proprietor": "Adam Williams", "trade": "Public House", "notes": ""},
        {"name": "Coach & Horses", "proprietor": "Thos. Harry", "trade": "Public House", "notes": ""},
        {"name": "Cross Keys", "proprietor": "Walter Kenear", "trade": "Public House", "notes": ""},
        {"name": "Crow", "proprietor": "Edward Thomas", "trade": "Public House", "notes": ""},
        {"name": "Freemasons’ Tavern", "proprietor": "John Kingson", "trade": "Public House", "notes": ""},
        {"name": "General Blucher", "proprietor": "Evan Morgan", "trade": "Public House", "notes": ""},
        {"name": "Globe", "proprietor": "Mary Gething", "trade": "Public House", "notes": ""},
        {"name": "Green Dragon", "proprietor": "David Davies", "trade": "Public House", "notes": ""},
        {"name": "Hope & Anchor", "proprietor": "Wm. Colcombe", "trade": "Public House", "notes": ""},
        {"name": "King’s Arms", "proprietor": "Wm. Rowland", "trade": "Public House", "notes": ""},
        {"name": "Market Boat", "proprietor": "Wm. Edmonds", "trade": "Public House", "notes": ""},
        {"name": "Noah’s Ark", "proprietor": "Evan Jones", "trade": "Public House", "notes": ""},
        {"name": "Old Bull", "proprietor": "Wm. Watkins", "trade": "Public House", "notes": ""},
        {"name": "Old Red Cow", "proprietor": "Sarah Batten", "trade": "Public House", "notes": ""},
        {"name": "Old Ship", "proprietor": "Mary Jenkins", "trade": "Public House", "notes": ""},
        {"name": "Punch House", "proprietor": "John Wells", "trade": "Public House", "notes": ""},
        {"name": "Red Cow", "proprietor": "David Francies", "trade": "Public House", "notes": ""},
        {"name": "Red Lion", "proprietor": "John Jones", "trade": "Public House", "notes": ""},
        {"name": "Royal Oak", "proprietor": "Wm. Roberts", "trade": "Public House", "notes": ""},
        {"name": "Salutation", "proprietor": "Richard Parry", "trade": "Public House", "notes": ""},
        {"name": "Ship & Castle", "proprietor": "William John", "trade": "Public House", "notes": ""},
        {"name": "Ship-a-Ground", "proprietor": "Adam Young", "trade": "Public House", "notes": ""},
        {"name": "Ship-a-Ground", "proprietor": "Samuel Coombs", "trade": "Public House", "notes": "Pillgwelly"},
        {"name": "Ship-on-Launch", "proprietor": "Catherine Jones", "trade": "Public House", "notes": ""},
        {"name": "Six Bells", "proprietor": "John Stephens", "trade": "Public House", "notes": ""},
        {"name": "Tredegar Arms", "proprietor": "T. Price", "trade": "Public House", "notes": "Pillgwelly"},
        {"name": "Tredegar Inn", "proprietor": "Thomas Ashmead", "trade": "Public House", "notes": ""},
        {"name": "Vulcan", "proprietor": "Richard Williams", "trade": "Public House", "notes": ""},
        {"name": "White Lion", "proprietor": "George Thomas", "trade": "Public House", "notes": ""}
      ]
    },
    {
      "category": "Timber Merchants",
      "entries": [
        {"name": "Batchelor Benjamin", "trade": "Timber Merchant", "notes": ""},
        {"name": "Bowcher & Watkins", "trade": "Timber Merchants (of Chepstow)", "notes": ""},
        {"name": "Harrhy David", "trade": "Timber Merchant (and deal)", "notes": ""},
        {"name": "Jones Henry", "trade": "Timber Merchant", "notes": ""},
        {"name": "Young John", "trade": "Timber Merchant", "notes": ""}
      ]
    },
    {
      "category": "Watch & Clock Makers",
      "entries": [
        {"name": "Frost William", "trade": "Watch & Clock Maker", "notes": ""},
        {"name": "Mills Thomas", "trade": "Watch & Clock Maker", "notes": ""},
        {"name": "Morris Philip", "trade": "Watch & Clock Maker", "notes": ""},
        {"name": "Williams Evan", "trade": "Watch & Clock Maker", "notes": ""}
      ]
    },
    {
      "category": "Wheelwrights",
      "entries": [
        {"name": "Lewis John", "trade": "Wheelwright", "notes": ""},
        {"name": "Moses John", "trade": "Wheelwright", "notes": ""}
      ]
    },
    {
      "category": "Wine & Spirit Merchants",
      "entries": [
        {"name": "Harrhy David", "trade": "Wine & Spirit Merchant", "notes": ""},
        {"name": "Jones & Roberts", "trade": "Wine & Spirit Merchants", "notes": ""},
        {"name": "Wall Maria", "trade": "Wine & Spirit Merchant", "notes": ""}
      ]
    },
    {
      "category": "Manufacturing, Shipping & Miscellaneous",
      "entries": [
        {"name": "Beedle & Russell", "trade": "Straw Hat Manufacturers", "notes": ""},
        {"name": "Blight Richd.", "trade": "Brazier & Tin-Plate Worker", "notes": ""},
        {"name": "Cook & Turner", "trade": "Sail Makers", "notes": ""},
        {"name": "Johns Matthew & John", "trade": "Ship & Boat Builders", "notes": ""},
        {"name": "Leigh George & Smith", "trade": "Tin-Plate Manufacturers (of Pontypool)", "notes": "Robert Gething, agent"},
        {"name": "Monmouthshire Canal Navigation Company", "trade": "Canal Company", "notes": "Thos. Cooke, agent"},
        {"name": "Portuguese Consul for Newport & Cardiff", "trade": "Consular Official", "notes": "Wm. Jones"},
        {"name": "Stamp Office", "trade": "Government Stamp Office", "notes": "William Williams, deputy distributer"},
        {"name": "Williams Thomas", "trade": "Rope Maker", "notes": ""}
      ]
    }
  ]
}

with open("data/early_directories/pigot_1822.json", "w") as f:
    json.dump(p1822, f, indent=2)

count = sum(len(s["entries"]) for s in p1822["sections"])
print(f"Generated pigot_1822.json with {len(p1822['sections'])} categories and {count} entries.")

# 1835 Pigot & Co.'s Directory
p1835 = {
  "year": 1835,
  "title": "Pigot & Co.’s National Commercial Directory for 1835",
  "county": "Monmouthshire",
  "town": "Newport, Caerleon & Suburbs",
  "narrative": "NEWPORT is an ancient market town, seaport, and borough, situated in the hundred of Wentlooge, 148 miles from London, 24 from Bristol, and 12 from Cardiff. It stands on the right bank of the river Usk, over which is an elegant stone bridge of five arches, built by David Edwards (son of the celebrated architect of Pontypridd). The town has grown with prodigious rapidity owing to the Monmouthshire Canal and Sirhowy Tramroad bringing down vast quantities of coal and iron from the hills. The population in 1801 was 1,423; in 1811, 3,025; in 1821, 4,001; and in 1831, 7,062 inhabitants (exclusive of Caerleon); these returns proving how rapidly the population has increased within a few years.\n\nCAERLEON is an ancient market town, in the parish of Llangattock, and hundred of Usk, three miles from Newport, seated on the Usk. This town was once the metropolis of Wales, and for extent next to London; it was then the third city in Britain, having an archbishop’s see from the establishment of Christianity in this island. In the time of the Romans it was their principal station; and, according to tradition, the renowned King Arthur here kept his court, and instituted that celebrated order of knighthood, styled 'the order of the round table.' The remains of several antiquities are still found in and around the place—such as a part of the wall that surrounded it, the site of a Roman amphitheatre, and part of a fosse; remains of Roman armour, coins, stone coffins, sepulchral stones, rings, &c. are often dug up here. The walls of Caerleon were built by the Romans with brick, and it is affirmed that they were three miles in circumference. There were also three churches, exclusive of the University, and many elegant structures, besides baths; it is said formerly to have extended to St. Julian’s, and was a place of considerable strength in the reign of Henry II; for the valiant Iorwerth ap Owen ap Caradock, lord of Caerleon, defended it a long time against the King’s forces, though at last vanquished and deprived of his seignorial territory.\n\nThe name of this ancient and interesting city signifies 'the fortress of Lleon upon Usk,' being so designated from an ancient British king; and not, as Camden states, who says its name is derived from the circumstance of a Roman legion being stationed here. The suburb still bears the classical appellation of ULTRA PONTEM. Giraldus Cambrensis, who, in the fourteenth century, wrote an account of Caerleon, says—'we still see, both within and without the walls, subterraneous buildings, aqueducts, vaulted caverns, and stoves so excellently contrived as to convey their heat through secret and imperceptible pores.'\n\nThe principal works here are for rolling iron into sheets, and coating them with tin; some of these are very extensive establishments. The places of worship are, one church, and a chapel each for baptists and Wesleyan methodists; the Rev. David Phillips is the present officiating minister of the church. The living of Llangattock is a vicarage, in the gift of the prebends of Llandaff. The free school here was founded and endowed, in 1724, by Charles Williams, Esq. for clothing and educating twenty-five boys, and the like number of girls. The other principal charity is an alms-house for aged widows. The weekly market is held on Thursday, and another every alternate Monday for cattle, sheep, horses, pigs, &c. There are four annual fairs, namely, the third Wednesday in February, May 1st, July 20th, and September 21st. The parish of Llangattock contained, in 1821, 1,360 inhabitants, and in 1831, 1,362; of which last number 1,071 were returned for Caerleon.\n\nPOST OFFICE, High street, NEWPORT.—George Griffiths, Post Master.—Letters from London, Bristol, &c. arrive every afternoon at a quarter past one, and are despatched every afternoon at a quarter before twelve.—Letters from Birmingham, Liverpool, Manchester, Chepstow, &c. arrive every afternoon at five minutes past twelve, and are despatched every afternoon at a quarter past one.—Letters from Abergavenny, Brecon, Pontypool, Usk, and Crickhowell arrive every forenoon at a quarter past eleven, and are despatched every afternoon at two.—Letters from South Wales arrive every day at five minutes before eleven, and are despatched every afternoon at half-past two.—Letters from Tredegar, &c. arrive every morning at half-past ten, and are despatched every afternoon at half-past two.\n\nPOST OFFICE, CAERLEON.—Esther Powell, Post Mistress.—Letters from London, Bristol, &c. arrive every afternoon at half-past two, and are despatched every forenoon at a quarter before eleven.—Letters from Abergavenny, Brecon, Pontypool, Usk, and Crickhowell arrive every forenoon at a quarter before eleven, and are despatched every afternoon at half-past two.",
  "nobility_gentry_clergy": [
    {"name": "Bateman Goulthourt, esq.", "residence": "Burtholy House", "notes": ""},
    {"name": "Butler John, esq.", "residence": "Caerleon", "notes": ""},
    {"name": "Byron Rev. Benjamin", "residence": "Pentonville", "notes": ""},
    {"name": "Cobb Mrs. Elizabeth", "residence": "Westgate st", "notes": ""},
    {"name": "Coles Rev. Jas.", "residence": "Llanvihangel Vedw", "notes": ""},
    {"name": "Evans Rev. James", "residence": "Pouthir", "notes": ""},
    {"name": "Fothergill Thomas, esq.", "residence": "Caerleon", "notes": ""},
    {"name": "Gillman Rev. Thomas", "residence": "Club row", "notes": ""},
    {"name": "Hall George, esq.", "residence": "Belmont", "notes": ""},
    {"name": "Homfray John, esq.", "residence": "Pillgwenlly", "notes": ""},
    {"name": "Howell Rev. Lewis", "residence": "Caerleon", "notes": ""},
    {"name": "Hughes Rev. D.", "residence": "Corn st", "notes": ""},
    {"name": "Isaacson Rev. Anthony Allet", "residence": "Commercial street", "notes": ""},
    {"name": "James John, jun. esq.", "residence": "Lansoar", "notes": ""},
    {"name": "Jenkins John, esq.", "residence": "Caerleon", "notes": ""},
    {"name": "Jones Rev. Daniel", "residence": "Caerleon", "notes": ""},
    {"name": "Jones Mr. Edmund", "residence": "Bullmore", "notes": ""},
    {"name": "Jones Rev. Hugh Wm.", "residence": "Charles st", "notes": ""},
    {"name": "Jones Mrs.", "residence": "Westgate st", "notes": ""},
    {"name": "Jones Mrs. Nannette", "residence": "Mount pleasant", "notes": ""},
    {"name": "Leyson Rev. John", "residence": "Bassalleg", "notes": ""},
    {"name": "Mackworth Major Digby", "residence": "Glenusk House", "notes": ""},
    {"name": "Miles Rev. William", "residence": "Commercial st", "notes": ""},
    {"name": "Monkhouse Mrs. Bridget", "residence": "Cwmbrws House", "notes": ""},
    {"name": "Morgan Sir Chas. G. bart.", "residence": "Tredegar House", "notes": "Lord of the Manor & Member of Parliament"},
    {"name": "Morgan Charles, esq.", "residence": "Ruperra", "notes": ""},
    {"name": "Morgan Miss Mary", "residence": "Caerleon", "notes": ""},
    {"name": "Phillips Rev. David", "residence": "Green meadow, Caerleon", "notes": ""},
    {"name": "Phillips Wm. esq.", "residence": "Whitson House", "notes": ""},
    {"name": "Portal Rev. Patrick", "residence": "Commercial st", "notes": ""},
    {"name": "Pritchard Jno. Haman, esq.", "residence": "Caerleon", "notes": ""},
    {"name": "Pullen Mrs.", "residence": "Caerleon", "notes": ""},
    {"name": "Pyne Mr. Robert", "residence": "Pillgwenlly", "notes": ""},
    {"name": "Roberts Rev. Richard", "residence": "Christchurch", "notes": ""},
    {"name": "Salusbury Sir Thomas Robert, bart.", "residence": "Llanwern", "notes": ""},
    {"name": "Smith Mr. Charles", "residence": "Stow hill", "notes": ""},
    {"name": "Thomas Jas. esq.", "residence": "Mount, St. Albans", "notes": ""}
  ],
  "sections": [
    {
      "category": "Academies & Schools",
      "entries": [
        {"name": "Abbott Edmund Charles", "street": "Stow hill", "trade": "Gentlemen’s Boarding School", "notes": ""},
        {"name": "Blue School", "street": "Caerleon", "trade": "Francis Bindon, master", "notes": ""},
        {"name": "British School", "street": "Old green", "trade": "Cornelius Evans, master", "notes": ""},
        {"name": "Davis Richd.", "street": "Stow hill", "trade": "Gentlemen's Boarding Academy", "notes": "Gentlemen's building"},
        {"name": "Grammar School", "street": "Stow hill", "trade": "Edmund Charles Abbott, master", "notes": ""},
        {"name": "King The Misses", "street": "Commercial st", "trade": "Ladies’ Boarding School", "notes": ""},
        {"name": "Hunt Catherine", "street": "Commercial st", "trade": "Ladies’ Boarding School", "notes": "Commercial street"},
        {"name": "Marshall Mary Ann", "street": "Stow hill", "trade": "Ladies’ Boarding School", "notes": ""},
        {"name": "Marshall Samuel", "street": "Stow hill", "trade": "Gentlemen’s Boarding School", "notes": ""},
        {"name": "Minifie Frances", "street": "Commercial st", "trade": "Ladies’ Boarding School", "notes": ""},
        {"name": "National School (Boys)", "street": "Caerleon", "trade": "John Tucker, master", "notes": ""},
        {"name": "National School (Girls)", "street": "Caerleon", "trade": "Roxanna Elvira Sims, mistress", "notes": ""},
        {"name": "National School (Girls)", "street": "Commercial st", "trade": "Ann Lynden, mistress", "notes": ""},
        {"name": "Nichols John & Son", "street": "Commercial st", "trade": "Gentlemen’s Boarding School", "notes": ""},
        {"name": "Reece Ann", "street": "Commercial st", "trade": "Day School", "notes": ""},
        {"name": "Thomas Misses", "street": "Stow hill", "trade": "Ladies’ Boarding School", "notes": ""},
        {"name": "Williams Elizabeth", "street": "Stow hill", "trade": "Day School", "notes": ""},
        {"name": "Williams Elizabeth & Ellen", "street": "Commercial st", "trade": "Day School", "notes": ""}
      ]
    },
    {
      "category": "Accountants & Agents",
      "entries": [
        {"name": "Downman Hugh Herbert", "street": "Commercial street", "trade": "Accountant", "notes": ""},
        {"name": "Jones Robert", "street": "Commercial street", "trade": "Accountant", "notes": ""},
        {"name": "Cadman James", "street": "Canal parade", "trade": "Agent (Mineral), Pentwyn Works", "notes": ""},
        {"name": "Cooke Thomas", "street": "Canal Co., High st", "trade": "Agent to Monmouthshire Canal Co.", "notes": ""},
        {"name": "Corner John", "street": "Skinner street", "trade": "Insurance & Commission Agent", "notes": ""},
        {"name": "Hillier Richard", "street": "Commercial street", "trade": "Commission Agent", "notes": ""},
        {"name": "Francis John", "street": "Commercial street", "trade": "Agent (Ale)", "notes": ""},
        {"name": "Jeffery George", "street": "Canal parade", "trade": "Agent to John Jones, esq.", "notes": ""},
        {"name": "Jones, Nicholas & Co.", "street": "Commercial street", "trade": "Commission Agents", "notes": ""},
        {"name": "Justice Frederick", "street": "Tredegar wharf", "trade": "Agent to Sir Chas. G. Morgan, bart.", "notes": ""},
        {"name": "Leigh Richard", "street": "Stow hill", "trade": "Agent (Commission &c.)", "notes": ""},
        {"name": "Morgan Charles Humberston", "street": "Commercial street", "trade": "Agent (Wine, &c.)", "notes": ""},
        {"name": "Nicholas Jacob Jenkins", "street": "Commercial street", "trade": "Second Agent to Sir C. G. Morgan, bart.", "notes": ""},
        {"name": "Nicholson Christopher", "street": "Brook Vale Works", "trade": "Agent (Mineral)", "notes": ""},
        {"name": "Richards James", "street": "Coalbrook Vale Works", "trade": "Agent (Mineral)", "notes": ""},
        {"name": "Stonehouse Christopher Henry & Co.", "street": "Skinner street", "trade": "Surveyors & Agents to Lloyd's", "notes": ""},
        {"name": "Wells & Wood", "street": "Skinner street", "trade": "Commission Agents", "notes": ""}
      ]
    },
    {
      "category": "Attorneys & Solicitors",
      "entries": [
        {"name": "Baron Morwent", "street": "Caerleon", "trade": "Attorney", "notes": ""},
        {"name": "Brewer John", "street": "Commercial st", "trade": "Attorney", "notes": ""},
        {"name": "Davies William", "street": "Corn st", "trade": "Attorney", "notes": ""},
        {"name": "Hawkins Henry", "street": "Commercial st", "trade": "Attorney", "notes": ""},
        {"name": "Phillips Thomas Jones", "street": "High st", "trade": "Attorney", "notes": ""},
        {"name": "Prothero Thomas", "street": "Westgate st", "trade": "Attorney", "notes": "Treasurer to the Newport & Caerleon turnpike trusts"},
        {"name": "Reece Richard Llewellin", "street": "High st", "trade": "Attorney", "notes": ""}
      ]
    },
    {
      "category": "Bankers",
      "entries": [
        {"name": "Monmouthshire & Glamorganshire Banking Co.", "street": "High st", "trade": "Bankers", "notes": "Draw upon London Joint Stock Bank"},
        {"name": "Williams & Co. (Newport Old Bank)", "street": "High st", "trade": "Bankers", "notes": "Draw upon Cocks, Biddulph & Co."}
      ]
    },
    {
      "category": "Blacksmiths & Anchor Smiths",
      "entries": [
        {"name": "Evans William", "street": "Pillgwenlly", "trade": "Anchor & Ship Smith", "notes": ""},
        {"name": "Griffiths William", "street": "Canal parade", "trade": "Blacksmith", "notes": ""},
        {"name": "Jones John", "street": "Canal parade", "trade": "Blacksmith", "notes": ""},
        {"name": "Tombs Daniel", "street": "Canal parade", "trade": "Blacksmith", "notes": ""}
      ]
    },
    {
      "category": "Booksellers, Printers & Stationers",
      "entries": [
        {"name": "Nicholas Edward", "street": "High st", "trade": "Printer, Bookseller & Stationer", "notes": ""},
        {"name": "Reed Samuel", "street": "High st", "trade": "Bookseller, Binder & Stationer", "notes": ""},
        {"name": "Webber John", "street": "High st", "trade": "Bookseller & Stationer", "notes": ""}
      ]
    },
    {
      "category": "Boot & Shoe Makers",
      "entries": [
        {"name": "Fletcher John", "street": "Commercial st", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Harry Edward", "street": "Commercial st", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Lewis James", "street": "Commercial st", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Lewis John", "street": "High st", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Morgan John", "street": "Commercial st", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Prosser John", "street": "High st", "trade": "Boot & Shoe Maker", "notes": ""},
        {"name": "Spear Joseph & James", "street": "High st", "trade": "Boot & Shoe Makers", "notes": ""}
      ]
    },
    {
      "category": "Brewers & Maltsters",
      "entries": [
        {"name": "Fothergill Thomas", "street": "Caerleon", "trade": "Brewer & Maltster", "notes": ""},
        {"name": "Oliver George", "street": "High st", "trade": "Brewer", "notes": ""},
        {"name": "Phillips Thomas Jones", "street": "High st", "trade": "Maltster", "notes": ""},
        {"name": "Williams John", "street": "Commercial st", "trade": "Maltster", "notes": ""}
      ]
    },
    {
      "category": "Builders, Carpenters & Masons",
      "entries": [
        {"name": "Batchelor Benjamin", "street": "Canal parade", "trade": "Builder", "notes": ""},
        {"name": "Edwards Edward", "street": "Commercial st", "trade": "Builder & Carpenter", "notes": ""},
        {"name": "Jones Samuel", "street": "High st", "trade": "Builder & Cabinet Maker", "notes": ""},
        {"name": "Morgan James", "street": "Commercial st", "trade": "Builder", "notes": ""},
        {"name": "Waters & Jones", "street": "Canal parade", "trade": "Builders", "notes": ""}
      ]
    },
    {
      "category": "Coal Merchants & Shippers",
      "entries": [
        {"name": "Blannin James", "street": "Pillgwenlly", "trade": "Coal Shipper", "notes": ""},
        {"name": "Brewer John", "street": "Pillgwenlly", "trade": "Coal Merchant", "notes": ""},
        {"name": "Farquhar Robert & Co.", "street": "Pillgwenlly", "trade": "Coal Shippers", "notes": "Pontypool Colliery"},
        {"name": "Gething Robert", "street": "Pillgwenlly", "trade": "Coal Shipper & Merchant", "notes": ""},
        {"name": "Jones Orlando", "street": "Pillgwenlly", "trade": "Coal Merchant", "notes": ""},
        {"name": "Jones William", "street": "Pillgwenlly", "trade": "Coal Merchant", "notes": ""},
        {"name": "Leman James", "street": "Pillgwenlly", "trade": "Coal Merchant", "notes": ""},
        {"name": "Morgan Samuel", "street": "Pillgwenlly", "trade": "Coal Shipper", "notes": ""},
        {"name": "Penmain Coal Co.", "street": "Pillgwenlly", "trade": "Coal Shippers", "notes": ""},
        {"name": "Powell Thomas", "street": "Pillgwenlly", "trade": "Coal Shipper & Proprietor", "notes": "The renowned Thomas Powell, colliery owner"},
        {"name": "Prothero Thomas", "street": "Pillgwenlly", "trade": "Coal Shipper", "notes": ""},
        {"name": "Tredegar Iron & Coal Co.", "street": "Tredegar wharf", "trade": "Coal Shippers & Iron Masters", "notes": ""},
        {"name": "Webb Thomas", "street": "Pillgwenlly", "trade": "Coal Merchant", "notes": ""}
      ]
    },
    {
      "category": "Inns, Hotels & Commercial Houses",
      "entries": [
        {"name": "King’s Head Hotel", "proprietor": "John Morgan", "street": "High st", "trade": "Hotel & Posting House", "notes": "Commercial and family hotel"},
        {"name": "West Gate Hotel", "proprietor": "Ann Iggulden", "street": "Westgate st", "trade": "Hotel & Posting House", "notes": "Historic principal coaching inn"},
        {"name": "Parrot Inn", "proprietor": "Morgan Morgan", "street": "Commercial st", "trade": "Inn & Commercial Tavern", "notes": ""},
        {"name": "Tredegar Arms", "proprietor": "Wm. Phillips", "street": "Pillgwenlly", "trade": "Commercial Hotel", "notes": "Pillgwenlly harbour inn"},
        {"name": "Bush Inn", "proprietor": "Evan Evans", "street": "Commercial st", "trade": "Inn", "notes": ""},
        {"name": "Carpenters’ Arms", "proprietor": "Adam Williams", "street": "High st", "trade": "Public House", "notes": ""},
        {"name": "Coach & Horses", "proprietor": "Thomas Harry", "street": "Charles st", "trade": "Public House", "notes": ""},
        {"name": "Cross Keys", "proprietor": "Walter Kenear", "street": "Market st", "trade": "Public House", "notes": ""},
        {"name": "Green Dragon", "proprietor": "David Davies", "street": "Commercial st", "trade": "Public House", "notes": ""},
        {"name": "Hope & Anchor", "proprietor": "William Colcombe", "street": "Canal parade", "trade": "Public House", "notes": ""},
        {"name": "Noah’s Ark", "proprietor": "Evan Jones", "street": "Commercial st", "trade": "Public House", "notes": ""},
        {"name": "Old Bull", "proprietor": "William Watkins", "street": "High st", "trade": "Public House", "notes": ""},
        {"name": "Old Ship", "proprietor": "Mary Jenkins", "trade": "Public House", "street": "Canal parade", "notes": ""},
        {"name": "Punch House", "proprietor": "John Wells", "street": "Canal parade", "trade": "Public House", "notes": ""},
        {"name": "Red Lion", "proprietor": "John Jones", "street": "High st", "trade": "Public House", "notes": ""},
        {"name": "Royal Oak", "proprietor": "Wm. Roberts", "street": "High st", "trade": "Public House", "notes": ""},
        {"name": "Salutation", "proprietor": "Richard Parry", "street": "Commercial st", "trade": "Public House", "notes": ""},
        {"name": "Ship & Castle", "proprietor": "William John", "street": "Commercial st", "trade": "Public House", "notes": ""},
        {"name": "Ship-a-Ground", "proprietor": "Adam Young", "street": "Pillgwenlly", "trade": "Public House", "notes": ""},
        {"name": "White Lion", "proprietor": "George Thomas", "street": "High st", "trade": "Public House", "notes": ""}
      ]
    },
    {
      "category": "Iron Masters & Works",
      "entries": [
        {"name": "Blaenavon Iron Co.", "street": "Canal parade", "trade": "Iron Works", "notes": "Edmonds & Co., agents"},
        {"name": "Clydach Iron Co.", "street": "Wharf", "trade": "Iron Works", "notes": "Harford, Davies & Co."},
        {"name": "Ebbw Vale Iron Works", "street": "Canal parade", "trade": "Iron Works", "notes": "Harford, Davies & Co."},
        {"name": "Nantyglo Iron Works", "street": "Canal parade", "trade": "Iron Works", "notes": "Messrs. Bailey, proprietors"},
        {"name": "Pentwyn Iron Works", "street": "Canal parade", "trade": "Iron Works", "notes": "Hunt, Phillips & Co."},
        {"name": "Pontypool Iron Works", "street": "Canal parade", "trade": "Iron Works", "notes": "Capel Hanbury Leigh, esq."},
        {"name": "Sirhowy Iron Works", "street": "Wharf", "trade": "Iron Works", "notes": "Harford, Davies & Co."},
        {"name": "Tredegar Iron Works", "street": "Tredegar wharf", "trade": "Iron Masters", "notes": "Homfray, Thompson & Forman"},
        {"name": "Varteg Iron Works", "street": "Canal parade", "trade": "Iron Works", "notes": "Kenrick & Co."}
      ]
    },
    {
      "category": "Linen & Woollen Drapers",
      "entries": [
        {"name": "Frost John", "street": "High st", "trade": "Linen & Woollen Draper", "notes": "Later Mayor of Newport & prominent Chartist"},
        {"name": "Lowe William Henry", "street": "High st", "trade": "Linen & Woollen Draper", "notes": ""},
        {"name": "Rogers Richard", "street": "Commercial st", "trade": "Draper", "notes": ""},
        {"name": "Wetherill Thomas", "street": "Commercial st", "trade": "Draper & Milliner", "notes": ""}
      ]
    },
    {
      "category": "Ship Builders & Chandlers",
      "entries": [
        {"name": "Batchelor Benjamin", "street": "Canal parade", "trade": "Ship Builder & Timber Merchant", "notes": ""},
        {"name": "Cook & Turner", "street": "Canal parade", "trade": "Sail Makers & Riggers", "notes": ""},
        {"name": "Johns Matthew & John", "street": "Canal parade", "trade": "Ship & Boat Builders", "notes": ""},
        {"name": "Jones William", "street": "Pillgwenlly", "trade": "Ship Chandler & Broker", "notes": ""},
        {"name": "Masterman Thomas", "street": "Pillgwenlly", "trade": "Ship Chandler", "notes": ""},
        {"name": "Stonehouse Christopher Henry", "street": "Skinner street", "trade": "Ship Broker & Lloyd's Agent", "notes": ""}
      ]
    },
    {
      "category": "Surgeons & Medical",
      "entries": [
        {"name": "Brewer William", "street": "Commercial st", "trade": "Surgeon", "notes": ""},
        {"name": "Davis Daniel Walter", "street": "Corn st", "trade": "Surgeon", "notes": ""},
        {"name": "Hawkins James", "street": "Commercial st", "trade": "Surgeon", "notes": ""},
        {"name": "Morgan William", "street": "High st", "trade": "Surgeon", "notes": ""}
      ]
    },
    {
      "category": "Wine & Spirit Merchants",
      "entries": [
        {"name": "Harrhy David", "street": "High st", "trade": "Wine & Spirit Merchant", "notes": ""},
        {"name": "Jones & Roberts", "street": "Commercial st", "trade": "Wine & Spirit Merchants", "notes": ""},
        {"name": "Wall Maria", "street": "High st", "trade": "Wine & Spirit Merchant", "notes": ""}
      ]
    }
  ]
}

with open("data/early_directories/pigot_1835.json", "w") as f:
    json.dump(p1835, f, indent=2)

print("Generated pigot_1835.json successfully.")
