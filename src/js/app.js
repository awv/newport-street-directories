let directoryData = [];
let uniqueStreets = [];
let selectedIndex = -1;

    // Search Results State
    let currentSearchResults = { all: [], people: [], occupations: [], streets: [] };
    let currentSearchTab = 'all';
    let currentPage = 1;
    const PAGE_SIZE = 25;

    // Full Forename Abbreviation Lookup Dictionary
    const FORENAME_MAP = {
      "Ab": "Abraham", "Abig": "Abigail", "Abr": "Abraham", "Abra": "Abraham",
      "Ad": "Adelard", "Adr": "Adrian", "Agn": "Agnes", "Alb": "Albert", "Albt": "Albert",
      "Alc": "Alice", "Alex": "Alexander", "Ale": "Alethea", "Alf": "Alfred", "Alfd": "Alfred",
      "Alph": "Alphonse", "Am": "Amanda", "Amb": "Ambrose", "And": "Andrew", "Andw": "Andrew",
      "Ang": "Angeline", "An": "Anne", "Ani": "Annie", "Ant": "Antoine", "Anth": "Anthony",
      "Anthy": "Anthony", "Arch": "Archibald", "Archd": "Archibald", "Art": "Arthur",
      "Arth": "Arthur", "Aud": "Audrey", "Aug": "August", "Balt": "Balthazar",
      "Barb": "Barbara", "Bart": "Bartholomew", "Barth": "Barthelemy", "Bea": "Beatrice",
      "Ben": "Benjamin", "Benj": "Benjamin", "Bern": "Bernard", "Brid": "Bridget",
      "Car": "Caroline", "Cath": "Catherine", "Cathne": "Catherine", "Charlt": "Charlotte",
      "Chals": "Charles", "Chas": "Charles", "Chs": "Charles", "Chris": "Christopher",
      "Clem": "Clement", "Clif": "Clifford", "Clifd": "Clifford", "Cons": "Constance",
      "Const": "Constance", "Corn": "Cornelius", "Cor’us": "Cornelius", "Cuthbt": "Cuthbert",
      "Dan": "Daniel", "Danl": "Daniel", "Dav": "David", "Deb": "Deborah",
      "Delbt": "Delbert", "Den": "Dennis", "Dom": "Dominique", "Don": "Donald",
      "Dor": "Dorothy", "Doug": "Douglas", "Dy": "Dorothy", "Eben": "Ebenezer",
      "Ed": "Edward", "Edm": "Edmund", "Edw": "Edward", "Elis": "Elisabeth",
      "Eliz": "Elizabeth", "Eliza": "Elizabeth", "Elizh": "Elizabeth", "Elizth": "Elizabeth",
      "Elnr": "Eleanor", "Em": "Emma", "Eml": "Emily", "Ern": "Ernest",
      "Esth": "Esther", "Etne": "Etienne", "Euc": "Euclide", "Eug": "Eugene",
      "Eugne": "Eugene", "Eus": "Eustace", "Ezek": "Ezekiel", "Fel": "Felicite",
      "Ferd": "Ferdinand", "Fern": "Fernand", "Flo": "Florence", "Flor": "Florence",
      "Fra": "Francis", "Fran": "Frances", "Fred": "Frederick", "Fredk": "Frederick",
      "Fs": "Francis", "Frs": "Francis", "Frs. X": "François-Xavier", "Gab": "Gabrielle",
      "Gen": "Genevieve", "Geo": "George", "Geof": "Geoffrey", "Ger": "Gerald",
      "Germ": "Germaine", "Gert": "Gertrude", "Gilbt": "Gilbert", "Godf": "Godfrey",
      "Graz": "Graziella", "Grif": "Griffith", "Gul": "William", "Guliel": "William",
      "Gwen": "Gwendolyn", "Han": "Hannah", "Har": "Harold", "Hel": "Helen",
      "Hen": "Henry", "Henr": "Henriette", "Hep": "Hephzibah", "Herb": "Herbert",
      "Herbt": "Herbert", "Hest": "Hester", "Hon": "Honour", "Hub": "Hubert",
      "Hubt": "Hubert", "Hum": "Humphrey", "Humy": "Humphrey", "Hy": "Henry",
      "Ioh": "John", "Ir": "Irene", "Isab": "Isabel", "Isb": "Isabel", "Ja": "James",
      "Jabus": "James", "Jac": "James", "Jacq": "Jacques", "J. Bte": "Jean-Baptiste",
      "Jas": "James", "Jean": "Jean", "Jer": "Jeremiah", "Jere": "Jeremiah",
      "Jerh": "Jeremiah", "Jermh": "Jeremiah", "Jn": "John", "Jne": "Jeanne",
      "Jno": "John", "Jnthn": "Jonathan", "Jon": "Jonathan", "Jone": "Joan",
      "Jos": "Joseph", "Josh": "Joshua", "Jro": "Jerome", "Jsph": "Joseph",
      "Jud": "Judith", "Jul": "Julian", "Kath": "Katherine", "Ken": "Kenneth",
      "Lan": "Lancelot", "Lau": "Laurence", "Lawr": "Lawrence", "Len": "Leonard",
      "Leo": "Leopold", "Leon": "Leonard", "Let": "Letitia", "Ls": "Louis",
      "Lse": "Louise", "Luc": "Lucian", "Lyd": "Lydia", "Mad": "Madeleine",
      "Marc": "Marcelline", "Marg": "Margaret", "Margt": "Margaret", "Margy": "Margery",
      "Marm": "Marmaduke", "Mart": "Martha", "Mat": "Matthew", "Math": "Mathias",
      "Mathw": "Matthew", "Matt": "Matthew", "Mau": "Maurice", "Mgt": "Margaret",
      "Mic": "Michael", "Mich": "Michael", "Michl": "Michael", "Mill": "Millicent",
      "My": "Mary", "Nap": "Napoleon", "Nar": "Narcisse", "Nath": "Nathaniel",
      "Nathl": "Nathaniel", "Naz": "Nazaire", "Neh": "Nehemiah", "Nic": "Nicholas",
      "Nich": "Nicholas", "Nicho": "Nicholas", "Nichs": "Nicholas", "Ns": "Nicholas",
      "Oct": "Octave", "Ol": "Oliver", "Pama": "Pamelia", "Pat": "Patrick",
      "Patk": "Patrick", "Pen": "Penelope", "Pet": "Peter", "Ph": "Phillip",
      "Phil": "Phillip", "Phin": "Phineas", "Phyl": "Phyllis", "Pre": "Pierre",
      "Prisc": "Priscilla", "Pru": "Prudence", "Rach": "Rachel", "Ray": "Raymond",
      "Rayd": "Raymond", "Reb": "Rebecca", "Reba": "Rebecca", "Reg": "Reginald",
      "Regd": "Reginald", "Ric": "Richard", "Rich": "Richard", "Richd": "Richard",
      "Richdus": "Richard", "Robt": "Robert", "Rodk": "Roderick", "Rog": "Roger",
      "Rol": "Roland", "Ron": "Ronald", "Rowl": "Rowland", "Rph": "Ralph",
      "Sam": "Samuel", "Saml": "Samuel", "Sar": "Sarah", "Sid": "Sidney",
      "Silv": "Sylvester", "Sim": "Simon", "Sol": "Solomon", "Stan": "Stanley",
      "Steph": "Stephen", "Sus": "Susan", "Susna": "Susannah", "Suz": "Suzanne",
      "Syd": "Sydney", "Tam": "Thomasin", "Teles": "Telesphore", "Theo": "Theodore",
      "Ther": "Therese", "Tho": "Thomas", "Thos": "Thomas", "Ths": "Thomas",
      "Tim": "Timothy", "Tous": "Toussaint", "Tristm": "Tristram", "Urs": "Ursula",
      "Val": "Valentine", "Vic": "Victor", "Vinc": "Vincent", "Virg": "Virginia",
      "Walt": "Walter", "Wilf": "Wilfred", "Wilfd": "Wilfred", "Wm": "William",
      "Xpher": "Christopher", "Xpr": "Christopher", "Xtianus": "Christian",
      "Xtopherus": "Christopher", "Zach": "Zachariah"
    };

    function expandForename(forename) {
      if (!forename) return '';
      return forename.split(' ').map(word => {
        const cleanWord = word.replace(/\.$/, '').trim();
        if (FORENAME_MAP[cleanWord]) return FORENAME_MAP[cleanWord];
        return word;
      }).join(' ');
    }

    const cleanStr = (s) => {
      if (!s) return '';
      return String(s)
        .replace(/^"|"$/g, '')
        .replace(/,\s*[a-zA-Z0-9\s]+\b/g, '')
        .toLowerCase()
        .replace(/\.[a-z]$/g, '')
        .replace(/\brd\b\.?/g, 'road')
        .replace(/\bst\b\.?/g, 'street')
        .replace(/\bave\b\.?/g, 'avenue')
        .replace(/\bter\b\.?/g, 'terrace')
        .replace(/\bpl\b\.?/g, 'place')
        .replace(/\bsq\b\.?/g, 'square')
        .replace(/\(the\s+/g, '(')
        .replace(/[^a-z0-9]/g, '');
    };

    function formatStreetName(name) {
      if (!name) return '';
      let clean = name.replace(/[-_]+/g, ' ').trim();
      return clean.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
    }

    const NON_TRADES_REGEX = /^(mrs\.?|miss\.?|mr\.?|thos\.?|jas\.?|wm\.?|saml\.?|john|geo\.?|chas\.?|hy\.?|richd\.?|harry|ernest|fredk\.?|arthur|edwd\.?|walt\.?|david|danl\.?|benj\.?|stepn\.?|iss e|ltd\.?|limited|co\.?|& co\.?|co\.? ltd\.?|ld\.?|henry|joseph|albert|reginald|harold|alfred|frank|edward|herbert|edwin|fred|norman|ivor|stanley|leslie|sidney|horace|edgar|lewis|percy|wilfred|bernard|eric|clifford|trevor|return\.?|junr?\.?|&|&c|etc|\{.*\}|;;;)$/i;

    function getTradeOverrides() {
      try {
        return JSON.parse(localStorage.getItem('trade_overrides') || '{}');
      } catch (e) {
        return {};
      }
    }

    function cleanOccupation(trade) {
      if (!trade || trade.trim() === '' || trade === '-') return 'Residence / Private';

      let clean = trade.trim();
      const overrides = getTradeOverrides();

      // Check custom trade overrides first
      if (overrides[clean.toLowerCase()]) {
        return overrides[clean.toLowerCase()];
      }

      // Catch JSON block spills (e.g. Butcher"", ""Business / Entity"":""..."", Outfitter And Pawnbroker...)
      if (/\{|""|Business \/ Entity|Layout \/ Notes|Forenames|Surname/i.test(clean)) {
        if (/butcher/i.test(clean)) return 'Butcher';
        if (/outfitter/i.test(clean)) return 'Outfitter';
        if (/pawnbroker/i.test(clean)) return 'Pawnbroker';
        return 'Residence / Private';
      }

      // Catch Bengali or non-ASCII OCR artifacts (e.g. "ভিন")
      if (/[\u0980-\u09FF\u0600-\u06FF\u0400-\u04FF\u4E00-\u9FFF]/.test(clean)) {
        return 'Residence / Private';
      }

      // Catch year-only spills in parentheses or raw (e.g. "(1910)", "1910", ". S")
      if (/^\(?\d{4}\)?$/i.test(clean) || /^\.\s*[a-z]$/i.test(clean)) {
        return 'Residence / Private';
      }

      // Catch professional qualifications / engineering suffixes
      if (/^m\.?i\.?c\.?e\.?/i.test(clean) || /^r\.?c\.?s\.?/i.test(clean)) {
        if (/civ\.?\s*eng/i.test(clean) || /eng/i.test(clean)) return 'Civil Engineer';
        if (/surg|dentist/i.test(clean)) return 'Dental Surgeon';
        return 'Civil Engineer';
      }

      // Catch long multi-line advertisement spills (e.g. "India Rubber, Gutta Percha...", "Guest, Keen & Nettlefolds...", "Colliery Proprietors...", "Al Exporters...")
      if (/gutta percha|hose packings|steamship and colliery furnishers|imperial mills|colliery proprietors|agents for the united national/i.test(clean)) {
        if (/rubber|gutta percha/i.test(clean)) return 'India Rubber & Gutta Percha Manufacturers';
        if (/mills|nettlefolds/i.test(clean)) return 'Iron & Steel Manufacturers';
        if (/colliery|coal/i.test(clean)) return 'Colliery Proprietors & Coal Exporters';
        return 'Commercial Business';
      }

      // Catch Waypoints, Address Spills, Flat numbers, Phone numbers, & Non-trade OCR spills
      if (
        /^(here is|here are|from\s+\d+|from\s+[a-z]+|\(?the roundabout\)?|\(?flat\s+\d+.*?\)?)/i.test(clean) ||
        /^(tel\.?|telephone|newport\s+\d+|\d+\s*\(after|\d+[a-z]?,?\s*workers)/i.test(clean) ||
        /^(do\.?|ditto|[-—_\|\\\[\]\{\}\.\,\&\;\:\?\!]+|&c|etc|\(?return\)?\.?|;;;)$/i.test(clean) ||
        /^(ltd\.?|co\.?|& co\.?|co\.?\s+ltd\.?|ltd\.?,\s*ltd|ltd\.?,\s*co\.?|gas\s+co|way\s+co\.?'?s?\s*office|1st\s+floor|2nd\s+floor|3rd\s+floor)$/i.test(clean) ||
        /^(&|\*|are|for|de|en|et|si|tai|vw|wks|rd|to\s+\d+\s+unbuilt|\(3\)|p\.o\.?|& m|& b|and at cardiff.*)$/i.test(clean) ||
        NON_TRADES_REGEX.test(clean)
      ) {
        return 'Residence / Private';
      }

      // Filter house/villa/building names left in trade column (e.g., "The Woodlands", "Norwood", "Eversley", "Rosetta", "Brynholme", "Gasworks", "Woolmer")
      if (
        /^(the\s+woodlands|norwood|eversley|rosetta|brynholme|gasworks|woolmer)$/i.test(clean) ||
        /^(bryn|villas?|cottage|house|lodge|manor|hall|court|view|terrace|gardens)\b/i.test(clean)
      ) {
        return 'Residence / Private';
      }

      // Handle "do. [Trade]" or "ditto [Trade]" patterns
      clean = clean.replace(/^(?:\d+\s+)?(?:do\.?|ditto)\s*[\.,]*\s*(?:\[(.*?)\]|(.*?))$/i, (m, g1, g2) => (g1 || g2 || '').trim());
      clean = clean.replace(/^[-—_\|,\s]+/, '').replace(/[-—_\|,\s]+$/, '').trim();

      // Strip house numbers and address prefixes (e.g. "20-24, Boot Repairer" -> "Boot Repairer", "52, Labourer" -> "Labourer", "Engrocer, 19 Foster F. J. Greengrocer")
      clean = clean
        .replace(/^\(from\s+\d+[^)]*\)\s*/i, '')
        .replace(/^\[?(\d+[-\d]*[a-z]?),?\s*/i, '')
        .replace(/^\d+[a-z]?,\s*/i, '')
        .replace(/\s+\d+[a-z]?$/i, '')
        .replace(/^\[/g, '')
        .replace(/\]$/g, '')
        .replace(/^[a-z]+,\s*\d+\s+[a-z\s\.,']+/i, '')
        .trim();

      // Strip person name spills and company spills preceding trades
      clean = clean
        .replace(/^[a-z\s\.,'\-]+\b(mrs|mr|miss)\b.*?,?\s*/i, '')
        .replace(/^[a-z\s\.,'\-]+\b(and|&)\s+co\.?'?s?\s+(offices|works|stores|yard)\s*,?\s*/i, '')
        .replace(/^[a-z0-9\s\.,'&\-]+\b(co\.?|ltd\.?|& co\.?)\s*,?\s*(land agents|surveyors|auctioneers|shipping agents|steam\s*ship|coal exporters|brickworks|milliners|iron|draper)/i, '$2')
        .replace(/^[a-z\s\.,'\-]+,?\s*(mar\.?\s*eng'?n?r|eng'?r|eng'?n?r)/i, '$1');

      // De-duplicate concatenated OCR phrases (e.g. "Milliners, Ltd., Milliners" -> "Milliners", "Baby Linen... Outfitters, Ltd., Baby Linen..." -> "Baby Linen & Childrens Outfitters", "Brewers, Ltd." -> "Brewers")
      clean = clean.replace(/^([^,\-]+?)\s*[\,;\—\-].*?\b\1\b/i, '$1').trim();

      // Clean leading & trailing company suffixes
      clean = clean
        .replace(/^(ltd\.?|co\.?|& co\.?|& co\.?,?\s*ltd\.?|and co\.?)\s*,?\s*/i, '')
        .replace(/[\,;\s]+(ltd\.?|co\.?|& co\.?|co\.?\s+ltd\.?)$/i, '')
        .trim();

      if (!clean || clean === '-' || clean === '—' || /^(ltd\.?|co\.?|& co\.?|&|and)$/i.test(clean) || NON_TRADES_REGEX.test(clean)) {
        return 'Residence / Private';
      }

      // Clean trailing ", &c" / ", etc" / "(return)" / Phone number suffixes / Ditto fragments
      clean = clean
        .replace(/[\,;\s]+(?:&c|etc)\.?$/i, '')
        .replace(/\s*\(\s*return\s*\)\.?$/i, '')
        .replace(/\s*\(\s*tel\.?\s*\d+.*?\)$/i, '')
        .replace(/\s+ditto$/i, '')
        .trim();

      // Clean municipal address spills & institution fragment lines
      if (
        /^(county borough of|council offices|home for the aged|home for aged|aged \(men\)|aged \(females\))/i.test(clean) ||
        /^(independent order of|adult education|british steel corporation|engineering & foundry)/i.test(clean)
      ) {
        if (/county borough of/i.test(clean)) return 'Municipal / Council Office';
        if (/home for/i.test(clean) || /aged \(/i.test(clean)) return 'Care Home / Residential Home';
        if (/independent order/i.test(clean)) return 'Friendly Society / Lodge';
        if (/adult education/i.test(clean)) return 'Educational Institution';
        if (/british steel/i.test(clean)) return 'Steel Works / Office';
        if (/engineering & foundry/i.test(clean)) return 'Engineering & Foundry';
      }

      // Handle School institutional titles
      if (/school|junior high|senior high|grammar school|convent school/i.test(clean)) {
        return 'School / Educational Institution';
      }

      // Specific multi-line commercial consolidations & compound expansions
      if (/^dkr$/i.test(clean)) return 'Docker';
      if (/^eng\.?\s*du'?vr$/i.test(clean)) return 'Engine Driver';
      if (/^m'?sion\s*agt$/i.test(clean)) return 'Commission Agent';
      if (/^m\.?b\.?\s*do$/i.test(clean)) return 'Physician & Surgeon';
      if (/^house\s*agt$/i.test(clean)) return 'House Agent';
      if (/^wol\s*mcht$/i.test(clean)) return 'Wool Merchant';
      if (/^min\.?\s*eng$/i.test(clean)) return 'Mining Engineer';
      if (/^engr\s*&\s*mer$/i.test(clean)) return 'Engineer & Merchant';
      if (/^eng\.?,\s*surg\.?\s*dentist$/i.test(clean)) return 'Dental Surgeon';
      if (/^l\.?d\.?s\.?,?\s*r\.?c\.?s\.?/i.test(clean)) return 'Dental Surgeon';
      if (/^wgn$/i.test(clean)) return 'Wagon Repairer';
      if (/^dgr$/i.test(clean)) return 'Dredger';
      if (/bootmaker/i.test(clean)) return 'Bootmaker';
      if (/bakers?.*confection/i.test(clean)) return 'Baker & Confectioner';
      if (/dispensing chemist/i.test(clean)) return 'Chemist';
      if (/potato mer/i.test(clean)) return 'Potato Merchant';
      if (/provision mer/i.test(clean)) return 'Provision Merchant';
      if (/builders?.*merchant/i.test(clean)) return 'Builders Merchant';
      if (/china.*glass/i.test(clean)) return 'China & Glass Merchant';
      if (/consulting eng/i.test(clean)) return 'Consulting Engineer';
      if (/newsagent.*stationer/i.test(clean)) return 'Newsagent & Stationer';
      if (/surveyor.*estate agent/i.test(clean)) return 'Estate Agent & Surveyor';
      if (/scrap.*metal/i.test(clean)) return 'Scrap Metal Merchant';
      if (/john ambulance/i.test(clean)) return 'St. John Ambulance Hall';

      clean = clean
        .replace(/\bg[\.\s]*w[\.\s]*r[\.\s]*/gi, 'G.W.R. ')
        .replace(/G\.W\.R\.\s*[\.,]+/gi, 'G.W.R. ')
        .replace(/\s+/g, ' ')
        .trim()
        .replace(/G\.W\.R\.\s*$/gi, 'G.W.R.')
        .replace(/\bgov\.?\s+offcl\b/gi, 'Government Official')
        .replace(/\bdk\s+police\b/gi, 'Dock Police')
        .replace(/\bldg\s+ho\b/gi, 'Lodging House')
        .replace(/\bdrapers\s+collctr\b/gi, 'Drapers Collector')
        .replace(/\bgas\s+inspct\b/gi, 'Gas Inspector')
        .replace(/\bblrmr\b/gi, 'Boilermaker')
        .replace(/\bcustom\s+offr\b/gi, 'Custom Officer')
        .replace(/\bglass\s+(wrkr|wk)\b/gi, 'Glass Worker')
        .replace(/\bice\s+cream\s+vendr\b/gi, 'Ice Cream Vendor')
        .replace(/\bcoal\s+tipr\b/gi, 'Coal Tipper')
        .replace(/\bdentst\b/gi, 'Dentist')
        .replace(/\bbus\s+drvi\b/gi, 'Bus Driver')
        .replace(/\bwagon\s+rp\b/gi, 'Wagon Repairer')
        .replace(/\b(electcn|electrn|elect|elct)\b/gi, 'Electrician')
        .replace(/\bflour\s+packr\b/gi, 'Flour Packer')
        .replace(/\broad\s+swp\b/gi, 'Road Sweeper')
        .replace(/\b(ironwor|ironwrkr|ironworkr|iworker|irn\s+worker)\b/gi, 'Ironworker')
        .replace(/\bbuilding\s+contr\s*&\s*engnrs\b/gi, 'Building Contractors and Engineers')
        .replace(/\bsales\s+drvr\b/gi, 'Sales Driver')
        .replace(/\btbeworker\b/gi, 'Tubeworker')
        .replace(/\bshoe\s+repr\b/gi, 'Shoe Repairer')
        .replace(/\bsteehvorkr\b/gi, 'Steelworker')
        .replace(/\bcrane\s+dr\b/gi, 'Crane Driver')
        .replace(/\belec\s+engineer\b/gi, 'Electrical Engineer')
        .replace(/\bstl\s+worker\b/gi, 'Steel Worker')
        .replace(/\bmotor\s+(drvr|dr)\b/gi, 'Motor Driver')
        .replace(/\bins\.?\s*agt\.?\b/gi, 'Insurance Agent')
        .replace(/\binsur\.?\s*agent\b/gi, 'Insurance Agent')
        .replace(/\bins\s+mercht?\b/gi, 'Insurance Merchant')
        .replace(/\bcoal\s+mercht?\b/gi, 'Coal Merchant')
        .replace(/\bcoal\s+mer\b/gi, 'Coal Merchant')
        .replace(/\bpostmn\b/gi, 'Postman')
        .replace(/\bcivil\s+serv(t|nt)\b/gi, 'Civil Servant')
        .replace(/\bdk\s+worker\b/gi, 'Dock Worker')
        .replace(/\btrmr\b/gi, 'Trimmer')
        .replace(/\bbricklayr\b/gi, 'Bricklayer')
        .replace(/\bsupt\.?\b/gi, 'Superintendent')
        .replace(/\bupholstr\b/gi, 'Upholsterer')
        .replace(/\bloco\s+driver\b/gi, 'Locomotive Driver')
        .replace(/\bclrk\b/gi, 'Clerk')
        .replace(/\b(steelworkr|steehvorkr|stlwrkr)\b/gi, 'Steelworker')
        .replace(/\bship\s+brkr\b/gi, 'Ship Broker')
        .replace(/\bfitters\s+hlpr\b/gi, 'Fitters Helper')
        .replace(/\bmarbl\s+polshr\b/gi, 'Marble Polisher')
        .replace(/\bcab\s+proprtr\b/gi, 'Cab Proprietor')
        .replace(/\bmonu\.?\s+mason\b/gi, 'Monumental Mason')
        .replace(/\brailwymn\b/gi, 'Railwayman')
        .replace(/\brly\s+foreman\b/gi, 'Railway Foreman')
        .replace(/\brly\s+inspt\b/gi, 'Railway Inspector')
        .replace(/\btram\s+inspt\b/gi, 'Tram Inspector')
        .replace(/\binspt\b/gi, 'Inspector')
        .replace(/\bironw6rker\b/gi, 'Ironworker')
        .replace(/\bgeneral\s+grocr\b/gi, 'General Grocer')
        .replace(/\blaborr\b/gi, 'Labourer')
        .replace(/\bpier\s+mastr\b/gi, 'Pier Master')
        .replace(/\bhouse\s+fur\b/gi, 'House Furnisher')
        .replace(/\bhatter\s*,\s*,\s*etc\b/gi, 'Hatter, etc.')
        .replace(/\bboot\s+manuftrs\b/gi, 'Boot Manufacturers')
        .replace(/\bphotogrpr\b/gi, 'Photographer')
        .replace(/\bmotormn\b/gi, 'Motorman')
        .replace(/\btug\s+drvr\b/gi, 'Tug Driver')
        .replace(/\belec\.?\s+eng\b/gi, 'Electrical Engineer')
        .replace(/\bcoachmn\b/gi, 'Coachman')
        .replace(/\brway\s+ganger\b/gi, 'Railway Ganger')
        .replace(/\beng\.?\s+drvr\.?\s+g\.?w\.?r\.?\b/gi, 'Engine Driver G.W.R.')
        .replace(/\bwoodtrnr\b/gi, 'Woodturner')
        .replace(/\btel\.?\s+clerk\b/gi, 'Telephone Clerk')
        .replace(/\bcellrmn\b/gi, 'Cellarman')
        .replace(/\bstrkr\b/gi, 'Striker')
        .replace(/\b(l;ab|labour[\x27\x22\x60]?r|lab[\x27\x22\x60]?r|lab[\x27\x22\x60]?rer)\b/gi, 'Labourer')
        .replace(/\btail;ors\b/gi, 'Tailors')
        .replace(/\bbrewerr\b/gi, 'Brewer')
        .replace(/\bprovision\s+merchanty\b/gi, 'Provision Merchant')
        .replace(/\bglass\s+blr\b/gi, 'Glassblower')
        .replace(/\btransp[\x27\x22\x60]?t\s+w[\x27\x22\x60]?r\b/gi, 'Transport Worker')
        .replace(/\bcr\.?\s*driver\b/gi, 'Crane Driver')
        .replace(/\btr[\x27\x22\x60]?mmer\b/gi, 'Trimmer')
        .replace(/\bhse\s+craft\s+mistress\b/gi, 'House Craft Mistress')
        .replace(/\bcanteen\s+stwd\b/gi, 'Canteen Steward')
        .replace(/\biron\s*&\s*metal\s+mcht\s+and\s+marine\s+stores\b/gi, 'Iron & Metal Merchant and Marine Stores')
        .replace(/\biworker\s*&\s*shop\b/gi, 'Ironworker and Shop')
        .replace(/\bnews\s*&\s*hairdr\b/gi, 'News and Hairdresser')
        .replace(/\bturf\s+acnt\b/gi, 'Turf Accountant')
        .replace(/\bahopkeeper\b/gi, 'Shopkeeper')
        .replace(/\btime\s+kp\b/gi, 'Timekeeper')
        .replace(/\bpump\s+attd?t\b/gi, 'Pump Attendant')
        .replace(/\bcoal\s+tmr\b/gi, 'Coal Trimmer')
        .replace(/\bblksth\b/gi, 'Blacksmith')
        .replace(/\bschool\s+teach\b/gi, 'School Teacher')
        .replace(/\bshop\s+ft[\x27\x22\x60]?rs\b/gi, 'Shop Fitters')
        .replace(/\binsurnc\s+agt\b/gi, 'Insurance Agent')
        .replace(/\bhead\s+waitr\b/gi, 'Head Waiter')
        .replace(/\brailwaymn\b/gi, 'Railwayman')
        .replace(/\bbootmkrs\b/gi, 'Bootmakers')
        .replace(/\bgreengrcrs\b/gi, 'Greengrocers')
        .replace(/\bpolice\s+sgt\b/gi, 'Police Sergeant')
        .replace(/\btobacnst\b/gi, 'Tobacconist')
        .replace(/\bbuilders\s+yd\b/gi, 'Builders Yard')
        .replace(/\bsecty\b/gi, 'Secretary')
        .replace(/\bgenl\s+dealer\b/gi, 'General Dealer')
        .replace(/\bcellarmn\b/gi, 'Cellarman')
        .replace(/\btravellr\b/gi, 'Traveller')
        .replace(/\bcycle\s+repr\b/gi, 'Cycle Repairer')
        .replace(/\benginemn\b/gi, 'Engineman')
        .replace(/\bpipe\s+fittr\b/gi, 'Pipe Fitter')
        .replace(/\bstocktkr\b/gi, 'Stocktaker')
        .replace(/\bwheelwgt\b/gi, 'Wheelwright')
        .replace(/\bwardrobe\s+dlr\b/gi, 'Wardrobe Dealer')
        .replace(/\bdecor[\x27\x22\x60]?tr\b/gi, 'Decorator')
        .replace(/\bboilermk\b/gi, 'Boilermaker')
        .replace(/\bpltlyr\b/gi, 'Platelayer')
        .replace(/\bglass\s+wks\b/gi, 'Glass Works')
        .replace(/\bins\.?\s+superintendent\b/gi, 'Insurance Superintendent')
        .replace(/\bgenl\.?\s+shop\b/gi, 'General Shop')
        .replace(/\bironwkr\b/gi, 'Ironworker')
        .replace(/\bstlwkr\b/gi, 'Steelworker')
        .replace(/wkr\b/gi, 'worker');

      // Standard trade abbreviations
      clean = clean
        .replace(/\blabr\b/gi, 'Labourer')
        .replace(/\bdvr\b/gi, 'Driver')
        .replace(/\bdrvr\b/gi, 'Driver')
        .replace(/\bdrivr\b/gi, 'Driver')
        .replace(/\beng\.?\s+driver\b/gi, 'Engine Driver')
        .replace(/\beng\.?\s+dvr\b/gi, 'Engine Driver')
        .replace(/\bptr\b/gi, 'Painter')
        .replace(/\bclk\b/gi, 'Clerk')
        .replace(/\btrm\b/gi, 'Trimmer')
        .replace(/\bbricklyr\b/gi, 'Bricklayer')
        .replace(/\bcarptr\b/gi, 'Carpenter')
        .replace(/\beng dvr\b/gi, 'Engine Driver');

      // Preserve G.W.R. and G.P.O. casing if present
      clean = clean.replace(/\b(g\.?p\.?o\.?)\b\.?/gi, 'G.P.O.');
      clean = clean.replace(/\w\S*/g, (txt) => {
        if (txt.toUpperCase() === 'G.W.R.') return 'G.W.R.';
        if (txt.toUpperCase() === 'G.P.O.') return 'G.P.O.';
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
      });

      return clean;
    }

    function getEraTag(yearStr) {
      const yr = parseInt(yearStr);
      if (yr < 1901) return 'Late Victorian';
      if (yr <= 1914) return 'Edwardian Era';
      if (yr <= 1939) return 'Interwar Period';
      return 'Post-War Era';
    }

    function quickSearch(query) {
      const input = document.getElementById('search-input');
      if (input) input.value = query;
      window.location.hash = `#search=${encodeURIComponent(query)}`;
    }

    function cleanSlug(text) {
      if (!text) return '';
      return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'unnamed';
    }

    let masterStreetsList = [];
    const streetCacheMap = new Map();
    let searchIndexData = null;
    let isSearchLoading = false;

    async function loadMasterStreets() {
      if (masterStreetsList.length) return masterStreetsList;
      try {
        const response = await fetch('data/streets.json');
        masterStreetsList = await response.json();
        uniqueStreets = masterStreetsList.map(s => s.displayName);

        // Update home stat counters
        const totalRecords = masterStreetsList.reduce((acc, s) => acc + s.recordsCount, 0);
        const recordsElem = document.getElementById('stat-records-count');
        if (recordsElem) recordsElem.innerText = totalRecords.toLocaleString();
        
        const streetsElem = document.getElementById('stat-streets-count');
        if (streetsElem) streetsElem.innerText = `${masterStreetsList.length}+`;

        return masterStreetsList;
      } catch (err) {
        console.error("Failed loading data/streets.json", err);
        return [];
      }
    }

    async function loadStreetData(rawStreetName) {
      const slug = cleanSlug(rawStreetName);
      if (streetCacheMap.has(slug)) return streetCacheMap.get(slug);

      try {
        const response = await fetch(`data/streets/${slug}.json`);
        if (!response.ok) return { records: [], summary: {} };
        const data = await response.json();
        streetCacheMap.set(slug, data);
        
        // Auto-apply active session overrides to freshly loaded street data
        if (sessionOverrides.length > 0) {
          sessionOverrides.forEach(ov => {
            if (ov.match && ov.apply && cleanSlug(ov.match.street) === slug) {
              applyLocalOverridePreview(
                ov.match.street,
                ov.match.year,
                ov.apply.house_number || ov.match.house_number || '',
                { surname: ov.match.surname_contains || '', building_name: ov.match.building_name || '' },
                ov.apply.building_name,
                ov.apply.surname,
                ov.apply.forename,
                ov.apply.trade,
                ov.apply.source_type || 'Primary'
              );
            }
          });
        }

        return data;
      } catch (err) {
        console.error(`Failed loading street JSON for ${slug}`, err);
        return { records: [], summary: {} };
      }
    }

    async function loadSearchIndex() {
      if (searchIndexData || isSearchLoading) return searchIndexData;
      isSearchLoading = true;
      try {
        const response = await fetch('data/search_index.json');
        searchIndexData = await response.json();
        isSearchLoading = false;
        return searchIndexData;
      } catch (err) {
        console.error("Failed loading search_index.json", err);
        isSearchLoading = false;
        return [];
      }
    }

    // --- Categorised Search Autocomplete Logic ---
    const searchInput = document.getElementById('search-input');
    const autocompleteContainer = document.getElementById('autocomplete-results');

    if (searchInput && autocompleteContainer) {
      searchInput.addEventListener('input', async () => {
        const query = searchInput.value.trim().toLowerCase();
        
        if (query.length < 2) {
          autocompleteContainer.classList.remove('active');
          return;
        }

        const indexData = await loadSearchIndex();

        const matchingStreets = (masterStreetsList || [])
          .filter(s => s.displayName.toLowerCase().includes(query))
          .slice(0, 3)
          .map(s => s.displayName);
        
        const matchingPeopleMap = new Map();
        for (const r of (indexData || [])) {
          const fullName = r.n || '';
          if (fullName.toLowerCase().includes(query) && !matchingPeopleMap.has(fullName.toLowerCase())) {
            const locLabel = r.k ? `${r.k}` : 'Street';
            matchingPeopleMap.set(fullName.toLowerCase(), {
              name: fullName,
              street: r.s,
              targetKey: r.k,
              tag: `${locLabel} ${r.s}`
            });
            if (matchingPeopleMap.size >= 3) break;
          }
        }
        const matchingPeople = Array.from(matchingPeopleMap.values());

        const matchingOccupationsSet = new Set();
        for (const r of (indexData || [])) {
          const displayTrade = cleanOccupation(r.t);
          if (
            displayTrade &&
            displayTrade !== 'Residence / Private' &&
            displayTrade.length < 40 &&
            displayTrade.toLowerCase().includes(query)
          ) {
            matchingOccupationsSet.add(displayTrade);
            if (matchingOccupationsSet.size >= 3) break;
          }
        }
        const matchingOccupations = Array.from(matchingOccupationsSet);

        if (!matchingStreets.length && !matchingPeople.length && !matchingOccupations.length) {
          autocompleteContainer.classList.remove('active');
          return;
        }

        autocompleteContainer.innerHTML = '';

        if (matchingStreets.length) {
          appendAutocompleteGroup('Streets', matchingStreets.map(s => ({
            label: `🏠 ${s}`, tag: 'Street', hash: `#street=${encodeURIComponent(s)}`
          })));
        }

        if (matchingPeople.length) {
          appendAutocompleteGroup('People', matchingPeople.map(p => ({
            label: `👤 ${p.name}`, tag: p.tag, hash: `#house=${encodeURIComponent(p.street + '|' + p.targetKey)}`
          })));
        }

        if (matchingOccupations.length) {
          appendAutocompleteGroup('Occupations', matchingOccupations.map(o => ({
            label: `🛠️ ${o}`, tag: 'Occupation', hash: `#search=${encodeURIComponent(o)}`
          })));
        }

        autocompleteContainer.classList.add('active');
      });
    }

    function appendAutocompleteGroup(title, items) {
      const groupHeader = document.createElement('div');
      groupHeader.className = 'autocomplete-group-title';
      groupHeader.innerText = title;
      autocompleteContainer.appendChild(groupHeader);

      items.forEach(itemData => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `<span>${itemData.label}</span><span class="type-tag">${itemData.tag}</span>`;
        item.addEventListener('click', () => {
          autocompleteContainer.classList.remove('active');
          window.location.hash = itemData.hash;
        });
        autocompleteContainer.appendChild(item);
      });
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-box-wrapper')) {
        autocompleteContainer.classList.remove('active');
      }
    });

    function parseSearchQuery(query) {
      const match = query.trim().match(/^(\d+[a-zA-Z]?)\s+(.*)/);
      if (match) return { number: match[1], street: match[2] };
      return { number: null, street: query.trim() };
    }

    document.getElementById('search-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const rawQuery = searchInput.value.trim();
      const { number, street } = parseSearchQuery(rawQuery);

      const matchedStreet = masterStreetsList.find(s => cleanStr(s.displayName) === cleanStr(street));

      if (number && matchedStreet) {
        const targetStreet = matchedStreet.displayName;
        window.location.hash = `#house=${encodeURIComponent(targetStreet + '|' + number)}`;
      } else {
        window.location.hash = `#search=${encodeURIComponent(rawQuery)}`;
      }
    });

    // --- Navigation Router ---
    async function navigate() {
      const hash = window.location.hash || '#home';
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      if (autocompleteContainer) autocompleteContainer.classList.remove('active');

      await loadMasterStreets();

      if (hash.startsWith('#search=')) {
        const query = decodeURIComponent(hash.substring(8));
        await renderSearchView(query);
        document.getElementById('view-search').classList.add('active');
      } else if (hash.startsWith('#street=')) {
        const rawStreet = decodeURIComponent(hash.substring(8));
        await renderStreetView(rawStreet);
        document.getElementById('view-street').classList.add('active');
      } else if (hash.startsWith('#house=')) {
        const parts = decodeURIComponent(hash.substring(7)).split('|');
        const street = parts[0] || '';
        const locKey = parts[1] || '';
        await renderHouseView(street, locKey);
        document.getElementById('view-house').classList.add('active');
      } else if (hash === '#streets') {
        renderStreetsView();
        document.getElementById('view-streets').classList.add('active');
      } else if (hash === '#directories') {
        renderDirectoriesView();
        document.getElementById('view-directories').classList.add('active');
      } else if (hash.startsWith('#directories=')) {
        const year = hash.replace('#directories=', '');
        renderStreetsView(year);
        document.getElementById('view-streets').classList.add('active');
      } else {
        document.getElementById('view-home').classList.add('active');
      }

      window.scrollTo(0, 0);
    }

    // --- Search View Rendering ---
    async function renderSearchView(query) {
      document.getElementById('search-query-display').innerText = query;

      const searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.value = query;

      const cleanQ = query.trim().toLowerCase();
      if (!cleanQ) return;

      const indexData = await loadSearchIndex();

      const matchedStreetsMap = new Map();
      const matchedPeople = [];
      const matchedOccupations = [];

      // Match streets from masterStreetsList
      masterStreetsList.forEach(st => {
        if (st.displayName.toLowerCase().includes(cleanQ)) {
          matchedStreetsMap.set(st.slug, {
            type: 'street',
            title: st.displayName,
            sub: `${st.houseCount || st.recordsCount} Properties • ${st.yearsSpan}`,
            address: 'Explore Street',
            hash: `#street=${encodeURIComponent(st.displayName)}`
          });
        }
      });

      // Match residents & trades from searchIndexData
      (indexData || []).forEach(r => {
        const fullName = r.n || '';
        const trade = r.t || '';
        const street = r.s || '';
        const locKey = r.k || '';
        const locAddress = `${locKey} ${street}`;

        if (fullName.toLowerCase().includes(cleanQ)) {
          matchedPeople.push({
            type: 'person',
            title: fullName,
            sub: trade || 'Resident',
            address: locAddress,
            hash: `#house=${encodeURIComponent(street + '|' + locKey)}`
          });
        }

        if (trade && trade.toLowerCase().includes(cleanQ)) {
          matchedOccupations.push({
            type: 'occupation',
            title: fullName,
            sub: trade,
            address: locAddress,
            hash: `#house=${encodeURIComponent(street + '|' + locKey)}`
          });
        }
      });

      const matchedStreets = Array.from(matchedStreetsMap.values());

      currentSearchResults = {
        people: matchedPeople,
        occupations: matchedOccupations,
        streets: matchedStreets,
        all: [...matchedStreets, ...matchedPeople, ...matchedOccupations]
      };

      document.getElementById('count-all').innerText = currentSearchResults.all.length;
      document.getElementById('count-people').innerText = currentSearchResults.people.length;
      document.getElementById('count-occupations').innerText = currentSearchResults.occupations.length;
      document.getElementById('count-streets').innerText = currentSearchResults.streets.length;

      currentPage = 1;
      setSearchFilter('all');
    }

    function setSearchFilter(tab, element) {
      currentSearchTab = tab;
      currentPage = 1;

      document.querySelectorAll('.search-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
      
      if (element) {
        element.classList.add('active');
      } else {
        const defaultBtn = document.querySelector(`.search-tabs .tab-btn[onclick*="'${tab}'"]`);
        if (defaultBtn) defaultBtn.classList.add('active');
      }

      renderSearchResultsList();
    }

    function renderSearchResultsList() {
      const listContainer = document.getElementById('search-results-list');
      listContainer.innerHTML = '';

      const dataset = currentSearchResults[currentSearchTab] || [];
      const totalCount = dataset.length;
      const totalPages = Math.ceil(totalCount / PAGE_SIZE) || 1;

      document.getElementById('search-summary-text').innerText = `Found ${totalCount} matching record entries.`;

      if (totalCount === 0) {
        listContainer.innerHTML = '<p style="color: var(--muted); padding: 2rem 0;">No matching records found for this category filter.</p>';
        document.getElementById('page-indicator').innerText = 'Page 0 of 0';
        document.getElementById('prev-page').disabled = true;
        document.getElementById('next-page').disabled = true;
        return;
      }

      const startIdx = (currentPage - 1) * PAGE_SIZE;
      const pageData = dataset.slice(startIdx, startIdx + PAGE_SIZE);

      pageData.forEach(item => {
        const card = document.createElement('a');
        card.className = 'result-card';
        card.href = item.hash;
        card.innerHTML = `
          <div class="result-main">
            <div class="result-title">${item.title}</div>
            <div class="result-sub">${item.sub}</div>
          </div>
          <div class="result-meta">
            <div class="result-address">${item.address || 'Explore Street'}</div>
          </div>
        `;
        listContainer.appendChild(card);
      });

      document.getElementById('page-indicator').innerText = `Page ${currentPage} of ${totalPages}`;
      document.getElementById('prev-page').disabled = currentPage === 1;
      document.getElementById('next-page').disabled = currentPage >= totalPages;
    }

    function changeSearchPage(delta) {
      currentPage += delta;
      renderSearchResultsList();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    let currentAuditFilter = 'all';

    function setStreetAuditFilter(filter) {
      currentAuditFilter = filter;
      ['all', 'name_verified', 'fully_enriched', 'unverified'].forEach(f => {
        const btn = document.getElementById(`tab-audit-${f}`);
        if (btn) {
          if (f === filter) btn.classList.add('active');
          else btn.classList.remove('active');
        }
      });
      renderStreetsView();
    }

    // --- All Streets View Rendering ---
    function renderStreetsView(filterYear = null) {
      const container = document.getElementById('streets-content');
      if (!container) return;
      container.innerHTML = '';

      if (!masterStreetsList.length) {
        container.innerHTML = '<p style="color: var(--muted); padding: 2rem;">Loading street directory...</p>';
        return;
      }

      // Update Audit Counters
      let masterDict = {};
      const storedOverrides = sessionOverrides.filter(o => o.action === 'UPDATE_MASTER_REGISTRY');
      storedOverrides.forEach(o => {
        masterDict[o.slug] = { audit: { status: o.audit_status } };
      });

      const totalCount = masterStreetsList.length;
      let nameVerifiedCount = 0;
      let fullyEnrichedCount = 0;
      let unverifiedCount = 0;

      masterStreetsList.forEach(s => {
        const slug = cleanStr(s.displayName).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        const overrideStatus = masterDict[slug] ? masterDict[slug].audit.status : null;
        let status = overrideStatus || s.auditStatus || 'UNVERIFIED';
        if (status === 'VERIFIED') status = 'NAME_VERIFIED';

        if (status === 'FULLY_ENRICHED') fullyEnrichedCount++;
        else if (status === 'NAME_VERIFIED') nameVerifiedCount++;
        else unverifiedCount++;
      });

      const cntAll = document.getElementById('count-audit-all');
      const cntNameVer = document.getElementById('count-audit-name_verified');
      const cntEnriched = document.getElementById('count-audit-fully_enriched');
      const cntUnver = document.getElementById('count-audit-unverified');
      if (cntAll) cntAll.innerText = totalCount;
      if (cntNameVer) cntNameVer.innerText = nameVerifiedCount;
      if (cntEnriched) cntEnriched.innerText = fullyEnrichedCount;
      if (cntUnver) cntUnver.innerText = unverifiedCount;

      let streetsToShow = masterStreetsList;
      if (filterYear) {
        streetsToShow = masterStreetsList.filter(s => s.yearsSpan && s.yearsSpan.includes(filterYear));
        document.getElementById('streets-summary-text').innerText = 
          `Index of ${streetsToShow.length} streets recorded in the ${filterYear} directory collection.`;
        document.querySelector('#view-streets .street').innerText = `${filterYear} Directory Streets`;
        document.querySelector('#view-streets .breadcrumb').innerHTML = `<a href="#home">Home</a> &rarr; <a href="#directories">Directories</a> &rarr; <span>${filterYear}</span>`;
      } else {
        if (currentAuditFilter === 'name_verified') {
          streetsToShow = masterStreetsList.filter(s => {
            const slug = cleanStr(s.displayName).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            let status = masterDict[slug] ? masterDict[slug].audit.status : (s.auditStatus || 'UNVERIFIED');
            if (status === 'VERIFIED') status = 'NAME_VERIFIED';
            return status === 'NAME_VERIFIED';
          });
        } else if (currentAuditFilter === 'fully_enriched') {
          streetsToShow = masterStreetsList.filter(s => {
            const slug = cleanStr(s.displayName).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            const status = masterDict[slug] ? masterDict[slug].audit.status : (s.auditStatus || 'UNVERIFIED');
            return status === 'FULLY_ENRICHED';
          });
        } else if (currentAuditFilter === 'unverified') {
          streetsToShow = masterStreetsList.filter(s => {
            const slug = cleanStr(s.displayName).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            let status = masterDict[slug] ? masterDict[slug].audit.status : (s.auditStatus || 'UNVERIFIED');
            if (status === 'VERIFIED') status = 'NAME_VERIFIED';
            return status === 'UNVERIFIED';
          });
        }

        document.getElementById('streets-summary-text').innerText = 
          `Showing ${streetsToShow.length} of ${masterStreetsList.length} total recorded streets in archive collections.`;
        document.querySelector('#view-streets .street').innerText = `All Streets`;
        document.querySelector('#view-streets .breadcrumb').innerHTML = `<a href="#home">Home</a> &rarr; <span>Streets</span>`;
      }

      if (!streetsToShow.length) {
        container.innerHTML = '<p style="color: var(--muted); padding: 3rem 0; text-align: center;">No streets match the selected audit filter.</p>';
        return;
      }

      // Build A-Z Quick Jump Bar
      const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
      const activeLetters = new Set(streetsToShow.map(s => s.displayName.charAt(0).toUpperCase()));

      const jumpBar = document.getElementById('alpha-jump-bar');
      if (jumpBar) {
        jumpBar.innerHTML = '';
        alphabet.forEach(letVal => {
          const btn = document.createElement('button');
          const isActive = activeLetters.has(letVal);
          btn.className = `alpha-jump-btn ${isActive ? 'active' : 'disabled'}`;
          btn.innerText = letVal;
          if (isActive) {
            btn.onclick = (e) => {
              e.preventDefault();
              const targetSection = document.getElementById(`letter-${letVal}`);
              if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            };
          }
          jumpBar.appendChild(btn);
        });
      }

      let currentLetter = '';
      let currentGrid = null;

      streetsToShow.forEach(data => {
        const firstLetter = data.displayName.charAt(0).toUpperCase();
        if (firstLetter !== currentLetter) {
          currentLetter = firstLetter;

          const section = document.createElement('div');
          section.className = 'alpha-section';
          section.id = `letter-${currentLetter}`;

          const header = document.createElement('h2');
          header.className = 'alpha-header';
          header.innerText = currentLetter;

          currentGrid = document.createElement('div');
          currentGrid.className = 'street-grid';

          section.appendChild(header);
          section.appendChild(currentGrid);
          container.appendChild(section);
        }

        const propText = data.houseCount > 0 ? `${data.houseCount} Properties` : `${data.recordsCount} Records`;
        const slug = cleanStr(data.displayName).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        let currentStatus = masterDict[slug] ? masterDict[slug].audit.status : (data.auditStatus || 'UNVERIFIED');
        if (currentStatus === 'VERIFIED') currentStatus = 'NAME_VERIFIED';

        let badgeHTML = '<span class="source-pill source-pill-primary" style="font-size: 0.65rem; opacity: 0.7;">⚠️ RAW</span>';
        if (currentStatus === 'FULLY_ENRICHED') {
          badgeHTML = '<span class="source-pill source-pill-user" style="font-size: 0.65rem; background: rgba(200, 157, 84, 0.2); color: var(--accent); border-color: var(--accent);">🌟 ENRICHED</span>';
        } else if (currentStatus === 'NAME_VERIFIED') {
          badgeHTML = '<span class="source-pill source-pill-user" style="font-size: 0.65rem;">🔒 NAME VERIFIED</span>';
        }

        const card = document.createElement('a');
        card.className = 'street-index-card';
        card.href = `#street=${encodeURIComponent(data.displayName)}`;
        card.innerHTML = `
          <div class="street-index-title">${data.displayName}</div>
          <div class="street-index-footer">
            <span class="street-index-meta">${propText} • ${data.yearsSpan}</span>
            <span class="street-index-badge">${badgeHTML}</span>
          </div>
        `;
        currentGrid.appendChild(card);
      });
    }

    let currentStreet = '';

    // --- Single Street View Rendering ---
    async function renderStreetView(rawStreetName) {
      const displayName = rawStreetName.trim();
      currentStreet = displayName;
      document.getElementById('street-title').innerText = displayName;
      document.getElementById('street-heading').innerText = displayName;

      const streetData = await loadStreetData(rawStreetName);
      const streetRecords = streetData.records || [];

      // Calculate street development origin era
      const streetYears = streetRecords.map(r => parseInt(r.year)).filter(y => !isNaN(y)).sort((a,b) => a - b);
      const firstYr = streetYears.length ? streetYears[0] : 1876;
      const lastYr = streetYears.length ? streetYears[streetYears.length - 1] : 1950;
      
      let eraText = '';
      if (firstYr <= 1876) eraText = '📜 Victorian Core Street (Recorded since 1876)';
      else if (firstYr <= 1897) eraText = `🏛️ Late Victorian Urban Expansion (First recorded in ${firstYr} directory)`;
      else if (firstYr <= 1914) eraText = `🏡 Edwardian Housing Expansion (First recorded in ${firstYr} directory)`;
      else if (firstYr <= 1939) eraText = `🌳 Interwar Garden Suburb / Municipal Estate (First recorded in ${firstYr} directory)`;
      else eraText = `🏗️ Post-War Development (First recorded in ${firstYr} directory)`;

      // Render former names or modern renamed name badge if recorded in street summary
      const summary = streetData.summary || {};
      const formerNames = summary.formerNames || [];
      const renamedTo = summary.renamedTo || summary.modernName || '';
      const lat = summary.latitude || '';
      const lon = summary.longitude || '';
      const streetSlug = cleanSlug(displayName);
      
      const heroMediaElem = document.getElementById('street-hero-media');
      if (heroMediaElem) {
        if (lat && lon) {
          heroMediaElem.innerHTML = `
            <div style="border: 1px solid var(--accent-muted); border-radius: 10px; overflow: hidden; background: #120f0d; box-shadow: 0 8px 24px rgba(0,0,0,0.5);">
              <div style="position: relative; overflow: hidden; height: 210px; background: #000;">
                <img src="assets/images/streetview/${streetSlug}.jpg" alt="${displayName} Street View" style="width: 100%; height: 100%; object-fit: cover; display: block;" onerror="this.onerror=null; document.getElementById('street-hero-media').style.display='none';" />
              </div>
              <div style="padding: 0.6rem 0.9rem; background: rgba(18, 15, 13, 0.95); font-size: 0.82rem; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--accent-muted);">
                <span style="color: var(--accent); font-weight: 500; display: inline-flex; align-items: center; gap: 0.3rem;">📍 <strong>${lat}, ${lon}</strong></span>
                <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}" target="_blank" rel="noopener" style="color: var(--accent); text-decoration: underline; font-weight: 600;">Explore Street View ↗</a>
              </div>
            </div>`;
          heroMediaElem.style.display = 'block';
        } else {
          heroMediaElem.style.display = 'none';
          heroMediaElem.innerHTML = '';
        }
      }

      let formerHTML = '';
      if (renamedTo) {
        formerHTML += `<div style="margin-top: 0.75rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span style="font-size: 0.85rem; color: var(--accent); background: rgba(200, 157, 84, 0.15); border: 1px solid var(--accent-muted); padding: 0.25rem 0.65rem; border-radius: 12px; font-weight: 500;">
              🔀 Renamed to: <a href="#street=${encodeURIComponent(renamedTo)}" style="color: var(--accent); text-decoration: underline; font-weight: 600;">${renamedTo}</a>
            </span>
           </div>`;
      }
      if (formerNames.length > 0) {
        const formerLinks = formerNames.map(fn => `<a href="#street=${encodeURIComponent(fn)}" style="color: var(--accent); text-decoration: underline; font-weight: 600;">${fn}</a>`).join(', ');
        formerHTML += `<div style="margin-top: 0.75rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span style="font-size: 0.85rem; color: var(--accent); background: rgba(200, 157, 84, 0.15); border: 1px solid var(--accent-muted); padding: 0.25rem 0.65rem; border-radius: 12px; font-weight: 500;">
              📜 Formerly recorded as: <strong>${formerLinks}</strong>
            </span>
           </div>`;
      }

      const isPureCrossRefStreet = streetRecords.length > 0 && streetRecords.every(r => r.surname && r.surname.toLowerCase().startsWith('see '));
      const crossRefRec = streetRecords.find(r => r.surname && r.surname.toLowerCase().startsWith('see '));
      const introElem = document.getElementById('street-intro');
      if (introElem) {
        if (isPureCrossRefStreet && crossRefRec) {
          const targetStreet = crossRefRec.surname.substring(4).trim();
          introElem.innerHTML = `🏛️ Archival Directory Notice: In historical directories, <strong>${displayName}</strong> is an index cross-reference pointing readers to <strong>${targetStreet}</strong>. <a href="#street=${encodeURIComponent(targetStreet)}" style="color: #c89d54; text-decoration: underline; font-weight: 600; margin-left: 6px;">Check the ${targetStreet} Directory →</a>${formerHTML}`;
          document.getElementById('house-grid').innerHTML = '';
          return;
        } else {
          introElem.innerHTML = `<div>${eraText}. Recorded across ${streetRecords.length} directory entries from ${firstYr} to ${lastYr}.</div>${formerHTML}`;
        }
      }

      const locationsMap = new Map();

      streetRecords.forEach(r => {
        let cleanSurname = (r.surname || '').replace(/^[-~\s]+/, '').trim();
        let cleanForename = (r.forename || '').trim();
        
        let fullName = cleanForename ? `${cleanForename} ${cleanSurname}` : cleanSurname;
        fullName = fullName.replace(/^[-~\s]+/, '').trim();

        let key = '';
        let displayTitle = '';
        let isExplicitLocation = false;

        if (r.house_number && r.house_number !== '-' && r.house_number !== '~' && r.house_number !== '0') {
          key = cleanStr(r.house_number);
          displayTitle = r.house_number;
          isExplicitLocation = true;
        } else if (r.building_name && r.building_name !== '-' && r.building_name !== '~' && r.building_name !== '0') {
          key = cleanStr(r.building_name);
          displayTitle = r.building_name;
          isExplicitLocation = true;
        } else if (fullName) {
          key = cleanStr(fullName);
          displayTitle = fullName;
        }

        if (!key) return;

        if (!locationsMap.has(key)) {
          locationsMap.set(key, {
            key: key,
            displayTitle: displayTitle,
            isExplicitLocation: isExplicitLocation,
            targetKey: (r.house_number || r.building_name || fullName),
            records: []
          });
        }
        locationsMap.get(key).records.push(r);
      });

      const grid = document.getElementById('house-grid');
      grid.innerHTML = '';

      if (locationsMap.size === 0) {
        grid.innerHTML = '<p style="color: var(--muted);">No matching property records found for this street.</p>';
        return;
      }

      // Partition locations into Numbered Properties, Named Villas & Buildings, and Unnumbered Listings
      const numberedProperties = [];
      const namedVillas = [];
      const unnumberedListings = [];

      Array.from(locationsMap.values()).forEach(loc => {
        const hasHouseNum = loc.records.some(r => r.house_number && r.house_number !== '-' && r.house_number !== '~' && r.house_number !== '0');
        const hasBldgName = loc.records.some(r => r.building_name && r.building_name !== '-' && r.building_name !== '~' && r.building_name !== '0');

        if (hasHouseNum) {
          numberedProperties.push(loc);
        } else if (hasBldgName) {
          namedVillas.push(loc);
        } else {
          unnumberedListings.push(loc);
        }
      });

      // Sort helpers
      const parseNum = (str) => {
        const m = str.match(/^(\d+)/);
        return m ? parseInt(m[1]) : null;
      };
      const sortNumeric = (a, b) => {
        const numA = parseNum(a.displayTitle);
        const numB = parseNum(b.displayTitle);
        if (numA !== null && numB !== null) return numA - numB;
        if (numA !== null) return -1;
        if (numB !== null) return 1;
        return a.displayTitle.localeCompare(b.displayTitle);
      };
      const sortAlpha = (a, b) => a.displayTitle.localeCompare(b.displayTitle);

      numberedProperties.sort(sortNumeric);
      namedVillas.sort(sortAlpha);
      unnumberedListings.sort(sortAlpha);

      grid.style.display = 'flex';
      grid.style.flexDirection = 'column';
      grid.style.gap = '2.5rem';

      function renderSection(title, locations) {
        if (locations.length === 0) return;

        const section = document.createElement('div');
        section.innerHTML = `
          <h3 style="font-family: var(--heading-font); font-size: 1.65rem; color: var(--accent); margin-bottom: 1rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.5rem; display: flex; align-items: center; gap: 0.75rem;">
            <span>${title}</span>
            <span style="font-size: 0.85rem; font-family: var(--sans-font); background: rgba(200, 157, 84, 0.12); color: var(--accent); padding: 0.2rem 0.6rem; border-radius: 12px; font-weight: 600;">${locations.length}</span>
          </h3>
          <div class="street-grid"></div>
        `;
        const subGrid = section.querySelector('.street-grid');

        locations.forEach(loc => {
          const maxYear = Math.max(...loc.records.map(r => parseInt(r.year)).filter(y => !isNaN(y)));
          const latestRecords = loc.records.filter(r => parseInt(r.year) === maxYear);

          let residentName = '';
          let tradeTitle = '';

          if (loc.isExplicitLocation) {
            if (latestRecords.length === 1) {
              const r = latestRecords[0];
              const sName = (r.surname || '').replace(/^[-~\s]+/, '').trim();
              const fName = (r.forename || '').trim();
              const name = fName ? `${expandForename(fName)} ${sName}` : sName;
              residentName = name;
              tradeTitle = cleanOccupation(r.trade);
            } else {
              const first = latestRecords[0];
              const sName = (first.surname || '').replace(/^[-~\s]+/, '').trim();
              const fName = (first.forename || '').trim();
              const firstName = fName ? `${expandForename(fName)} ${sName}` : sName;
              residentName = `${firstName} + ${latestRecords.length - 1} other${latestRecords.length > 2 ? 's' : ''}`;
              tradeTitle = cleanOccupation(first.trade);
            }
          } else {
            const r = latestRecords[0];
            residentName = cleanOccupation(r.trade);
          }

          let cleanTitle = loc.displayTitle.replace(/^[-~\s]+/, '').trim();
          const bldg = loc.records.find(r => {
            if (!r.building_name || r.building_name === '-' || r.building_name === '~' || r.building_name === '0') return false;
            const b = r.building_name.trim();
            if (r.surname && b.toLowerCase().includes(r.surname.toLowerCase())) return false;
            return true;
          });

          let headerTitleHtml = '';
          if (bldg && cleanTitle !== bldg.building_name) {
            headerTitleHtml = `
              <span class="card-num">${cleanTitle}</span>
              <span class="card-sep">—</span>
              <span class="card-hname">${bldg.building_name}</span>
            `;
          } else {
            headerTitleHtml = `
              <span class="card-num">${cleanTitle}</span>
            `;
          }

          const card = document.createElement('a');
          card.className = 'street-card';
          card.href = `#house=${encodeURIComponent(displayName + '|' + loc.targetKey)}`;
          card.innerHTML = `
            <div class="card-top-section">
              ${headerTitleHtml}
            </div>
            <div class="card-body-section">
              <div class="card-resident-name">${residentName || 'Residence'}</div>
              ${tradeTitle && tradeTitle !== 'Residence / Private' ? `<div class="card-trade-title">${tradeTitle}</div>` : ''}
            </div>
          `;
          subGrid.appendChild(card);
        });

        grid.appendChild(section);
      }

      renderSection('Numbered Properties', numberedProperties);
      renderSection('Named Villas & Buildings', namedVillas);
      renderSection('Unnumbered Listings / Other', unnumberedListings);
    }

    // --- House & Building Timeline View State & Enhancements ---
    let currentHouseRecords = [];
    let currentTimelineEraFilter = 'all';
    let currentTimelineViewMode = 'tenure';
    let currentActiveMediaMode = 'facade';

    function filterTimeline(era, btn) {
      currentTimelineEraFilter = era;
      document.querySelectorAll('.era-filter-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      renderTimelineItems();
    }

    function switchMediaMode(mode) {
      currentActiveMediaMode = mode;
      const imgElement = document.getElementById('property-image');
      const mapIframe = document.getElementById('property-map');
      const btnFacade = document.getElementById('media-btn-facade');
      const btnMap = document.getElementById('media-btn-map');

      if (mode === 'facade') {
        if (btnFacade) btnFacade.classList.add('active');
        if (btnMap) btnMap.classList.remove('active');
        imgElement.style.display = 'block';
        mapIframe.style.display = 'none';
        document.getElementById('image-caption-title').innerText = 'Archival Facade View';
      } else {
        if (btnMap) btnMap.classList.add('active');
        if (btnFacade) btnFacade.classList.remove('active');
        imgElement.style.display = 'none';
        mapIframe.style.display = 'block';
        document.getElementById('image-caption-title').innerText = 'Interactive Location Map';
      }
    }

    function copyCitation() {
      const citationText = document.getElementById('citation-text').innerText;
      navigator.clipboard.writeText(citationText).then(() => {
        const btn = document.getElementById('citation-btn');
        const orig = btn.innerText;
        btn.innerText = '✓ Citation Copied!';
        btn.style.background = '#c89d54';
        btn.style.color = '#120f0d';
        setTimeout(() => {
          btn.innerText = orig;
          btn.style.background = '';
          btn.style.color = '';
        }, 2000);
      });
    }

    async function renderHouseView(rawStreetName, locationKey) {
      const displayName = formatStreetName(rawStreetName);
      const cleanLocKey = cleanStr(locationKey);

      // Extract leading house number prefix if present (e.g. "35-35A" from "35-35A Smith W. H. & Son")
      const numMatch = locationKey.trim().match(/^(\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?)$/);
      const extractedHouseNum = numMatch ? numMatch[1] : locationKey;
      const cleanExtractedNum = cleanStr(extractedHouseNum);

      // 1. Gather all street properties to compute Prev / Next house navigation links
      const streetData = await loadStreetData(rawStreetName);
      const streetRecords = streetData.records || [];
      const locationKeysSet = new Set();
      streetRecords.forEach(r => {
        const target = r.house_number || r.building_name || `${expandForename(r.forename)} ${r.surname}`.trim();
        if (target) locationKeysSet.add(target);
      });

      const sortedLocKeys = Array.from(locationKeysSet).sort((a, b) => {
        const parseNum = (str) => {
          const m = str.match(/^(\d+)/);
          return m ? parseInt(m[1]) : null;
        };
        const numA = parseNum(a);
        const numB = parseNum(b);
        if (numA !== null && numB !== null) return numA - numB;
        if (numA !== null) return -1;
        if (numB !== null) return 1;
        return a.localeCompare(b);
      });

      const currentIdx = sortedLocKeys.findIndex(k => cleanStr(k) === cleanLocKey || cleanStr(k) === cleanExtractedNum);
      const prevBtn = document.getElementById('prev-house-btn');
      const nextBtn = document.getElementById('next-house-btn');

      if (currentIdx > 0) {
        prevBtn.classList.remove('disabled');
        prevBtn.href = `#house=${encodeURIComponent(displayName + '|' + sortedLocKeys[currentIdx - 1])}`;
      } else {
        prevBtn.classList.add('disabled');
        prevBtn.href = '#';
      }

      if (currentIdx !== -1 && currentIdx < sortedLocKeys.length - 1) {
        nextBtn.classList.remove('disabled');
        nextBtn.href = `#house=${encodeURIComponent(displayName + '|' + sortedLocKeys[currentIdx + 1])}`;
      } else {
        nextBtn.classList.add('disabled');
        nextBtn.href = '#';
      }

      // 2. Filter records for this exact house / location
      currentHouseRecords = streetRecords
        .filter(r => {
          const rHouseNum = cleanStr(r.house_number);
          const rBldgName = cleanStr(r.building_name);
          const rawFullName = (r.forename ? `${r.forename} ${r.surname}` : r.surname).trim();
          const fullName = cleanStr(rawFullName);
          const expandedFullName = cleanStr(`${expandForename(r.forename)} ${r.surname}`);

          if (rHouseNum && (rHouseNum === cleanLocKey || rHouseNum === cleanExtractedNum)) return true;
          if (rBldgName && (rBldgName === cleanLocKey || rBldgName === cleanExtractedNum)) return true;
          if (!rHouseNum && !rBldgName && (fullName === cleanLocKey || expandedFullName === cleanLocKey || cleanLocKey.includes(fullName) || fullName.includes(cleanLocKey))) return true;

          return false;
        })
        .sort((a, b) => parseInt(b.year) - parseInt(a.year));

      // Clean up any raw cross-reference prefix from locationKey (e.g. "NewportSee Stow Hill" -> "Stow Hill")
      const rawCleanLabel = locationKey.replace(/^(newport\s*)?see\s*/i, '').trim();
      const seeMatch = locationKey.match(/(?:newport\s*)?see\s+(.*)/i);
      const targetStreetRef = seeMatch ? seeMatch[1].trim() : null;

      const displayLocationLabel = numMatch ? extractedHouseNum : rawCleanLabel;
      const isNumeric = /^\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?$/.test(displayLocationLabel.trim());
      const headerLabel = displayLocationLabel;
      const breadcrumbLabel = isNumeric ? `No. ${displayLocationLabel}` : displayLocationLabel;
      const cleanStreetDisplay = displayName.replace(/^(newport\s*)?see\s*/i, '').trim();

      document.getElementById('house-breadcrumb-num').innerText = breadcrumbLabel;
      document.getElementById('house-number-display').innerText = headerLabel;
      document.getElementById('house-street-display').innerText = cleanStreetDisplay;
      
      const streetLink = document.getElementById('house-street-link');
      streetLink.innerText = cleanStreetDisplay;
      streetLink.href = `#street=${encodeURIComponent(cleanStreetDisplay)}`;

      document.getElementById('record-count').innerText = `${currentHouseRecords.length} Records Found`;

      const introElem = document.getElementById('property-intro');
      const houseCrossRefRec = currentHouseRecords.find(r => r.surname && r.surname.toLowerCase().startsWith('see '));

      if (houseCrossRefRec) {
        const targetStreet = houseCrossRefRec.surname.substring(4).trim();
        introElem.innerHTML = `🏛️ Archival Directory Notice: In historical directories, <strong>${cleanStreetDisplay}</strong> points readers to <strong>${targetStreet}</strong>. <a href="#street=${encodeURIComponent(targetStreet)}" style="color: #c89d54; text-decoration: underline; font-weight: 600; margin-left: 6px;">Check ${targetStreet} Directory →</a>`;
      } else if (currentHouseRecords.length === 0) {
        if (targetStreetRef) {
          introElem.innerHTML = `🏛️ Archival Cross-Reference Notice: In historical street directories, this location was an index cross-reference pointing readers to <strong>${targetStreetRef}</strong>. No individual resident entries are filed under this heading. <a href="#street=${encodeURIComponent(targetStreetRef)}" style="color: #c89d54; text-decoration: underline; font-weight: 600; margin-left: 6px;">View ${targetStreetRef} Directory →</a>`;
        } else {
          introElem.innerText = `🏛️ Archival Directory Notice: No resident entries recorded for ${isNumeric ? 'No. ' + displayLocationLabel : displayLocationLabel} ${cleanStreetDisplay}. It may have been a cross-reference pointer or historical indexing note.`;
        }
      } else {
        introElem.innerText = `Historical directory timeline for ${isNumeric ? 'No. ' + displayLocationLabel : displayLocationLabel} ${cleanStreetDisplay}. Spanning ${currentHouseRecords.length} recorded entries across archival street directories.`;
      }

      // 3. Populate Property Quick Metrics Bar
      const yearsArray = currentHouseRecords.map(r => parseInt(r.year)).filter(y => !isNaN(y)).sort((a,b) => a - b);
      const earliestYr = yearsArray.length ? yearsArray[0] : '-';
      const latestYr = yearsArray.length ? yearsArray[yearsArray.length - 1] : '-';
      
      document.getElementById('p-stat-earliest').innerText = earliestYr;
      document.getElementById('p-stat-latest').innerText = latestYr;
      document.getElementById('p-stat-total').innerText = currentHouseRecords.length;

      const tradesList = currentHouseRecords.map(r => cleanOccupation(r.trade)).filter(t => t && t !== 'Residence / Private');
      const primaryTrade = tradesList.length ? tradesList[0] : 'Private Residence';
      document.getElementById('p-stat-primary-trade').innerText = primaryTrade.length > 18 ? primaryTrade.substring(0, 16) + '...' : primaryTrade;

      // 4. Update Archival Citation Text
      const citationText = `Newport Directory Archive — ${isNumeric ? 'No. ' + locationKey : locationKey} ${displayName}, Newport, Wales (${earliestYr}–${latestYr}).`;
      document.getElementById('citation-text').innerText = citationText;

      // 5. Media Image / Map Handling & Comprehensive Historical Location Mapping
      const imgElement = document.getElementById('property-image');
      const oldMapIframe = document.getElementById('property-map');
      
      const HISTORICAL_LOCATION_MAPS = {
        // Municipal Fire Brigade
        'firestationflats': { address: 'Dock Street, Newport, Wales', note: 'Demolished Municipal Fire Brigade Quarters (1930s). Historically located off Dock Street.' },
        'firestationcottages': { address: 'Dock Street, Newport, Wales', note: 'Demolished Municipal Fire Brigade Staff Cottages (1930s). Historically located off Dock Street.' },
        
        // Newport Town Dock & Wharves (Infilled 1930s)
        'docktown': { address: 'Commercial Road, Newport, Wales', note: 'Historic Newport Town Dock (1842–1930s, infilled). Now George Street Bridge / Commercial Road area.' },
        'dockthetown': { address: 'Commercial Road, Newport, Wales', note: 'Historic Newport Town Dock (1842–1930s, infilled). Now George Street Bridge / Commercial Road area.' },
        'docktheold': { address: 'Commercial Road, Newport, Wales', note: 'Historic Newport Old Town Dock (infilled 1930s).' },
        'dockstreetwharves': { address: 'Dock Street, Newport, Wales', note: 'Historic Town Dock Wharves Area (Redeveloped).' },
        'dockparade': { address: 'Commercial Road, Newport, Wales', note: 'Historic Town Dock East Parade (Redeveloped 1930s).' },
        
        // Friars Walk / Austin Friars Area (Redeveloped 2015)
        'austinfriars': { address: 'Friars Walk, Newport, Wales', note: 'Historic Austin Friars Friary Site. Redeveloped into modern Friars Walk & Kingsway (2015).' },
        'austinfriarschambers': { address: 'Friars Walk, Newport, Wales', note: 'Historic Austin Friars Chambers. Site now part of Friars Walk & Kingsway.' },
        
        // Monmouthshire Canal Basin (Infilled 1930s for Kingsway A4042)
        'canalbank': { address: 'Kingsway, Newport, Wales', note: 'Monmouthshire Canal Newport Basin (Infilled 1930s). Now Kingsway / A4042 carriageway.' },
        'canalparade': { address: 'Kingsway, Newport, Wales', note: 'Monmouthshire Canal Basin Parade (Infilled 1930s). Now Kingsway.' },
        'canalstreet': { address: 'Kingsway, Newport, Wales', note: 'Monmouthshire Canal Basin Street (Infilled 1930s). Now Kingsway.' },
        'canalterrace': { address: 'Kingsway, Newport, Wales', note: 'Monmouthshire Canal Basin Terrace (Infilled 1930s).' },

        // Military Barracks (Chartist Uprising 1839 era)
        'barracklane': { address: 'Cardiff Road, Newport, Wales', note: 'Historic Newport Military Barracks Lane (1839 Chartist Era Barracks site).' },
        'barrackroad': { address: 'Cardiff Road, Newport, Wales', note: 'Historic Newport Military Barracks Road (Chartist Era site).' },

        // Courtybella Ironworks & Tramroads
        'courtybella': { address: 'Cardiff Road, Newport, Wales', note: 'Historic Courtybella Ironworks & Tramroad Siding (Cardiff Road area).' },
        'courtybellastreet': { address: 'Cardiff Road, Newport, Wales', note: 'Historic Courtybella Ironworks Housing (Cardiff Road area).' },
        'courtybellaterrace': { address: 'Cardiff Road, Newport, Wales', note: 'Historic Courtybella Ironworks Housing (Cardiff Road area).' },

        // Workhouse & Institutional
        'workhousecottages': { address: 'Stow Hill, Newport, Wales', note: 'Former Union Workhouse Quarters, Stow Hill (now St Woolos Hospital campus).' }
      };

      const streetKey = cleanStr(displayName);
      const histConfig = HISTORICAL_LOCATION_MAPS[streetKey];

      const buildingSlug = cleanStr(displayName) + cleanStr(locationKey);
      const localAssetSrc = `/assets/images/properties/${buildingSlug}/archive/facade.jpg`;
      const targetAddress = histConfig ? histConfig.address : `${isNumeric ? locationKey : ''} ${displayName}, Newport, Wales`;
      const addressQuery = encodeURIComponent(targetAddress);
      const mapUrl = `https://maps.google.com/maps?q=${addressQuery}&t=&z=17&ie=UTF8&iwloc=&output=embed`;

      if (histConfig) {
        introElem.innerText = `🏛️ Historic Site Notice: ${histConfig.note} Spanning ${currentHouseRecords.length} recorded entries in archival street directories.`;
      }

      if (oldMapIframe && oldMapIframe.parentNode) {
        const newIframe = document.createElement('iframe');
        newIframe.id = 'property-map';
        newIframe.setAttribute('loading', 'lazy');
        newIframe.style.display = oldMapIframe.style.display;
        newIframe.src = mapUrl;
        oldMapIframe.parentNode.replaceChild(newIframe, oldMapIframe);
      }

      const testImg = new Image();
      testImg.src = localAssetSrc;

      testImg.onload = function() {
        imgElement.src = localAssetSrc;
        switchMediaMode('facade');
      };

      testImg.onerror = function() {
        switchMediaMode('map');
      };

      // 6. Reset Era filter & render timeline items
      currentTimelineEraFilter = 'all';
      document.querySelectorAll('.era-filter-btn').forEach(b => b.classList.remove('active'));
      const allEraBtn = document.querySelector('.era-filter-btn[onclick*="\'all\'"]');
      if (allEraBtn) allEraBtn.classList.add('active');

      renderTimelineItems();
    }

    function setTimelineViewMode(mode, btn) {
      currentTimelineViewMode = mode;
      document.getElementById('btn-mode-tenure').classList.remove('active');
      document.getElementById('btn-mode-yearly').classList.remove('active');
      if (btn) btn.classList.add('active');
      renderTimelineItems();
    }

    function filterTimeline(era, btn) {
      currentTimelineEraFilter = era;
      const eraBtns = document.querySelectorAll('.era-filter-row .era-filter-btn');
      eraBtns.forEach(b => {
        if (b.id !== 'btn-mode-tenure' && b.id !== 'btn-mode-yearly') b.classList.remove('active');
      });
      if (btn) btn.classList.add('active');
      renderTimelineItems();
    }

    function switchMediaMode(mode) {
      currentActiveMediaMode = mode;
      const imgElement = document.getElementById('property-image');
      const mapIframe = document.getElementById('property-map');
      const btnFacade = document.getElementById('media-btn-facade');
      const btnMap = document.getElementById('media-btn-map');

      if (mode === 'facade') {
        if (btnFacade) btnFacade.classList.add('active');
        if (btnMap) btnMap.classList.remove('active');
        imgElement.style.display = 'block';
        mapIframe.style.display = 'none';
        document.getElementById('image-caption-title').innerText = 'Archival Facade View';
      } else {
        if (btnMap) btnMap.classList.add('active');
        if (btnFacade) btnFacade.classList.remove('active');
        imgElement.style.display = 'none';
        mapIframe.style.display = 'block';
        document.getElementById('image-caption-title').innerText = 'Interactive Location Map';
      }
    }

    function copyCitation() {
      const citationText = document.getElementById('citation-text').innerText;
      navigator.clipboard.writeText(citationText).then(() => {
        const btn = document.getElementById('citation-btn');
        btn.innerText = '✓ Citation Copied!';
        setTimeout(() => btn.innerText = 'Copy Archival Citation', 2500);
      });
    }

    function renderTimelineItems() {
      const timeline = document.getElementById('timeline-list');
      timeline.innerHTML = '';

      let filteredRecords = currentHouseRecords;
      if (currentTimelineEraFilter !== 'all') {
        filteredRecords = currentHouseRecords.filter(r => {
          const era = getEraTag(r.year);
          if (currentTimelineEraFilter === 'Victorian') return era === 'Late Victorian';
          if (currentTimelineEraFilter === 'Edwardian') return era === 'Edwardian Era';
          if (currentTimelineEraFilter === 'Interwar') return era === 'Interwar Period' || era === 'Post-War Era';
          return true;
        });
      }

      if (filteredRecords.length === 0) {
        timeline.innerHTML = '<li class="timeline-item"><div class="timeline-trade">No historical records available for this selected era filter.</div></li>';
        return;
      }

      if (currentTimelineViewMode === 'tenure') {
        // --- TENURE RANGES VIEW MODE ---
        // Group records chronologically by occupant signature (surname + forename or building_name + trade)
        const sortedAsc = [...filteredRecords].sort((a,b) => parseInt(a.year) - parseInt(b.year));
        const tenureBlocks = [];
        let currentBlock = null;

        const getOccupantSig = (r) => {
          const b = cleanStr(r.building_name);
          const s = cleanStr(r.surname);
          const f = cleanStr(r.forename);
          const t = cleanStr(r.trade);
          return b ? `${b}|${s}|${t}` : `${s}|${f}|${t}`;
        };

        sortedAsc.forEach(r => {
          const sig = getOccupantSig(r);
          if (!currentBlock || currentBlock.sig !== sig) {
            currentBlock = {
              sig: sig,
              startYear: r.year,
              endYear: r.year,
              records: [r]
            };
            tenureBlocks.push(currentBlock);
          } else {
            currentBlock.endYear = r.year;
            currentBlock.records.push(r);
          }
        });

        // Render tenure blocks descending (most recent tenure top)
        tenureBlocks.reverse().forEach(block => {
          const isSpan = block.startYear !== block.endYear;
          const startYrNum = parseInt(block.startYear);
          const endYrNum = parseInt(block.endYear);
          const totalYearsDuration = isSpan ? (endYrNum - startYrNum + 1) : 1;
          const displayYearLabel = isSpan ? `${block.startYear} – ${block.endYear}` : block.startYear;
          const spanBadgeLabel = isSpan ? `${totalYearsDuration} Years Tenure` : `Directory Record`;

          const firstRec = block.records[0];
          const era = getEraTag(block.endYear);

          let occupantsHTML = '';
          // Deduplicate occupants inside tenure block if same person appears multiple times
          const dedupedBlockRecords = [];
          const seenSig = new Set();
          block.records.forEach(r => {
            const key = `${r.surname}|${r.forename}|${r.building_name}|${r.trade}`;
            if (!seenSig.has(key)) {
              seenSig.add(key);
              dedupedBlockRecords.push(r);
            }
          });

          dedupedBlockRecords.forEach(r => {
            const displayTrade = cleanOccupation(r.trade);
            const expandedForename = expandForename(r.forename);
            const fullResidentName = `${expandedForename} ${r.surname}`.trim();

            const searchNameHash = `#search=${encodeURIComponent(fullResidentName)}`;
            const searchTradeHash = `#search=${encodeURIComponent(displayTrade)}`;

            const encSt = encodeURIComponent(r.street || '');
            const encHn = encodeURIComponent(r.house_number || '');
            const encBn = encodeURIComponent(r.building_name || '');
            const encSn = encodeURIComponent(r.surname || '');
            const encFn = encodeURIComponent(r.forename || '');
            const encTr = encodeURIComponent(r.trade || '');

            const escFn = (str) => (str || '').replace(/'/g, "\\'");

            const bName = (r.building_name || '').trim();
            const trdName = (r.trade || '').trim();
            const isPubTrade = /vaults|inn|hotel|tavern|arms|bar|saloon|club|laboratory/i.test(trdName);
            const effectiveBldgName = bName || (isPubTrade ? trdName : '');

            let primaryTitleHTML = '';
            let subtitleHTML = '';

            if (fullResidentName) {
              primaryTitleHTML = `<a href="${searchNameHash}" class="timeline-name clickable-occupant-name" title="Search all records for ${fullResidentName}">${fullResidentName}</a>`;
              if (effectiveBldgName) {
                const searchBldgHash = `#search=${encodeURIComponent(effectiveBldgName)}`;
                subtitleHTML += `<div style="font-size: 0.95rem; color: #e2d7c5; font-weight: 500; margin-top: 0.15rem;">🏠 House Name: <a href="${searchBldgHash}" class="clickable-occupant-name" style="color: #ffffff; text-decoration: underline;" title="Search all records for ${effectiveBldgName}">${effectiveBldgName}</a></div>`;
              }
              if (displayTrade && displayTrade !== 'Residence / Private' && displayTrade.toLowerCase() !== effectiveBldgName.toLowerCase()) {
                subtitleHTML += `<div><a href="${searchTradeHash}" class="timeline-trade clickable-trade-tag" title="Search all ${displayTrade} entries">${displayTrade}</a></div>`;
              }
            } else {
              const searchBldgHash = `#search=${encodeURIComponent(effectiveBldgName)}`;
              primaryTitleHTML = `<a href="${searchBldgHash}" class="timeline-name clickable-occupant-name" title="Search all records for ${effectiveBldgName}">${effectiveBldgName}</a>`;
              if (displayTrade && displayTrade !== 'Residence / Private' && displayTrade.toLowerCase() !== effectiveBldgName.toLowerCase()) {
                subtitleHTML += `<div><a href="${searchTradeHash}" class="timeline-trade clickable-trade-tag" title="Search all ${displayTrade} entries">${displayTrade}</a></div>`;
              }
            }

            occupantsHTML += `
              <div class="occupant-entry" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                  ${primaryTitleHTML}
                  ${subtitleHTML}
                </div>
                <div style="display: flex; gap: 0.35rem; align-items: center;">
                  <button class="btn-edit-record" onclick="openScanInspectorModal('${r.year}', '${escFn(r.street)}', '${escFn(r.house_number)}')" style="border-color: var(--accent-muted); color: var(--accent);" title="View original directory scan page image for ${r.year}">📷 Scan</button>
                  <button class="btn-edit-record" onclick="openRecordEditorModal('${r.year}', '${escFn(r.street)}', '${escFn(r.house_number)}', '${escFn(r.building_name)}', '${escFn(r.surname)}', '${escFn(r.forename)}', '${escFn(r.trade)}')" title="Correct this property record">✏️ Edit</button>
                </div>
              </div>
            `;
          });

          const isSecondary = firstRec && firstRec.source_type === 'Secondary';
          const sourceBadgeHTML = isSecondary 
            ? `<span class="source-badge source-badge-secondary" title="Secondary Source: Historical Research / Manual Record">Research</span>`
            : `<span class="source-badge source-badge-primary" title="Primary Source: Published Street Directory">Directory</span>`;

          const li = document.createElement('li');
          li.className = 'timeline-item';
          li.innerHTML = `
            <div class="timeline-card">
              <div class="timeline-top">
                <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                  <span class="timeline-year" style="font-size: 1.5rem; letter-spacing: -0.02em;">${displayYearLabel}</span>
                  ${sourceBadgeHTML}
                  <span style="font-size: 0.72rem; font-weight: 600; color: var(--accent); background: rgba(200, 157, 84, 0.12); padding: 0.18rem 0.5rem; border-radius: 10px;">${spanBadgeLabel}</span>
                </div>
                <span class="era-badge">${era}</span>
              </div>
              <div class="occupants-list">
                ${occupantsHTML}
              </div>
              <div class="timeline-meta">
                <span>Recorded in ${[...new Set(block.records.map(r => r.year))].length} Directory Edition${[...new Set(block.records.map(r => r.year))].length > 1 ? 's' : ''} (${[...new Set(block.records.map(r => r.year))].join(', ')})</span>
              </div>
            </div>
          `;
          timeline.appendChild(li);
        });

      } else {
        // --- INDIVIDUAL YEARLY EDITIONS VIEW MODE ---
        const yearGroupsMap = new Map();
        filteredRecords.forEach(r => {
          if (!yearGroupsMap.has(r.year)) {
            yearGroupsMap.set(r.year, []);
          }
          yearGroupsMap.get(r.year).push(r);
        });

        const sortedYears = Array.from(yearGroupsMap.keys()).sort((a,b) => parseInt(b) - parseInt(a));

        sortedYears.forEach((yr, idx) => {
          const yearRecords = yearGroupsMap.get(yr);
          const era = getEraTag(yr);
          
          let occupantsHTML = '';
          yearRecords.forEach(r => {
            const displayTrade = cleanOccupation(r.trade);
            const expandedForename = expandForename(r.forename);
            const fullResidentName = `${expandedForename} ${r.surname}`.trim();

            const searchNameHash = `#search=${encodeURIComponent(fullResidentName)}`;
            const searchTradeHash = `#search=${encodeURIComponent(displayTrade)}`;

            const encSt = encodeURIComponent(r.street || '');
            const encHn = encodeURIComponent(r.house_number || '');
            const encBn = encodeURIComponent(r.building_name || '');
            const encSn = encodeURIComponent(r.surname || '');
            const encFn = encodeURIComponent(r.forename || '');
            const encTr = encodeURIComponent(r.trade || '');

            const escFn = (str) => (str || '').replace(/'/g, "\\'");

            if (r.surname && r.surname.toLowerCase().startsWith('see ')) {
              const targetStreet = r.surname.substring(4).trim();
              occupantsHTML += `
                <div class="occupant-entry cross-ref-entry" style="font-style: italic; opacity: 0.9; display: flex; justify-content: space-between; align-items: center;">
                  <div>👉 Directory Cross-Reference: <a href="#street=${encodeURIComponent(targetStreet)}" class="timeline-name clickable-occupant-name" style="color: #c89d54; text-decoration: underline; font-weight: 500;">See ${targetStreet}</a></div>
                  <button class="record-edit-btn" onclick="openTimelineRecordEditor(event, '${r.year}', '${escFn(encSt)}', '${escFn(encHn)}', '${escFn(encBn)}', '${escFn(encSn)}', '${escFn(encFn)}', '${escFn(encTr)}')">✏️ Edit</button>
                </div>
              `;
            } else {
              let primaryTitleHTML = '';
              let subtitleHTML = '';

              const bName = (r.building_name || '').trim();
              const trdName = (r.trade || '').trim();
              const isPubTrade = /vaults|inn|hotel|tavern|arms|bar|saloon|club|laboratory/i.test(trdName);
              const isBldgTrade = /masons?|grocers?|blacksmiths?|butchers?|engineers?|drapers?|labourers?|painters?|fitters?|clerks?|merchants?|tailors?|shoemakers?|shoerepairers?|builders?|contractors?|hauliers?|bakers?|carpenters?|printers?/i.test(bName);

              const effectiveBldgName = bName || (isPubTrade ? trdName : '');

              if (fullResidentName) {
                primaryTitleHTML = `<a href="${searchNameHash}" class="timeline-name clickable-occupant-name" title="Search all records for ${fullResidentName}">${fullResidentName}</a>`;
                if (effectiveBldgName) {
                  const searchBldgHash = `#search=${encodeURIComponent(effectiveBldgName)}`;
                  subtitleHTML += `<div style="font-size: 0.95rem; color: #e2d7c5; font-weight: 500; margin-top: 0.15rem;">🏠 House Name: <a href="${searchBldgHash}" class="clickable-occupant-name" style="color: #ffffff; text-decoration: underline;" title="Search all records for ${effectiveBldgName}">${effectiveBldgName}</a> ${isBldgTrade ? '<span style="font-size: 0.7rem; background: rgba(245, 101, 101, 0.2); color: #f56565; padding: 0.1rem 0.35rem; border-radius: 3px; margin-left: 0.3rem;" title="Trade may be trapped in House Name field">💡 Trade in House Name?</span>' : ''}</div>`;
                }
                if (displayTrade && displayTrade !== 'Residence / Private' && displayTrade.toLowerCase() !== effectiveBldgName.toLowerCase()) {
                  subtitleHTML += `<div><a href="${searchTradeHash}" class="timeline-trade clickable-trade-tag" title="Search all ${displayTrade} entries">${displayTrade}</a></div>`;
                }
              } else {
                const searchBldgHash = `#search=${encodeURIComponent(effectiveBldgName)}`;
                primaryTitleHTML = `<a href="${searchBldgHash}" class="timeline-name clickable-occupant-name" title="Search all records for ${effectiveBldgName}">${effectiveBldgName}</a>`;
                if (displayTrade && displayTrade !== 'Residence / Private' && displayTrade.toLowerCase() !== effectiveBldgName.toLowerCase()) {
                  subtitleHTML += `<div><a href="${searchTradeHash}" class="timeline-trade clickable-trade-tag" title="Search all ${displayTrade} entries">${displayTrade}</a></div>`;
                }
              }

              occupantsHTML += `
                <div class="occupant-entry" style="display: flex; justify-content: space-between; align-items: flex-start;">
                  <div>
                    ${primaryTitleHTML}
                    ${subtitleHTML}
                  </div>
                  <button class="record-edit-btn" onclick="openTimelineRecordEditor(event, '${r.year}', '${escFn(encSt)}', '${escFn(encHn)}', '${escFn(encBn)}', '${escFn(encSn)}', '${escFn(encFn)}', '${escFn(encTr)}')">✏️ Edit</button>
                </div>
              `;
            }
          });

          const firstRec = yearRecords[0];
          const isSecondary = firstRec && firstRec.source_type === 'Secondary';
          const sourceBadgeHTML = isSecondary 
            ? `<span class="source-badge source-badge-secondary" title="Secondary Source: Historical Research / Manual Record">Research</span>`
            : `<span class="source-badge source-badge-primary" title="Primary Source: Published Street Directory">Directory</span>`;

          const li = document.createElement('li');
          li.className = 'timeline-item';
          li.innerHTML = `
            <div class="timeline-card">
              <div class="timeline-top">
                <div style="display: flex; align-items: center;">
                  <span class="timeline-year">${yr}</span>
                  ${sourceBadgeHTML}
                </div>
                <span class="era-badge">${era}</span>
              </div>
              <div class="occupants-list">
                ${occupantsHTML}
              </div>
              <div class="timeline-meta">
                <span>${yearRecords.length} Occupant${yearRecords.length > 1 ? 's' : ''}</span>
              </div>
            </div>
          `;
          timeline.appendChild(li);
        });
      }
    }

    function renderDirectoriesView() {
      const container = document.getElementById('library-grid');
      if (!container) return;

      // Define our directories list
      // Processed directories have metadata (like record counts)
      // Unprocessed directories are placeholders for the 1848-1974 range
      const directories = [
        { year: 1848, name: "Hunt's Directory", processed: false },
        { year: 1850, name: "Scammell's Directory", processed: false },
        { year: 1865, name: "Morris' Directory", processed: false },
        { year: 1878, name: "Johns' Directory", processed: true, records: 3267 },
        { year: 1880, name: "Johns' Directory", processed: false },
        { year: 1887, name: "Johns' Directory", processed: true, records: 7226 },
        { year: 1890, name: "Johns' Directory", processed: true, records: 10222 },
        { year: 1893, name: "Johns' Directory", processed: true, records: 10637 },
        { year: 1894, name: "Johns' Directory", processed: true, records: 10549 },
        { year: 1897, name: "Johns' Directory", processed: false },
        { year: 1898, name: "Johns' Directory", processed: true, records: 12602 },
        { year: 1899, name: "Johns' Directory", processed: true, records: 13023 },
        { year: 1901, name: "Johns' Directory", processed: false },
        { year: 1902, name: "Johns' Directory", processed: true, records: 14223 },
        { year: 1903, name: "Johns' Directory", processed: true, records: 15809 },
        { year: 1905, name: "Johns' Directory", processed: false },
        { year: 1910, name: "Johns' Directory", processed: true, records: 12384 },
        { year: 1914, name: "Johns' Directory", processed: false },
        { year: 1920, name: "Johns' Directory", processed: false },
        { year: 1927, name: "Johns' Directory", processed: true, records: 19069 },
        { year: 1933, name: "Johns' Directory", processed: false },
        { year: 1936, name: "Johns' Directory", processed: true, records: 40925 },
        { year: 1938, name: "Johns' Directory", processed: false },
        { year: 1946, name: "Johns' Directory", processed: false },
        { year: 1950, name: "Johns' Directory", processed: false },
        { year: 1961, name: "Johns' Directory", processed: false },
        { year: 1971, name: "Johns' Directory", processed: true, records: 40925 },
        { year: 1974, name: "Johns' Directory", processed: false }
      ];

      // Sort chronological
      directories.sort((a, b) => a.year - b.year);

      container.innerHTML = '';
      let colorIndex = 1;

      directories.forEach(d => {
        const div = document.createElement('div');
        div.className = 'book-container';
        
        if (d.processed) {
          const colorClass = `book-color-${colorIndex}`;
          colorIndex = (colorIndex % 5) + 1; // Cycle 1-5 colors
          
          div.innerHTML = `
            <div class="book book-processed ${colorClass}" onclick="window.location.hash = '#directories=${d.year}'">
              <div class="book-spine-accent"></div>
              <div class="book-cover">
                <div class="book-title">${d.name}</div>
                <div class="book-year">${d.year}</div>
                <div class="book-meta">View Streets</div>
              </div>
            </div>
            <span class="book-label">${d.name} (${d.year})</span>
            <span class="book-status-badge badge-processed">${d.records.toLocaleString()} Records</span>
          `;
        } else {
          div.innerHTML = `
            <div class="book book-unprocessed">
              <div class="book-spine-accent"></div>
              <div class="book-cover">
                <div class="book-title">${d.name}</div>
                <div class="book-year">${d.year}</div>
                <div class="book-meta">Archived</div>
              </div>
            </div>
            <span class="book-label">${d.name} (${d.year})</span>
            <span class="book-status-badge badge-unprocessed">Awaiting OCR</span>
          `;
        }
        container.appendChild(div);
      });
    }

    // --- Interactive Record Editor State & Functions ---
    let currentEditingRecord = null;
    let sessionOverrides = [];

    function toggleEntryTypeFields() {
      const type = document.getElementById('edit-entry-type').value;
      const groupForename = document.getElementById('group-forename');
      const labelSurname = document.getElementById('label-surname');

      if (type === 'Business') {
        if (groupForename) groupForename.style.display = 'none';
        if (labelSurname) labelSurname.innerText = 'Commercial / Business Name';
      } else if (type === 'Cross-Reference') {
        if (groupForename) groupForename.style.display = 'none';
        if (labelSurname) labelSurname.innerText = 'Cross-Reference Pointer (e.g. See Stow Hill)';
      } else {
        if (groupForename) groupForename.style.display = 'flex';
        if (labelSurname) labelSurname.innerText = 'Surname';
      }
    }

    async function openRecordEditor(event, encodedStreet, encodedKey) {
      if (event && event.stopPropagation) event.stopPropagation();
      if (event && event.preventDefault) event.preventDefault();

      try {
        const street = decodeURIComponent(encodedStreet);
        const key = decodeURIComponent(encodedKey);
        
        const streetData = await loadStreetData(street);
        const records = streetData.records || [];
        
        // Find matching records for key
        const cleanKeyStr = cleanStr(key);
        const matchingRecs = records.filter(r => {
          const hNum = cleanStr(r.house_number);
          const bName = cleanStr(r.building_name);
          const name = cleanStr(`${r.forename} ${r.surname}`);
          return (hNum && (hNum === cleanKeyStr || cleanKeyStr.includes(hNum) || cleanKeyStr.includes(hNum))) ||
                 (bName && (bName === cleanKeyStr || cleanKeyStr.includes(bName))) ||
                 (name && (name === cleanKeyStr || cleanKeyStr.includes(name)));
        });

        const rec = matchingRecs.length ? matchingRecs[0] : { street, year: '1938', house_number: key };

        openTimelineRecordEditor(
          null,
          rec.year || '1938',
          encodeURIComponent(street),
          encodeURIComponent(rec.house_number || key),
          encodeURIComponent(rec.building_name || ''),
          encodeURIComponent(rec.surname || ''),
          encodeURIComponent(rec.forename || ''),
          encodeURIComponent(rec.trade || '')
        );
      } catch (err) {
        console.error("Error in openRecordEditor:", err);
      }
    }

    function openTimelineRecordEditor(event, yr, encStreet, encHouseNum, encBldgName, encSurname, encForename, encTrade) {
      if (event && event.stopPropagation) event.stopPropagation();
      if (event && event.preventDefault) event.preventDefault();

      try {
        const street = decodeURIComponent(encStreet || '');
        const houseNum = decodeURIComponent(encHouseNum || '');
        const bldgName = decodeURIComponent(encBldgName || '');
        const surname = decodeURIComponent(encSurname || '');
        const forename = decodeURIComponent(encForename || '');
        const trade = decodeURIComponent(encTrade || '');

        currentEditingRecord = {
          street, year: yr, house_number: houseNum, building_name: bldgName,
          surname, forename, trade
        };

        document.getElementById('edit-street').value = street;
        document.getElementById('edit-year').value = yr;
        document.getElementById('edit-house-number').value = houseNum;
        document.getElementById('edit-sub-unit').value = '';
        document.getElementById('edit-building-name').value = bldgName;
        document.getElementById('edit-surname').value = surname;
        document.getElementById('edit-forename').value = forename;
        document.getElementById('edit-trade').value = trade;
        document.getElementById('edit-reason').value = `${street}: Standardized record formatting for house ${houseNum || bldgName}`;

        const entryType = (surname.toLowerCase().startsWith('see ')) ? 'Cross-Reference' :
                          (!forename && (surname.includes('&') || surname.toLowerCase().includes('ltd') || surname.toLowerCase().includes('club') || surname.toLowerCase().includes('co'))) ? 'Business' : 'Person';

        document.getElementById('edit-entry-type').value = entryType;
        toggleEntryTypeFields();

        const delBtn = document.getElementById('btn-delete-record');
        if (delBtn) delBtn.style.display = 'inline-block';

        document.getElementById('editor-modal-backdrop').classList.add('active');
      } catch (err) {
        console.error("Error in openTimelineRecordEditor:", err);
      }
    }

    function swapBuildingNameAndTrade() {
      const bldgElem = document.getElementById('edit-building-name');
      const tradeElem = document.getElementById('edit-trade');
      if (!bldgElem || !tradeElem) return;

      const oldBldg = bldgElem.value;
      const oldTrade = tradeElem.value;

      bldgElem.value = oldTrade;
      tradeElem.value = oldBldg;

      const reasonElem = document.getElementById('edit-reason');
      if (reasonElem) {
        reasonElem.value = `Swapped House Name ("${oldBldg}") and Trade ("${oldTrade}") fields.`;
      }
    }

    function openAddPropertyModal() {
      const street = document.getElementById('street-heading') ? document.getElementById('street-heading').innerText : '';

      currentEditingRecord = null;
      const delBtn = document.getElementById('btn-delete-record');
      if (delBtn) delBtn.style.display = 'none';

      document.getElementById('edit-street').value = street;
      document.getElementById('edit-year').value = '';
      document.getElementById('edit-house-number').value = '';
      document.getElementById('edit-sub-unit').value = '';
      document.getElementById('edit-building-name').value = '';
      document.getElementById('edit-surname').value = '';
      document.getElementById('edit-forename').value = '';
      document.getElementById('edit-trade').value = '';
      document.getElementById('edit-source-type').value = 'Secondary';
      document.getElementById('edit-entry-type').value = 'Person';
      document.getElementById('edit-reason').value = `${street}: Added new property and record`;

      toggleEntryTypeFields();
      document.getElementById('editor-modal-backdrop').classList.add('active');
    }

    function openAddRecordModal() {
      const street = document.getElementById('house-street-display') ? document.getElementById('house-street-display').innerText : '';
      const houseNum = document.getElementById('house-number-display') ? document.getElementById('house-number-display').innerText : '';

      currentEditingRecord = null;
      const delBtn = document.getElementById('btn-delete-record');
      if (delBtn) delBtn.style.display = 'none';

      document.getElementById('edit-street').value = street;
      document.getElementById('edit-year').value = '';
      document.getElementById('edit-house-number').value = houseNum;
      document.getElementById('edit-sub-unit').value = '';
      document.getElementById('edit-building-name').value = '';
      document.getElementById('edit-surname').value = '';
      document.getElementById('edit-forename').value = '';
      document.getElementById('edit-trade').value = '';
      document.getElementById('edit-source-type').value = 'Secondary';
      document.getElementById('edit-entry-type').value = 'Person';
      document.getElementById('edit-reason').value = `${street}: Added gap-year historical research record for No. ${houseNum}`;

      toggleEntryTypeFields();
      document.getElementById('editor-modal-backdrop').classList.add('active');
    }

    function closeEditorModal() {
      document.getElementById('editor-modal-backdrop').classList.remove('active');
    }

    function deleteCurrentRecord() {
      if (!currentEditingRecord) return;
      const street = document.getElementById('edit-street').value.trim();
      const year = document.getElementById('edit-year').value.trim();
      const houseNum = document.getElementById('edit-house-number').value.trim();
      const surname = document.getElementById('edit-surname').value.trim();

      if (!confirm(`Are you sure you want to delete/exclude this record (${surname} - ${year})?`)) return;

      const overrideObj = {
        reason: `${street} ${year}: Excluded redundant/invalid record (${surname}).`,
        match: {
          street: street,
          year: year
        },
        action: "exclude"
      };

      if (surname) {
        overrideObj.match.surname_contains = surname.substring(0, 8);
      } else if (houseNum) {
        overrideObj.match.house_number = houseNum;
      }

      sessionOverrides.push(overrideObj);
      saveSessionToLocalStorage();
      updateOverrideDrawer();
      closeEditorModal();

      // Remove from local in-memory preview cache
      if (streetCacheMap.has(cleanSlug(street))) {
        const cached = streetCacheMap.get(cleanSlug(street));
        if (cached && cached.records) {
          const targetSur = cleanStr(surname);
          cached.records = cached.records.filter(r => !(r.year === year && cleanStr(r.surname) === targetSur));
        }
      }

      navigate();
    }

    function saveRecordCorrection() {
      const street = document.getElementById('edit-street').value.trim();
      const year = document.getElementById('edit-year').value.trim();
      const houseNum = document.getElementById('edit-house-number').value.trim();
      const subUnit = document.getElementById('edit-sub-unit').value.trim();
      const bldgName = document.getElementById('edit-building-name').value.trim();
      const sourceType = document.getElementById('edit-source-type').value;
      const entryType = document.getElementById('edit-entry-type').value;
      const surname = document.getElementById('edit-surname').value.trim();
      const forename = (entryType === 'Person') ? document.getElementById('edit-forename').value.trim() : '';
      const trade = document.getElementById('edit-trade').value.trim();
      const reason = document.getElementById('edit-reason').value.trim();

      const overrideObj = {
        reason: reason || `${street} ${year}: Manual record correction.`,
        match: {
          street: street,
          year: year
        },
        apply: {
          house_number: houseNum,
          building_name: bldgName,
          surname: surname,
          forename: forename,
          trade: trade,
          source_type: sourceType
        }
      };

      if (currentEditingRecord && currentEditingRecord.surname) {
        overrideObj.match.surname_contains = currentEditingRecord.surname.substring(0, 8);
      } else if (houseNum) {
        overrideObj.match.house_number = houseNum;
      }

      if (subUnit) {
        overrideObj.apply.sub_unit = subUnit;
      }

      // Check if an override for this exact record already exists in active session
      const existingIdx = sessionOverrides.findIndex(ov => 
        ov.match &&
        ov.match.street === overrideObj.match.street &&
        ov.match.year === overrideObj.match.year &&
        (
          (ov.match.house_number && ov.match.house_number === overrideObj.match.house_number) ||
          (ov.match.surname_contains && ov.match.surname_contains === overrideObj.match.surname_contains)
        )
      );

      if (existingIdx !== -1) {
        sessionOverrides[existingIdx] = overrideObj;
      } else {
        sessionOverrides.push(overrideObj);
      }
      saveSessionToLocalStorage();
      updateOverrideDrawer();
      closeEditorModal();

      // Instant local preview update
      applyLocalOverridePreview(street, year, houseNum, currentEditingRecord, bldgName, surname, forename, trade);

      // Refresh current view
      navigate();
    }

    function applyLocalOverridePreview(street, year, houseNum, origRec, bldgName, surname, forename, trade, sourceType = 'Primary') {
      if (streetCacheMap.has(cleanSlug(street))) {
        const cached = streetCacheMap.get(cleanSlug(street));
        if (cached && cached.records) {
          const targetHouse = cleanStr(houseNum);
          const targetSurname = origRec && origRec.surname ? cleanStr(origRec.surname) : '';
          const targetBldg = origRec && origRec.building_name ? cleanStr(origRec.building_name) : '';

          const rec = cached.records.find(r => {
            if (r.year !== year) return false;
            const rHouse = cleanStr(r.house_number);
            const rSurname = cleanStr(r.surname);
            const rBldg = cleanStr(r.building_name);

            if (targetHouse && rHouse === targetHouse) return true;
            if (targetSurname && (rSurname === targetSurname || rSurname.includes(targetSurname))) return true;
            if (targetBldg && rBldg === targetBldg) return true;
            return false;
          });
          if (rec) {
            rec.house_number = houseNum;
            rec.building_name = bldgName;
            rec.surname = surname;
            rec.forename = forename;
            rec.trade = trade;
            rec.source_type = sourceType;
          } else {
            cached.records.push({
              year: year,
              street: street,
              house_number: houseNum,
              building_name: bldgName,
              surname: surname,
              forename: forename,
              trade: trade,
              source_type: sourceType
            });
          }
        }
      }
    }

    function saveSessionToLocalStorage() {
      try {
        localStorage.setItem('newport_session_overrides', JSON.stringify(sessionOverrides));
      } catch (e) {
        console.warn("LocalStorage save failed", e);
      }
    }

    function loadSessionFromLocalStorage() {
      try {
        const stored = localStorage.getItem('newport_session_overrides');
        if (stored) {
          sessionOverrides = JSON.parse(stored);
          updateOverrideDrawer();
          
          // Re-apply preview overrides to cached data
          sessionOverrides.forEach(ov => {
            if (ov.match && ov.apply) {
              applyLocalOverridePreview(
                ov.match.street,
                ov.match.year,
                ov.apply.house_number,
                { surname: ov.match.surname_contains || '' },
                ov.apply.building_name,
                ov.apply.surname,
                ov.apply.forename,
                ov.apply.trade
              );
            }
          });
        }
      } catch (e) {
        console.warn("LocalStorage load failed", e);
      }
    }

    function updateOverrideDrawer() {
      const drawer = document.getElementById('override-drawer');
      const badge = document.getElementById('override-count-badge');
      if (sessionOverrides.length > 0) {
        drawer.classList.add('active');
        badge.innerText = `${sessionOverrides.length} Override${sessionOverrides.length > 1 ? 's' : ''}`;
      } else {
        drawer.classList.remove('active');
      }
    }

    function clearSessionOverrides() {
      if (confirm("Clear all un-merged session edits?")) {
        sessionOverrides = [];
        localStorage.removeItem('newport_session_overrides');
        updateOverrideDrawer();
        location.reload();
      }
    }

    function copySessionOverrides() {
      if (sessionOverrides.length === 0) return;
      const jsonStr = JSON.stringify(sessionOverrides, null, 2);
      navigator.clipboard.writeText(jsonStr).then(() => {
        alert(`Copied ${sessionOverrides.length} JSON override rules to clipboard!\n\nYou can paste this into edge_cases.json or specify it with merge_overrides.py.`);
      });
    }

    function downloadSessionOverrides() {
      if (sessionOverrides.length === 0) return;
      const jsonStr = JSON.stringify(sessionOverrides, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'user_overrides.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      // Auto-clear active session queue after export so next batch starts fresh
      sessionOverrides = [];
      localStorage.removeItem('newport_session_overrides');
      updateOverrideDrawer();
    }

    // --- Editor Mode Authorization & Keyboard Shortcut (Option 2) ---
    function checkEditorMode() {
      const urlParams = new URLSearchParams(window.location.search);
      const isEditorQuery = urlParams.get('editor') === 'true' || urlParams.get('edit') === 'true';
      const isEditorStored = localStorage.getItem('newport_editor_mode') === 'true';

      if (isEditorQuery || isEditorStored) {
        document.body.classList.add('editor-mode');
        localStorage.setItem('newport_editor_mode', 'true');
      } else {
        document.body.classList.remove('editor-mode');
      }
    }

    function toggleEditorMode() {
      const isCurrent = document.body.classList.contains('editor-mode');
      if (isCurrent) {
        document.body.classList.remove('editor-mode');
        localStorage.setItem('newport_editor_mode', 'false');
        alert("🔒 Editor Mode Disabled. Site is now in Public Read-Only Mode.");
      } else {
        document.body.classList.add('editor-mode');
        localStorage.setItem('newport_editor_mode', 'true');
        alert("✏️ Editor Mode Enabled! Edit & Add Record buttons are now active.");
      }
    }

    // --- Master Street Registry Editor Modal Functions ---
    let currentEditingStreetSlug = '';

    async function openMasterRegistryModal(streetName = null) {
      let targetStreet = streetName || currentStreet;

      if (!targetStreet && window.location.hash.startsWith('#street=')) {
        targetStreet = decodeURIComponent(window.location.hash.substring(8)).trim();
      }

      if (!targetStreet) {
        alert("Please navigate to a specific street directory page first.");
        return;
      }

      const slug = cleanSlug(targetStreet);
      currentEditingStreetSlug = slug;

      let masterDict = {};
      try {
        const resp = await fetch(`master_streets.json?v=${Date.now()}`);
        if (resp.ok) {
          const data = await resp.json();
          masterDict = data.streets || {};
        }
      } catch (err) {
        console.warn("Could not load master_streets.json", err);
      }

      const entry = masterDict[slug] || {
        canonical_name: targetStreet,
        slug: slug,
        former_names: [],
        sub_sections: [],
        numbering_scheme: { type: 'ODDS_EVENS', changed_from: '', approx_change_year: null, notes: '' },
        district: '',
        parish: '',
        audit_status: 'UNVERIFIED',
        audit: { status: 'UNVERIFIED', notes: '' }
      };

      document.getElementById('reg-canonical-title').innerText = entry.canonical_name || targetStreet;
      document.getElementById('reg-slug-subtitle').innerText = `slug: ${slug}`;
      let initStatus = entry.audit_status || (entry.audit && entry.audit.status) || 'UNVERIFIED';
      if (initStatus === 'VERIFIED') initStatus = 'NAME_VERIFIED';
      document.getElementById('reg-status-select').value = initStatus;
      document.getElementById('reg-former-names').value = (entry.former_names || []).join(', ');
      document.getElementById('reg-renamed-to').value = entry.renamed_to || entry.modern_name || '';
      document.getElementById('reg-sub-sections').value = (entry.sub_sections || []).join(', ');
      document.getElementById('reg-numbering-type').value = (entry.numbering_scheme && entry.numbering_scheme.type) ? entry.numbering_scheme.type : 'ODDS_EVENS';
      document.getElementById('reg-numbering-year').value = (entry.numbering_scheme && entry.numbering_scheme.approx_change_year) ? entry.numbering_scheme.approx_change_year : '';
      document.getElementById('reg-district').value = entry.district || '';
      document.getElementById('reg-parish').value = entry.parish || '';
      const lat = entry.latitude || (entry.coordinates && entry.coordinates.lat) || '';
      const lng = entry.longitude || (entry.coordinates && entry.coordinates.lng) || '';
      const heading = entry.heading !== undefined ? entry.heading : '';
      document.getElementById('reg-latitude').value = lat;
      document.getElementById('reg-longitude').value = lng;
      document.getElementById('reg-heading').value = heading;
      document.getElementById('reg-notes').value = entry.notes || (entry.audit && entry.audit.notes) || '';

      const previewContainer = document.getElementById('reg-streetview-preview-container');
      const previewImg = document.getElementById('reg-streetview-img');
      const previewLink = document.getElementById('reg-streetview-link');
      if (lat && lng) {
        previewImg.src = `assets/images/streetview/${slug}.jpg`;
        previewLink.href = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`;
        previewContainer.style.display = 'block';
      } else {
        previewContainer.style.display = 'none';
      }

      document.getElementById('master-registry-modal-overlay').classList.add('active');
    }

    function closeMasterRegistryModal() {
      document.getElementById('master-registry-modal-overlay').classList.remove('active');
    }

    function saveMasterRegistryEntry() {
      if (!currentEditingStreetSlug) return;

      const formerNamesRaw = document.getElementById('reg-former-names').value;
      const renamedTo = document.getElementById('reg-renamed-to').value.trim();
      const subSectionsRaw = document.getElementById('reg-sub-sections').value;

      const former_names = formerNamesRaw.split(',').map(s => s.trim()).filter(Boolean);
      const sub_sections = subSectionsRaw.split(',').map(s => s.trim()).filter(Boolean);
      const status = document.getElementById('reg-status-select').value;
      const numberingType = document.getElementById('reg-numbering-type').value;
      const numberingYear = document.getElementById('reg-numbering-year').value;
      const district = document.getElementById('reg-district').value.trim();
      const parish = document.getElementById('reg-parish').value.trim();
      const latitude = document.getElementById('reg-latitude').value.trim();
      const longitude = document.getElementById('reg-longitude').value.trim();
      const heading = document.getElementById('reg-heading').value.trim();
      const notes = document.getElementById('reg-notes').value.trim();

      const registryOverride = {
        action: 'UPDATE_MASTER_REGISTRY',
        slug: currentEditingStreetSlug,
        audit_status: status,
        former_names: former_names,
        renamed_to: renamedTo,
        sub_sections: sub_sections,
        numbering_scheme: {
          type: numberingType,
          approx_change_year: numberingYear ? parseInt(numberingYear) : null
        },
        district: district,
        parish: parish,
        latitude: latitude,
        longitude: longitude,
        heading: heading !== '' ? parseFloat(heading) : null,
        coordinates: {
          lat: latitude ? parseFloat(latitude) : null,
          lng: longitude ? parseFloat(longitude) : null
        },
        notes: notes,
        timestamp: new Date().toISOString()
      };

      sessionOverrides.push(registryOverride);
      saveSessionToLocalStorage();
      updateOverrideDrawer();
      closeMasterRegistryModal();

      if (window.location.hash.startsWith('#street=')) {
        const rawStreet = decodeURIComponent(window.location.hash.substring(8));
        renderStreetView(rawStreet);
      } else if (window.location.hash === '#streets') {
        renderStreetsView();
      }
    }

    // --- Master Street CSV Export & Import ---
    async function exportMasterStreetsCSV() {
      let masterDict = {};
      try {
        const resp = await fetch('master_streets.json');
        if (resp.ok) {
          const data = await resp.json();
          masterDict = data.streets || {};
        }
      } catch (err) {
        console.warn("Could not fetch master_streets.json", err);
      }

      // Incorporate active session overrides into export
      sessionOverrides.filter(o => o.action === 'UPDATE_MASTER_REGISTRY').forEach(o => {
        masterDict[o.slug] = {
          canonical_name: masterDict[o.slug] ? masterDict[o.slug].canonical_name : o.slug,
          slug: o.slug,
          audit: { status: o.audit_status, notes: o.notes || '' },
          former_names: o.former_names || [],
          sub_sections: o.sub_sections || [],
          numbering_scheme: o.numbering_scheme || { type: 'ODDS_EVENS' },
          district: o.district || '',
          parish: o.parish || '',
          coordinates: o.coordinates || { lat: null, lng: null }
        };
      });

      const headers = ["slug", "canonical_name", "audit_status", "former_names", "sub_sections", "numbering_type", "renumbering_year", "district", "parish", "latitude", "longitude", "notes"];
      const csvRows = [headers.join(",")];

      masterStreetsList.forEach(s => {
        const slug = cleanStr(s.displayName).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        const entry = masterDict[slug] || {
          canonical_name: s.displayName,
          slug: slug,
          audit: { status: s.auditStatus || 'UNVERIFIED', notes: '' },
          former_names: [],
          sub_sections: [],
          numbering_scheme: { type: 'ODDS_EVENS' },
          district: '',
          parish: '',
          coordinates: { lat: null, lng: null }
        };

        const escapeCSV = (val) => `"${String(val || '').replace(/"/g, '""')}"`;

        const row = [
          escapeCSV(slug),
          escapeCSV(entry.canonical_name || s.displayName),
          escapeCSV(entry.audit ? entry.audit.status : 'UNVERIFIED'),
          escapeCSV((entry.former_names || []).join('; ')),
          escapeCSV((entry.sub_sections || []).join('; ')),
          escapeCSV(entry.numbering_scheme ? entry.numbering_scheme.type : 'ODDS_EVENS'),
          escapeCSV(entry.numbering_scheme ? entry.numbering_scheme.approx_change_year : ''),
          escapeCSV(entry.district || ''),
          escapeCSV(entry.parish || ''),
          escapeCSV(entry.coordinates ? entry.coordinates.lat : ''),
          escapeCSV(entry.coordinates ? entry.coordinates.lng : ''),
          escapeCSV(entry.audit ? entry.audit.notes : '')
        ];
        csvRows.push(row.join(","));
      });

      const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(csvRows.join("\n"));
      const dlAnchor = document.createElement('a');
      dlAnchor.setAttribute("href", csvContent);
      dlAnchor.setAttribute("download", `master_streets_export_${new Date().toISOString().slice(0,10)}.csv`);
      document.body.appendChild(dlAnchor);
      dlAnchor.click();
      dlAnchor.remove();
    }

    function importMasterStreetsCSV(event) {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.split(/\r?\n/).filter(Boolean);
        if (lines.length < 2) return;

        let importCount = 0;
        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(/,(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)/).map(c => c.replace(/^"|"$/g, '').replace(/""/g, '"').trim());
          if (cols.length >= 3 && cols[0]) {
            const slug = cols[0];
            const status = cols[2] || 'UNVERIFIED';
            const former_names = cols[3] ? cols[3].split(';').map(x => x.trim()).filter(Boolean) : [];
            const sub_sections = cols[4] ? cols[4].split(';').map(x => x.trim()).filter(Boolean) : [];
            const numberingType = cols[5] || 'ODDS_EVENS';
            const numberingYear = cols[6] ? parseInt(cols[6]) : null;
            const district = cols[7] || '';
            const parish = cols[8] || '';
            const lat = cols[9] ? parseFloat(cols[9]) : null;
            const lng = cols[10] ? parseFloat(cols[10]) : null;
            const notes = cols[11] || '';

            sessionOverrides.push({
              action: 'UPDATE_MASTER_REGISTRY',
              slug: slug,
              audit_status: status,
              former_names: former_names,
              sub_sections: sub_sections,
              numbering_scheme: { type: numberingType, approx_change_year: numberingYear },
              district: district,
              parish: parish,
              coordinates: { lat: lat, lng: lng },
              notes: notes,
              timestamp: new Date().toISOString()
            });
            importCount++;
          }
        }

        saveSessionToLocalStorage();
        updateOverrideDrawer();
        renderStreetsView();
        alert(`📥 Successfully imported ${importCount} street records from CSV into your active session queue!`);
      };
      reader.readAsText(file);
    }

    window.addEventListener('keydown', (e) => {
      // Toggle Editor Mode on Cmd + Shift + E (Mac) or Ctrl + Shift + E (Windows)
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'E' || e.key === 'e')) {
        e.preventDefault();
        toggleEditorMode();
      }

      // Save on Enter key inside active editor modals
      if (e.key === 'Enter' && !e.shiftKey) {
        const propModal = document.getElementById('editor-modal-backdrop');
        const regModal = document.getElementById('master-registry-modal-overlay');
        
        if (propModal && propModal.classList.contains('active')) {
          e.preventDefault();
          saveRecordCorrection();
        } else if (regModal && regModal.classList.contains('active')) {
          e.preventDefault();
          saveMasterRegistryEntry();
        }
      }
    });

    window.addEventListener('hashchange', navigate);
    window.addEventListener('DOMContentLoaded', async () => {
      checkEditorMode();
      await loadMasterStreets();
      loadSessionFromLocalStorage();
      await navigate();
    });

    // --- Original Directory Scan Inspector Logic ---
    let scansIndex = null;
    let currentScanYear = null;
    let currentScanPageIdx = 0;
    let currentScanZoomLevel = 1.0;

    async function loadScansIndex() {
      if (scansIndex) return scansIndex;
      try {
        const resp = await fetch('data/scans_index.json');
        scansIndex = await resp.json();
        return scansIndex;
      } catch (err) {
        console.error("Failed loading data/scans_index.json", err);
        return {};
      }
    }

    async function openScanInspectorModal(year, streetName = '', houseNum = '', lineIdx = -1) {
      const modal = document.getElementById('scan-inspector-modal');
      const subtitle = document.getElementById('scan-modal-subtitle');

      if (!modal) return;

      const idxData = await loadScansIndex();
      const yrStr = String(year);
      const fileList = idxData[yrStr] || [];

      if (!fileList.length) {
        alert(`No original page scans indexed for the ${year} directory edition.`);
        return;
      }

      currentScanYear = yrStr;
      currentScanPageIdx = 0;
      currentScanZoomLevel = 1.0;
      resetScanZoom();

      subtitle.innerText = `${year} Johns Directory • ${streetName || 'Archive Volume'}`;
      
      updateScanModalDisplay(fileList, lineIdx);
      modal.style.display = 'flex';
    }

    function updateScanModalDisplay(fileList, lineIdx = -1) {
      const img = document.getElementById('scan-modal-img');
      const highlightBox = document.getElementById('scan-highlight-box');
      const pageCounter = document.getElementById('scan-page-counter');
      const openRawBtn = document.getElementById('scan-open-raw-btn');

      if (!fileList || !fileList.length) return;

      if (currentScanPageIdx < 0) currentScanPageIdx = 0;
      if (currentScanPageIdx >= fileList.length) currentScanPageIdx = fileList.length - 1;

      const imagePath = fileList[currentScanPageIdx];
      img.src = imagePath;
      openRawBtn.href = imagePath;
      pageCounter.innerText = `Page ${currentScanPageIdx + 1} of ${fileList.length}`;

      if (lineIdx >= 0) {
        highlightBox.style.display = 'block';
        const estimatedTop = 140 + (lineIdx * 24);
        highlightBox.style.top = `${estimatedTop}px`;
      } else {
        highlightBox.style.display = 'none';
      }
    }

    function changeScanPage(delta) {
      if (!scansIndex || !currentScanYear) return;
      const fileList = scansIndex[currentScanYear] || [];
      currentScanPageIdx += delta;
      updateScanModalDisplay(fileList);
    }

    function zoomScan(delta) {
      currentScanZoomLevel += delta;
      if (currentScanZoomLevel < 0.5) currentScanZoomLevel = 0.5;
      if (currentScanZoomLevel > 3.0) currentScanZoomLevel = 3.0;

      const wrapper = document.getElementById('scan-image-wrapper');
      if (wrapper) {
        wrapper.style.transform = `scale(${currentScanZoomLevel})`;
      }
    }

    function resetScanZoom() {
      currentScanZoomLevel = 1.0;
      const wrapper = document.getElementById('scan-image-wrapper');
      if (wrapper) {
        wrapper.style.transform = `scale(1.0)`;
      }
    }

    function closeScanInspectorModal() {
      const modal = document.getElementById('scan-inspector-modal');
      if (modal) modal.style.display = 'none';
    }

    // Attach scan functions to window for global access
    window.openScanInspectorModal = openScanInspectorModal;
    window.closeScanInspectorModal = closeScanInspectorModal;
    window.changeScanPage = changeScanPage;
    window.zoomScan = zoomScan;
    window.resetScanZoom = resetScanZoom;
