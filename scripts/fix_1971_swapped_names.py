#!/usr/bin/env python3
import csv
import re
import os
import sys

# Ensure field limit is high enough
csv.field_size_limit(sys.maxsize)

INPUT_CSV = "data.csv"
OUTPUT_CSV = "data.csv"

TITLES = {
    'mr', 'mrs', 'miss', 'ms', 'dr', 'rev', 'capt', 'col', 'maj', 'major', 'sergt', 
    'father', 'fr', 'messrs', 'sir', 'lord', 'lady', 'prof', 'ald', 'alderman', 'councillor', 'cllr'
}

COMMON_FORENAMES = {
    'john', 'william', 'thomas', 'james', 'george', 'charles', 'henry', 'david', 'richard', 
    'robert', 'edward', 'frederick', 'albert', 'joseph', 'harry', 'frank', 'walter', 
    'harold', 'herbert', 'alfred', 'reginald', 'sidney', 'leslie', 'horace', 'cyril', 'norman', 
    'stanley', 'clifford', 'ronald', 'leonard', 'victor', 'eric', 'kenneth', 'edwin', 'raymond', 
    'percival', 'percy', 'dennis', 'trevor', 'bernard', 'donald', 'brian', 'derek', 'gerald', 
    'graham', 'terence', 'anthony', 'alan', 'allan', 'colin', 'keith', 'gordon', 'malcolm', 
    'nevil', 'neville', 'stewart', 'stuart', 'barry', 'bryan', 'clive', 'douglas', 'geoffrey', 
    'jeffrey', 'nigel', 'peter', 'philip', 'roger', 'stephen', 'steven', 'ernest', 'arthur', 
    'samuel', 'benjamin', 'daniel', 'oscar', 'lawrence', 'francis', 'maurice', 'gilbert', 
    'godfrey', 'glyn', 'roy', 'desmond', 'valentine', 'ivan', 'ebenezer', 'michael', 'patrick', 
    'martin', 'clarence', 'russell', 'aubrey', 'lionel', 'rowland', 'laurence', 'julian', 
    'hubert', 'bertram', 'basil', 'wilfred', 'arnold', 'eynon', 'varney', 'sylgwyn', 'lyn', 
    'alun', 'bryn', 'ivor', 'gwilym', 'dillwyn', 'idris', 'hywel', 'geraint', 'rhys', 'gareth', 
    'emrys', 'tudor', 'mostyn', 'maldwyn', 'caradoc', 'wyn', 'wynne', 'wynford', 'arwyn', 
    'elvet', 'selwyn', 'morris', 'owain', 'eirwyn', 'howard', 'bruce', 
    'doug', 'ian', 'neil', 'adrian', 'timothy', 'nicholas', 'paul', 'mark', 'simon', 
    'christopher', 'jonathan', 'andrew', 'matthew', 'adam', 'luke', 'gregory', 'vincenzo', 'luigi', 'antonio', 'giovanni', 'mario', 'carlo', 'giuseppe', 'domenico', 'francesco', 'salvatore', 'angelo', 'pietro', 'gaetano', 'gianni', 'renato', 'bruno', 'paolo', 'stefano', 'enrico', 'marco', 'massimo', 'alberto', 'roberto', 'sergio', 'andrea', 'luca', 'dino', 'aldo', 'enzo', 'giacomo', 'giorgio', 'claudio', 'vittorio', 'marcello', 'guido', 'silvio', 'franco', 'pasquale', 'raffaele', 'rocco', 'sandro', 'umberto',
    # Abbreviations
    'thos', 'wm', 'jn', 'chas', 'edwd', 'geo', 'arth', 'hy', 'jas', 'albt', 'regnld', 'fredk', 
    'ernt', 'rt', 'rd', 'walt', 'herbt', 'alfd', 'sid', 'les', 'hor', 'cyr', 'norm', 
    'stan', 'cliff', 'ron', 'len', 'vic', 'ken', 'edw', 'ray', 'percevl', 'percev', 'den', 
    'trev', 'bern', 'don', 'bri', 'ger', 'gord', 'geoff', 'jeff', 'pete', 
    'phil', 'rog', 'steve', 'saml', 'fras', 'michl', 'danl', 'ebenzr', 'archbld', 'steph', 
    'christr', 'phlp', 'abrm', 'tim', 'dvd', 'stephn', 'reg', 'fred', 'bert', 'ern', 'davy', 
    'dave', 'bill', 'bob', 'jim', 'tom', 'dick', 'jack', 'ted', 'al', 'joe',
    # Female
    'mary', 'elizabeth', 'florence', 'emily', 'margaret', 'doris', 'gladys', 'edith', 'alice', 
    'ethel', 'lilian', 'hilda', 'winifred', 'violet', 'mabel', 'ivy', 'rose', 'ellen', 'sarah', 
    'beatrice', 'dorothy', 'olive', 'gwen', 'blanche', 'vera', 'constance', 'marjorie', 
    'kathleen', 'eileen', 'phyllis', 'joan', 'marion', 'joyce', 'brenda', 'audrey', 'sheila', 
    'patricia', 'maureen', 'beryl', 'pamela', 'shirley', 'barbara', 'doreen', 'iris', 'norma', 
    'nellie', 'harriet', 'annie', 'dora', 'gwendoline', 'irene', 'sylvia', 'rhoda', 'evelyn', 
    'ann', 'jane', 'catherine', 'katharine', 'eunice', 'mair', 'megan', 'bronwen', 'olwen', 
    'gwyneth', 'rhiannon', 'carys', 'sian', 'dilys', 'eluned', 'myfanwy', 'ceinwen', 'eira', 
    'morfydd', 'enid', 'gwynedd', 'nesta', 'hettie', 'maggie', 'minnie', 'jessie', 'may', 
    'elsie', 'ada', 'grace', 'daisy', 'clara', 'laura', 'agnes', 'lottie', 'fanny', 'hannah', 
    'leah', 'rachel', 'ruth', 'susannah', 'martha', 'emma', 'mrs', 'miss', 'madge', 'flossie', 
    'margt', 'mgt', 'dor', 'glad', 'eth', 'lil', 'win', 'vi', 'mabe', 'beatt', 'dot', 
    'ol', 'marj', 'kath', 'eil', 'phyl', 'pat', 'maur', 'pam', 'shirl', 'barb', 'dorn'
}

