import csv

CSV_PATH = "data.csv"

def run():
    print("Reading data.csv...")
    rows = []
    fixed = 0

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        for r in reader:
            st = r.get("street", "").strip()
            yr = r.get("year", "").strip()
            no = r.get("house_number", "").strip()
            sn = r.get("surname", "").strip()
            fn = r.get("forename", "").strip()
            tr = r.get("trade", "").strip()

            if st == "Glass Works Cottages" and yr == "1920":
                # Door 1: Levi / Clayton
                if no == "1" and sn == "Levi" and tr == "Clayton":
                    r["surname"] = "Clayton"
                    r["forename"] = "Levi"
                    r["trade"] = ""
                    fixed += 1

                # Door 3: — / Greenhals
                elif no == "3" and sn == "—" and tr == "Greenhals":
                    r["surname"] = "Greenhals"
                    r["forename"] = ""
                    r["trade"] = ""
                    fixed += 1

                # Door 5: J / W. / Hobson
                elif no == "5" and sn == "J" and fn == "W." and tr == "Hobson":
                    r["surname"] = "Hobson"
                    r["forename"] = "J. W."
                    r["trade"] = ""
                    fixed += 1

                # Door 6: Keril -> Keirl
                elif no == "6" and sn == "Keril":
                    r["surname"] = "Keirl"
                    fixed += 1

                # Door 13: John / Fouweather
                elif no == "13" and sn == "John" and tr == "Fouweather":
                    r["surname"] = "Fouweather"
                    r["forename"] = "John"
                    r["trade"] = ""
                    fixed += 1

                # Door 17: Alexander / Macdonald
                elif no == "17" and sn == "Alexander" and tr == "Macdonald":
                    r["surname"] = "Macdonald"
                    r["forename"] = "Alexander"
                    r["trade"] = ""
                    fixed += 1

                # Door 18: J. / Rollinson
                elif no == "18" and sn == "J." and tr == "Rollinson":
                    r["surname"] = "Rollinson"
                    r["forename"] = "J."
                    r["trade"] = ""
                    fixed += 1

                # Door 20: Lucy / Mrs. / Woods
                elif no == "20" and sn == "Lucy" and fn == "Mrs." and tr == "Woods":
                    r["surname"] = "Woods"
                    r["forename"] = "Mrs. Lucy"
                    r["trade"] = ""
                    fixed += 1

            rows.append(r)

    print(f"Fixed {fixed} records in 1920 Glass Works Cottages.")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("data.csv updated successfully.")

if __name__ == "__main__":
    run()
