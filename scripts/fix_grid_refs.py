import re

with open("clean_csv.py", "r", encoding="utf-8") as f:
    text = f.read()

target = "    clean = re.sub(r'Eveswel\\]', 'Eveswell', clean, flags=re.IGNORECASE)"
replacement = """    # Strip trailing map grid coordinates like ", E 2", ", C 5", ", B 4"
    clean = re.sub(r'[,\\s]+[A-Z]\\s*\\d+$', '', clean, flags=re.IGNORECASE).strip()

    clean = re.sub(r'Eveswel\\]', 'Eveswell', clean, flags=re.IGNORECASE)"""

if "Strip trailing map grid coordinates" not in text:
    text = text.replace(target, replacement)
    with open("clean_csv.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Successfully added grid reference stripper to clean_csv.py")
else:
    print("Grid reference stripper already present in clean_csv.py")