COMMON_SURNAMES = {
    'smith', 'jones', 'williams', 'davies', 'evans', 'roberts', 'lewis', 'hughes', 'morgan', 
    'griffiths', 'edwards', 'hill', 'moore', 'clark', 'wright', 'phillips', 'jenkins', 'powell', 
    'price', 'rees', 'owen', 'james', 'morris', 'richards', 'lloyd', 'martin', 'harrison', 
    'allen', 'baker', 'cook', 'clarke', 'taylor', 'brown', 'green', 'hall', 'harris', 'king', 
    'lee', 'mason', 'miller', 'parker', 'turner', 'walker', 'ward', 'watson', 'white', 'wilson', 
    'wood', 'young', 'antill', 'howells', 'sayer', 'wallis', 'berthon', 'cornford', 'fox', 
    'madden', 'limbrick', 'walters', 'weguelin', 'snell', 'daniels', 'arnold', 'thomas', 
    'maxfield', 'cording', 'bryant', 'davis', 'fry', 'reade', 'elliott', 'jewell', 'quick', 
    'brodie', 'edmonds', 'buttrey', 'sullivan', 'prince', 'hindson', 'laugharne', 'dobbie', 
    'tyson', 'barnes', 'lang', 'hando', 'parfitt', 'coughlan', 'cloud', 'perrot', 'rysdale', 
    'pollard', 'lavender', 'mcarthur', 'tombs', 'stokes', 'mancino', 
    'hooper', 'nurden', 'forte', 'woodward', 'breen', 'bennett', 'webber', 'morrison', 'carter', 
    'mitchell', 'marshall'
}

BUSINESS_KEYWORDS = {
    'ltd', 'limited', '& co', '& sons', '& son', 'brothers', 'bros', 'works', 'board', 'depot', 
    'association', 'society', 'office', 'inn', 'hotel', 'club', 'station', 'stores', 'church', 
    'chapel', 'school', 'garage', 'transport', 'hospital', 'clinic', 'bank', 'brewery', 'union', 
    'co.', 'corp', 'corporation', 'trust', 'fund', 'service', 'services'
}

def clean_building_name(text):
    text = text.strip()
    text = re.sub(r'^\((.*)\)$', r'\1', text)
    text = re.sub(r'(\b[A-Za-z]+)-([a-z]+\b)', r'\1\2', text)
    words = [w.capitalize() for w in text.split()]
    return ' '.join(words)

def clean_name_field(val):
    val = val.strip()
    # Normalize multiple spaces
    val = re.sub(r'\s+', ' ', val)
    return val

