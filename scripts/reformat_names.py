import json, re

def format_directory_name(raw_name):
    raw = raw_name.strip()
    if not raw:
        return raw

    # Corporate / Institutional entities - keep untouched
    if re.search(r"\b(company|co\.|co\b|bank|banking|office|works|school|academy|society|navigation|consul|committee|inn|hotel|tavern|arms|boat|house|head|dragon|bull|cow|ship|ark|bells|lion|cross\s+keys)\b", raw, re.I):
        return raw

    # Multiple individuals joined by & or and (e.g. "Spear Joseph & James", "Waters & Jones")
    if " & " in raw or " and " in raw:
        return raw

    # Quirks: "The Misses King", "The Misses Thomas"
    m_misses = re.match(r"^([A-Z][a-z]+)\s+(?:the\s+)?misses\.?$", raw, re.I)
    if m_misses:
        return f"The Misses {m_misses.group(1)}"
    m_misses2 = re.match(r"^(?:the\s+)?misses\s+([A-Z][a-z]+)\.?$", raw, re.I)
    if m_misses2:
        return f"The Misses {m_misses2.group(1)}"

    # Special historical cases:
    # "Morgan Sir Chas. G. bart." -> "Sir Chas. G. Morgan, Bart."
    # "Salusbury Sir Thomas Robert, bart." -> "Sir Thomas Robert Salusbury, Bart."
    # "Bateman Goulthourt, esq." -> "Goulthourt Bateman, Esq."
    # "Mackworth Major Digby" -> "Major Digby Mackworth"
    # "Hall George, esq." -> "George Hall, Esq."

    clean = raw
    suffix = ""
    # Suffix matching (esq, bart, etc.)
    m_suf = re.search(r",?\s*\b(esq\.?|bart\.?|jun\.?|sen\.?|jr\.?|sr\.?)\b\.?", clean, re.I)
    if m_suf:
        raw_suf = m_suf.group(1).lower().rstrip('.')
        if raw_suf == 'esq': suffix = 'Esq.'
        elif raw_suf == 'bart': suffix = 'Bart.'
        elif raw_suf in ('jun', 'jr'): suffix = 'Jun.'
        elif raw_suf in ('sen', 'sr'): suffix = 'Sen.'
        clean = clean[:m_suf.start()] + clean[m_suf.end():]
        clean = clean.strip(", ")

    # Title matching (Rev., Sir, Major, Capt., Mrs., Mr., Miss)
    title = ""
    m_title = re.search(r"\b(mrs\.?|mr\.?|miss\.?|rev\.?|dr\.?|capt\.?|col\.?|major\.?|sir)\b", clean, re.I)
    if m_title:
        t_str = m_title.group(1).lower().rstrip('.')
        title_map = {
            'mrs': 'Mrs.',
            'mr': 'Mr.',
            'miss': 'Miss',
            'rev': 'Rev.',
            'dr': 'Dr.',
            'capt': 'Capt.',
            'col': 'Col.',
            'major': 'Major',
            'sir': 'Sir'
        }
        title = title_map.get(t_str, t_str.capitalize() + '.')
        clean = clean[:m_title.start()] + clean[m_title.end():]
        clean = re.sub(r"\s+", " ", clean).strip(", ")

    parts = [p.strip() for p in clean.split() if p.strip()]
    if not parts:
        formatted = ""
    elif len(parts) == 1:
        formatted = parts[0]
    else:
        # Standard directory format: Surname Forename (e.g. "Brewer John" -> "John Brewer")
        surname = parts[0]
        forenames = " ".join(parts[1:])
        formatted = f"{forenames} {surname}"

    full_name_parts = []
    if title:
        full_name_parts.append(title)
    if formatted:
        full_name_parts.append(formatted)
    
    full_str = " ".join(full_name_parts)
    if suffix:
        full_str += f", {suffix}"
    return full_str

# Test across both JSON files and update them
for fn in ["data/early_directories/pigot_1822.json", "data/early_directories/pigot_1835.json"]:
    with open(fn) as f:
        data = json.load(f)

    if "nobility_gentry_clergy" in data:
        for item in data["nobility_gentry_clergy"]:
            item["formatted_name"] = format_directory_name(item["name"])

    for sec in data["sections"]:
        for entry in sec["entries"]:
            entry["formatted_name"] = format_directory_name(entry["name"])

    with open(fn, "w") as f:
        json.dump(data, f, indent=2)

print("Both 1822 and 1835 JSON files updated with formatted_name fields.")
