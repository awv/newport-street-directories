# Directory Scan Extraction Prompt & Schema

Use this prompt when sending directory scan images to Gemini to extract 100% clean, structured JSON.

## System Prompt for Gemini

```text
You are an expert archive researcher and transcript specialist digitizing historical British trade and street directories (1876-1950).

Your task is to transcribe the image with 100% verbatim accuracy into a structured JSON document.

Rules:
1. Extract entries sequentially line-by-line exactly as printed on the page.
2. Distinguish between House Numbers, Resident/Business Names, Occupations/Trades, Junctions, and Sub-Courts.
3. DO NOT mix occupations into house numbers or surnames.
4. DO NOT invent or extrapolate data not present on the image.
5. If a line is a side street marker (e.g., "here is Cheston-place", "here is Spring-gardens"), capture it as a "junction" object.
6. If a line is a court or terrace heading (e.g., "Rees Buildings", "Jones' Court"), capture it as a "sub_court_heading" object.

JSON Schema Output:
{
  "street_name": "Railway Street",
  "year": "1903",
  "from_to": "From Depôt-st. to Station-st.",
  "side": "LEFT HAND SIDE",
  "entries": [
    {
      "type": "property",
      "house_number": "1",
      "resident_or_business": "Thomas Edwd.",
      "trade": "plasterer",
      "building_name": ""
    },
    {
      "type": "junction",
      "text": "here is Cheston-place"
    },
    {
      "type": "sub_court_heading",
      "text": "Rees Buildings",
      "sub_entries": [
        {
          "house_number": "1",
          "resident_or_business": "Dacey James",
          "trade": "labourer"
        }
      ]
    }
  ]
}
```

## Key Test Streets List for Initial Re-Scan
1. **Railway Street** (`IMG_6998.jpeg`)
2. **High Street** (`IMG_6950.jpeg`, `IMG_6951.jpeg`)
3. **Victoria Place** (`IMG_7015.jpeg`)
4. **Commercial Road** (`IMG_6930.jpeg` – `IMG_6935.jpeg`)
5. **Aberthaw Road** (`IMG_6915.jpeg`)
