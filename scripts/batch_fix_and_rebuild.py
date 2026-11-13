import os
import sys
import subprocess
import csv
import json

def run_step(desc, cmd):
    print(f"\n==========================================")
    print(f"STEP: {desc}")
    print(f"COMMAND: {cmd}")
    print(f"==========================================")
    res = subprocess.run(cmd, shell=True, check=True)
    if res.returncode != 0:
        print(f"ERROR: {desc} failed with exit code {res.returncode}")
        sys.exit(1)

def main():
    os.chdir("/Users/robgale/Documents/Newport Street Directory Project")

    # 1. Ensure parse_1902.py Albany Street switch is line 91/93
    with open("scripts/parse_1902.py", "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("line_num in [90, 92]", "line_num in [91, 92, 93]")
    with open("scripts/parse_1902.py", "w", encoding="utf-8") as f:
        f.write(content)

    # 2. Parse 1902
    run_step("Parse 1902 TSV", "python3 scripts/parse_1902.py")

    # 3. Parse 1903
    run_step("Parse 1903 TSV", "python3 scripts/parse_1903.py")

    # 4. Merge 1902 into data.csv
    run_step("Merge 1902 into data.csv", "python3 scripts/merge_1902.py")

    # 5. Merge 1903 into data.csv
    run_step("Merge 1903 into data.csv", "python3 scripts/merge_1903.py")

    # 6. Run clean_csv.py
    run_step("Clean CSV", "python3 scripts/clean_csv.py")

    # 7. Count 1902 and 1903 records in data.csv and update app.js
    c1902 = 0
    c1903 = 0
    with open("data.csv", "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            y = row.get("year")
            if y == "1902":
                c1902 += 1
            elif y == "1903":
                c1903 += 1
    print(f"Verified canonical counts: 1902 = {c1902}, 1903 = {c1903}")

    with open("src/js/app.js", "r", encoding="utf-8") as f:
        app_js = f.read()
    
    import re
    app_js = re.sub(r'\{\s*year:\s*1902,\s*name:\s*[^,]+,\s*processed:\s*true,\s*records:\s*\d+\s*\}',
                    f'{{ year: 1902, name: "Johns\' Directory", processed: true, records: {c1902} }}', app_js)
    app_js = re.sub(r'\{\s*year:\s*1903,\s*name:\s*[^,]+,\s*processed:\s*true,\s*records:\s*\d+\s*\}',
                    f'{{ year: 1903, name: "Johns\' Directory", processed: true, records: {c1903} }}', app_js)
    with open("src/js/app.js", "w", encoding="utf-8") as f:
        f.write(app_js)

    # 8. Rebuild site data and timeline matrix
    run_step("Rebuild site data", "python3 scripts/build_site_data.py")
    run_step("Generate timeline matrix", "python3 scripts/generate_timeline_matrix.py")

    # 9. Verify Agincourt Street JSON
    print("\n==========================================")
    print("VERIFICATION: Agincourt Street")
    print("==========================================")
    with open("data/streets/agincourt-street.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    records = d.get("records", [])
    y1902 = [r for r in records if r.get("year") == "1902"]
    y1903 = [r for r in records if r.get("year") == "1903"]
    print(f"Agincourt Street 1902 count: {len(y1902)}")
    print(f"Agincourt Street 1903 count: {len(y1903)}")
    print("Sample 1902 records (houses 44, 42, 40, 38, 36, 34):")
    for r in y1902:
        if r.get("house_number") in ["44", "42", "40", "38", "36", "34"]:
            print(f"  No. {r.get('house_number')}: {r.get('forename')} {r.get('surname')} - {r.get('trade')}")
    print("Sample 1903 records (houses 1, 3, 5, 7, 9):")
    for r in y1903[:5]:
        print(f"  No. {r.get('house_number')}: {r.get('forename')} {r.get('surname')} - {r.get('trade')}")

    print("\nALL BATCH JOBS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