def process_1971_row(row):
    if row.get("year") != "1971":
        return row, False

    sn = row.get("surname", "").strip()
    fn = row.get("forename", "").strip()
    bn = row.get("building_name", "").strip()
    tr = row.get("trade", "").strip()

    changed = False

    # 1. Extract building names enclosed in parentheses
    for field_name in ['sn', 'fn']:
        val = sn if field_name == 'sn' else fn
        m_bldg = re.search(r'\(([^)]+)\)', val)
        if m_bldg:
            bldg_extracted = clean_building_name(m_bldg.group(1))
            if len(bldg_extracted) > 1 and not bldg_extracted.lower() in {'j.p', 'jp', 'snr', 'jnr', 'sr', 'jr'}:
                if not bn:
                    bn = bldg_extracted
                    changed = True
                val_clean = re.sub(r'\s*\([^)]+\)', '', val).strip()
                if field_name == 'sn':
                    sn = val_clean
                else:
                    fn = val_clean
                changed = True

    # 2. Skip businesses/commercial entities
    comb = f"{sn} {fn}".lower()
    if any(k in comb for k in BUSINESS_KEYWORDS):
        row["surname"] = clean_name_field(sn)
        row["forename"] = clean_name_field(fn)
        row["building_name"] = clean_name_field(bn)
        return row, changed

    # 3. Handle single name in forename with empty surname (e.g. Mrs Fry)
    if not sn and fn:
        tokens = fn.split()
        if len(tokens) >= 2 and tokens[0].lower().rstrip('.') in TITLES:
            sn = tokens[-1]
            fn = " ".join(tokens[:-1])
            changed = True
        else:
            sn = fn
            fn = ""
            changed = True

    # 4. Special reconstruct for single initial in surname (e.g. sn='V', fn='Miss M. Snell')
    if sn.strip().isalpha() and len(sn.strip()) == 1 and fn:
        tokens = fn.split()
        if len(tokens) >= 2 and tokens[0].lower().rstrip('.') in TITLES:
            real_sn = tokens[-1]
            real_fn = " ".join(tokens[:-1]) + f" {sn.strip()}."
            sn = real_sn
            fn = real_fn
            changed = True

    # 5. Swap detection when both sn and fn are present
    if sn and fn:
        sn_words = [w.lower().rstrip('.,;') for w in re.split(r'[\s\-]+', sn) if w]
        fn_words = [w.lower().rstrip('.,;') for w in re.split(r'[\s\-]+', fn) if w]

        sn_has_title = any(w in TITLES for w in sn_words)
        fn_has_title = any(w in TITLES for w in fn_words)

        sn_is_initials = bool(re.match(r'^[A-Z](\.\s*[A-Z])*\.?$', sn.strip()))
        fn_is_initials = bool(re.match(r'^[A-Z](\.\s*[A-Z])*\.?$', fn.strip()))

        sn_has_common_fn = any(w in COMMON_FORENAMES for w in sn_words)
        fn_has_common_fn = any(w in COMMON_FORENAMES for w in fn_words)

        sn_has_common_sn = any(w in COMMON_SURNAMES for w in sn_words)
        fn_has_common_sn = any(w in COMMON_SURNAMES for w in fn_words)

        should_swap = False

        if sn_has_title and not fn_has_title:
            should_swap = True
        elif sn_is_initials and not fn_is_initials:
            should_swap = True
        elif sn_has_common_fn and not fn_has_common_fn and not fn_has_title:
            should_swap = True
        elif sn_has_common_fn and fn_has_common_sn and not sn_has_common_sn:
            should_swap = True
        elif any(re.match(r'^[A-Z]\.?$', w.upper()) for w in sn_words) and not any(re.match(r'^[A-Z]\.?$', w.upper()) for w in fn_words):
            if not fn_has_title and not fn_is_initials:
                should_swap = True

        if should_swap:
            sn, fn = fn, sn
            changed = True

    row["surname"] = clean_name_field(sn)
    row["forename"] = clean_name_field(fn)
    row["building_name"] = clean_name_field(bn)
    row["trade"] = clean_name_field(tr)

    return row, changed

def main():
    print(f"Reading {INPUT_CSV}...")
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} records. Processing 1971 records...")
    swap_count = 0
    for r in rows:
        r, changed = process_1971_row(r)
        if changed:
            swap_count += 1

    print(f"Corrected and normalized {swap_count} records in 1971.")

    print(f"Writing updated dataset to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("data.csv update complete.")

if __name__ == "__main__":
    main()
