import sys
import os
import re

def clean_slug(text):
    if not text:
        return ""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or "unnamed"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 add_street_content.py \"Street Name\"")
        sys.exit(1)
        
    street_name = sys.argv[1].strip()
    slug = clean_slug(street_name)
    
    target_dir = os.path.join("street_content", slug)
    os.makedirs(target_dir, exist_ok=True)
    
    md_file = os.path.join(target_dir, "index.md")
    if os.path.exists(md_file):
        print(f"Street content folder and file already exist at: {md_file}")
        return
        
    template = f"""---
# Custom settings for {street_name}
latitude: ""
longitude: ""
map_query: "{street_name}, Newport"
---

Write the historical description for {street_name} here. If you write a description here, it will override the automatically generated summary (e.g. "Historical directory timeline...") on the street page.

You can also place images (.jpg, .png, etc.) inside this directory and they will be automatically detected and loaded on the street page.
"""
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(template)
        
    print(f"Created street content skeleton at: {md_file}")

if __name__ == "__main__":
    main()
