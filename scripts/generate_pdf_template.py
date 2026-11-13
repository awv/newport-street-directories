import json

def generate_print_html(year):
    json_path = f"data/early_directories/pigot_{year}.json"
    with open(json_path) as f:
        data = json.load(f)

    title = data.get("title", f"Pigot & Co.'s Directory ({year})")
    narrative = data.get("narrative", "")
    gentry = data.get("nobility_gentry_clergy", [])
    sections = data.get("sections", [])

    gentry_html = ""
    if gentry:
        gentry_html = """
        <div class="pdf-section page-break-before">
          <h2 class="pdf-sec-title">Nobility, Gentry & Clergy</h2>
          <div class="pdf-grid-2col">
        """
        for g in gentry:
            disp_name = g.get("formatted_name") or g.get("name")
            res = g.get("residence", "")
            notes = f" ({g['notes']})" if g.get("notes") else ""
            gentry_html += f"""
              <div class="pdf-entry">
                <span class="pdf-entry-name">{disp_name}</span>
                <span class="pdf-entry-desc">— {res}{notes}</span>
              </div>
            """
        gentry_html += "</div></div>"

    sections_html = ""
    for sec in sections:
        cat_title = sec["category"]
        entries = sec["entries"]
        sections_html += f"""
          <div class="pdf-trade-category">
            <h3 class="pdf-cat-title">{cat_title}</h3>
            <div class="pdf-grid-2col">
        """
        for e in entries:
            disp_name = e.get("formatted_name") or e.get("name")
            trade = e.get("trade", "")
            street = f", {e['street']}" if e.get("street") else ""
            notes = f" [{e['notes']}]" if e.get("notes") else ""
            sections_html += f"""
              <div class="pdf-entry">
                <span class="pdf-entry-name">{disp_name}</span>
                <span class="pdf-entry-desc">{trade}{street}{notes}</span>
              </div>
            """
        sections_html += "</div></div>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 16mm 16mm 16mm 16mm;
    }}
    body {{
      font-family: 'Georgia', 'Times New Roman', serif;
      color: #1a1a1a;
      background: #ffffff;
      line-height: 1.45;
      font-size: 9.5pt;
      margin: 0;
      padding: 0;
    }}
    .pdf-running-footer {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 9mm;
      border-top: 1px solid #77581e;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 8pt;
      font-family: 'Georgia', 'Times New Roman', serif;
      color: #555555;
      background: #ffffff;
      box-sizing: border-box;
    }}
    .pdf-running-footer span {{
      letter-spacing: 0.02em;
    }}
    .print-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .print-table td {{
      padding: 0;
      margin: 0;
      border: none;
    }}
    .footer-spacer {{
      height: 12mm;
    }}
    .pdf-header {{
      text-align: center;
      border-bottom: 2px solid #2b2b2b;
      padding-bottom: 12pt;
      margin-bottom: 16pt;
    }}
    .pdf-pub-date {{
      font-size: 8.5pt;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #77581e;
      font-weight: bold;
    }}
    .pdf-title {{
      font-size: 24pt;
      font-weight: normal;
      margin: 6pt 0 4pt 0;
      letter-spacing: 0.04em;
    }}
    .pdf-subtitle {{
      font-size: 11pt;
      font-style: italic;
      color: #444;
      margin: 0;
    }}
    .pdf-narrative {{
      background: #fdfbf7;
      border: 1px solid #e7decb;
      border-radius: 4pt;
      padding: 12pt 14pt;
      margin-bottom: 18pt;
      font-size: 9pt;
      text-align: justify;
    }}
    .pdf-narrative h2 {{
      font-size: 12pt;
      color: #77581e;
      margin: 0 0 6pt 0;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .pdf-sec-title {{
      font-size: 14pt;
      border-bottom: 1.5pt solid #77581e;
      padding-bottom: 3pt;
      margin: 16pt 0 10pt 0;
      color: #77581e;
      letter-spacing: 0.05em;
    }}
    .pdf-cat-title {{
      font-size: 11pt;
      font-weight: bold;
      color: #1a1a1a;
      border-bottom: 0.5pt solid #ccc;
      padding-bottom: 2pt;
      margin: 12pt 0 6pt 0;
      page-break-after: avoid;
    }}
    .pdf-grid-2col {{
      column-count: 2;
      column-gap: 18pt;
    }}
    .pdf-entry {{
      break-inside: avoid;
      margin-bottom: 4.5pt;
      font-size: 8.8pt;
    }}
    .pdf-entry-name {{
      font-weight: bold;
      color: #0f172a;
    }}
    .pdf-entry-desc {{
      color: #444;
      font-style: italic;
    }}
    .page-break-before {{
      page-break-before: always;
    }}
  </style>
</head>
<body>
  <div class="pdf-running-footer">
    <span>Created by <strong>Robert Gale</strong>, <em>Newport Cornucopia</em> — www.newportcornucopia.co.uk</span>
  </div>

  <table class="print-table">
    <tbody>
      <tr>
        <td>
          <div class="pdf-header">
            <div class="pdf-pub-date">Monmouthshire Historic Gazetteers Archive</div>
            <h1 class="pdf-title">{title}</h1>
            <p class="pdf-subtitle">Borough, Port & Ancient Market Town of Newport (with Caerleon)</p>
          </div>

          <div class="pdf-narrative">
            <h2>Historical Topographical Survey & Commercial Statistics ({year})</h2>
            <p style="white-space: pre-line; margin: 0;">{narrative}</p>
          </div>

          {gentry_html}

          <div class="pdf-section">
            <h2 class="pdf-sec-title">Classified Directory of Trades, Merchants & Manufactures</h2>
            {sections_html}
          </div>
        </td>
      </tr>
    </tbody>
    <tfoot>
      <tr>
        <td><div class="footer-spacer"></div></td>
      </tr>
    </tfoot>
  </table>
</body>
</html>"""

    out_file = f"pdf_reports/pigot_{year}_print.html"
    with open(out_file, "w") as f:
        f.write(html)
    print(f"Generated {out_file}")

generate_print_html(1822)
generate_print_html(1835)
