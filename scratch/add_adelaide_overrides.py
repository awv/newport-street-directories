import json
import subprocess

with open("edge_cases.json", "r", encoding="utf-8") as f:
    ec = json.load(f)

overrides = ec.get("overrides", [])

# Add overrides to ensure both occupants are preserved for 1913 and 1920
new_rules = [
    {
        "reason": "Adelaide Street #2 1913: Ensure Thos Charles is listed alongside Wm J.S. Taylor",
        "match": {
            "street": "Adelaide Street",
            "year": "1913",
            "house_number": "2",
            "surname": "Charles"
        },
        "apply": {
            "house_number": "2",
            "surname": "Charles",
            "forename": "Thos."
        }
    },
    {
        "reason": "Adelaide Street #2 1913: Ensure Wm J.S. Taylor is listed alongside Thos Charles",
        "match": {
            "street": "Adelaide Street",
            "year": "1913",
            "house_number": "2",
            "surname": "Taylor"
        },
        "apply": {
            "house_number": "2",
            "surname": "Taylor",
            "forename": "Wm. J. S."
        }
    },
    {
        "reason": "Adelaide Street #2 1920: Ensure Thos Charles is listed alongside W.A. Wright",
        "match": {
            "street": "Adelaide Street",
            "year": "1920",
            "house_number": "2",
            "surname": "Charles"
        },
        "apply": {
            "house_number": "2",
            "surname": "Charles",
            "forename": "Thos."
        }
    },
    {
        "reason": "Adelaide Street #2 1920: Ensure W.A. Wright is listed alongside Thos Charles",
        "match": {
            "street": "Adelaide Street",
            "year": "1920",
            "house_number": "2",
            "surname": "Wright"
        },
        "apply": {
            "house_number": "2",
            "surname": "Wright",
            "forename": "W. A."
        }
    }
]

overrides.extend(new_rules)
ec["overrides"] = overrides

with open("edge_cases.json", "w", encoding="utf-8") as f:
    json.dump(ec, f, indent=2, ensure_ascii=False)

print("Added Adelaide Street #2 1913 and 1920 dual-occupant overrides to edge_cases.json!")
