import json

with open("edge_cases.json", "r", encoding="utf-8") as f:
    ec = json.load(f)

overrides = ec.get("overrides", [])

overrides.append({
    "reason": "Batch audit: Merge 'Caerleon' into 'Caerleon Road'",
    "match": {
        "street": "Caerleon"
    },
    "apply": {
        "street": "Caerleon Road"
    }
})

ec["overrides"] = overrides

with open("edge_cases.json", "w", encoding="utf-8") as f:
    json.dump(ec, f, indent=2, ensure_ascii=False)

print("Added Caerleon -> Caerleon Road override!")
