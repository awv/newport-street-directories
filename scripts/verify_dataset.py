import json
import os
import sys

DATA_DIR = "data/streets"

def run_verifications():
    print("Running Dataset Accuracy Verification Tests...")
    errors = []

    # Test 1: Commercial Road 1890 verification
    comm_path = os.path.join(DATA_DIR, "commercial-road.json")
    if not os.path.exists(comm_path):
        errors.append("ERROR: commercial-road.json does not exist!")
    else:
        with open(comm_path, "r", encoding="utf-8") as f:
            comm_data = json.load(f)
        recs_1890 = [r for r in comm_data.get("records", []) if r.get("year") == "1890"]
        
        woodruff_exists = any(r.get("house_number") == "1" and ("Woodruff" in r.get("surname", "")) for r in recs_1890)
        if not woodruff_exists:
            errors.append("FAIL: 1890 Commercial Road is missing #1 Woodruff R.")

        # Assert house number 1 contains strictly <= 2 records (Woodruff R & S. Wales Daily News office)
        house_1_recs = [r for r in recs_1890 if r.get("house_number") == "1"]
        if len(house_1_recs) > 2:
            errors.append(f"FAIL: 1890 Commercial Road house #1 contains unexpected entries: {house_1_recs}")

        # Assert numbers 1 to 30 are properly assigned to house numbers
        recs_with_hnum = [r for r in recs_1890 if r.get("house_number") in [str(i) for i in range(1, 31)]]
        if len(recs_with_hnum) < 25:
            errors.append(f"FAIL: 1890 Commercial Road house numbers 1-30 are missing house_number assignments (found {len(recs_with_hnum)})")

        # Assert no shifted house numbers (e.g. "10", "11", "14", "19", "31") remain in surname for 1890 Commercial Road
        shifted_nums = [r for r in recs_1890 if r.get("surname") in ["10", "11", "14", "15", "16", "19", "31"]]
        if shifted_nums:
            errors.append(f"FAIL: 1890 Commercial Road contains shifted numeric surnames: {shifted_nums}")

        # Check absence of St. Mary Street spillover (James C, Reed Wm, Hodge Thos)
        invalid_bleed = [r for r in recs_1890 if (r.get("surname") == "James" and r.get("forename") == "C") or (r.get("surname") == "Reed" and r.get("forename") == "Wm") or (r.get("surname") == "Hodge" and r.get("forename") == "Thos")]
        if invalid_bleed:
            errors.append(f"FAIL: 1890 Commercial Road contains St. Mary Street side-bleed: {invalid_bleed}")

    # Test 2: St. Mary's Road 1890 verification
    stmary_path = os.path.join(DATA_DIR, "st-mary-s-road.json")
    if not os.path.exists(stmary_path):
        errors.append("ERROR: st-mary-s-road.json does not exist!")
    else:
        with open(stmary_path, "r", encoding="utf-8") as f:
            stmary_data = json.load(f)
        stmary_recs_1890 = [r for r in stmary_data.get("records", []) if r.get("year") == "1890"]
        james_c = any(("James" in r.get("surname", "") or "James" in r.get("forename", "")) and ("C" in r.get("surname", "") or "C" in r.get("forename", "")) for r in stmary_recs_1890)
        if not james_c:
            errors.append("FAIL: 1890 St. Mary's Road missing #1 James C!")

    if errors:
        print("\n--- VERIFICATION FAILURES ---")
        for err in errors:
            print(f"❌ {err}")
        sys.exit(1)
    else:
        print("✅ ALL DATASET VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verifications()
