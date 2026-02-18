"""
Reads all data from the results/ folder and generates a single HTML page.

Usage:
    uv run generate_html.py

Output:
    results/index.html
"""

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import json
import sys
from pathlib import Path


def load_json(path: Path):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def party_color(party_name: str) -> str:
    name = (party_name or "").lower()
    if "national democratic congress" in name or "ndc" in name:
        return "#FECA09"
    if "new national party" in name or "nnp" in name:
        return "#026701"
    if "labour" in name:
        return "#D50000"
    if "renaissance" in name:
        return "#4BACC6"
    if "liberal" in name:
        return "#F79646"
    if "progress" in name:
        return "#C0504D"
    if "empowerment" in name:
        return "#808080"
    if "patriotic" in name:
        return "#CED2DB"
    if "freedom" in name:
        return "#DC6E3E"
    if "independent" in name:
        return "#DCDCDC"
    return "#94A3B8"


def render_general(year: int, data: dict) -> str:
    results = data.get("results", [])
    if not results:
        return "<p>No data available.</p>"

    max_votes = max((r.get("votes") or 0 for r in results), default=1)
    rows = ""
    for r in results:
        votes = r.get("votes") or 0
        pct   = r.get("percentage") or 0.0
        seats = r.get("seats")
        change = r.get("change", "—")
        party  = r.get("party", "")
        color  = party_color(party)
        bar_w  = round((votes / max_votes) * 100, 1)
        seats_str  = str(seats) if seats is not None else "—"
        votes_fmt  = f"{votes:,}" if votes else "—"
        chg_class  = "pos" if str(change).startswith("+") else ("neg" if any(str(change).startswith(c) for c in ["–","-"]) else "neu")

        rows += f"""<tr>
          <td class="td-party">
            <span class="dot" style="background:{color}"></span>{party}
          </td>
          <td class="td-bar">
            <div class="bar" style="width:{bar_w}%;background:{color}80"></div>
          </td>
          <td class="td-num">{votes_fmt}</td>
          <td class="td-num">{pct}%</td>
          <td class="td-num bold">{seats_str}</td>
          <td class="td-num {chg_class}">{change}</td>
        </tr>"""

    return f"""<table class="data-table">
      <thead><tr>
        <th>Party</th><th>Bar</th><th>Votes</th><th>%</th><th>Seats</th><th>+/–</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def render_constituency(data: dict) -> str:
    constituencies = data.get("constituencies", [])
    if not constituencies:
        return ""

    cards = ""
    for c in constituencies:
        name        = c.get("constituency", "")
        electorate  = c.get("electorate")
        turnout_pct = c.get("turnout_pct")
        winner      = c.get("winner", {})
        candidates  = c.get("candidates", [])
        w_candidate = winner.get("candidate", "—")
        w_party     = winner.get("party", "—")
        w_color     = party_color(w_party)
        elec_str    = f"{electorate:,}" if electorate else "—"
        tpct_str    = f"{turnout_pct}%" if turnout_pct else "—"

        cand_max  = max((cd.get("votes") or 0 for cd in candidates), default=1)
        cand_rows = ""
        for cd in candidates:
            cv   = cd.get("votes") or 0
            cp   = cd.get("percentage") or 0.0
            cc   = party_color(cd.get("party", ""))
            cb   = round((cv / cand_max) * 100, 1) if cand_max else 0
            cand_rows += f"""<div class="cand">
              <span class="dot sm" style="background:{cc}"></span>
              <span class="cand-name">{cd.get('candidate','')}</span>
              <span class="cand-party">{cd.get('party','')}</span>
              <div class="mini-bar-wrap"><div class="mini-bar" style="width:{cb}%;background:{cc}80"></div></div>
              <span class="cand-votes">{cv:,}</span>
              <span class="cand-pct">{cp}%</span>
            </div>"""

        cards += f"""<div class="const-card">
          <div class="const-head" style="border-left:3px solid {w_color}">
            <span class="const-name">{name}</span>
            <span class="badge" style="background:{w_color}22;color:{w_color};border:1px solid {w_color}55">{w_candidate}</span>
          </div>
          <div class="const-meta">
            <span>Electorate <b>{elec_str}</b></span>
            <span>Turnout <b>{tpct_str}</b></span>
          </div>
          <div class="const-cands">{cand_rows}</div>
        </div>"""

    return f"""<h3 class="sub-heading">By Constituency</h3>
    <div class="const-grid">{cards}</div>"""


def build_page(years_data: list[tuple]) -> str:
    # years_data: list of (year, general_dict, constituency_dict_or_None)

    nav_links = "".join(
        f'<a href="#year-{y}" class="nav-chip">{y}</a>' for y, _, _ in years_data
    )

    sections = ""
    for year, general, constituency in years_data:
        election_name = general.get("election", f"{year} Grenadian General Election")
        source        = general.get("source", "")
        general_html  = render_general(year, general)
        const_html    = render_constituency(constituency) if constituency else ""

        sections += f"""<section class="year-section" id="year-{year}">
        <div class="year-header">
          <h2 class="year-title">{year}</h2>
          <a class="source-link" href="{source}" target="_blank">Wikipedia ↗</a>
        </div>
        <h3 class="sub-heading">Overall Results</h3>
        {general_html}
        {const_html}
      </section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Grenada General Elections</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&family=Bebas+Neue&display=swap" rel="stylesheet"/>
  <style>
    :root {{
      --green:  #009A44;
      --red:    #CE1126;
      --gold:   #FCD116;
      --bg:     #f7f5f0;
      --surface:#ffffff;
      --border: #e2ddd6;
      --text:   #1a1612;
      --muted:  #6b6258;
      --radius: 14px;
    }}
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}

    body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); }}

    /* Nav */
    .topbar {{
      background: linear-gradient(90deg, var(--red) 0%, var(--red) 8px, var(--green) 8px, var(--green) calc(100% - 8px), var(--red) calc(100% - 8px));
      position:sticky; top:0; z-index:100;
      display:flex; align-items:center; gap:16px;
      padding:0 24px; height:56px;
      box-shadow:0 2px 8px rgba(0,0,0,.25);
    }}
    .topbar-title {{
      font-family:'Bebas Neue',sans-serif;
      font-size:1.6rem; letter-spacing:.06em;
      color:#fff;
      margin-right:auto;
    }}
    .topbar-title span {{ color:var(--gold); }}
    .nav-chip {{
      font-size:13px; font-weight:500;
      color:rgba(255,255,255,.75);
      padding:6px 14px; border-radius:999px;
      text-decoration:none;
      border:1px solid rgba(255,255,255,.2);
      transition:all .15s;
    }}
    .nav-chip:hover {{ background:rgba(255,255,255,.15); color:#fff; }}

    /* Layout */
    .wrapper {{ max-width:960px; margin:0 auto; padding:32px 24px 80px; }}

    .year-section {{
      background:var(--surface);
      border-radius:var(--radius);
      box-shadow:0 1px 3px rgba(0,0,0,.07), 0 4px 12px rgba(0,0,0,.05);
      padding:32px;
      margin-bottom:32px;
      animation:fadeUp .4s ease both;
    }}
    @keyframes fadeUp {{
      from{{ opacity:0; transform:translateY(12px); }}
      to  {{ opacity:1; transform:translateY(0); }}
    }}

    .year-header {{
      display:flex; align-items:center; justify-content:space-between;
      margin-bottom:24px;
      padding-bottom:16px;
      border-bottom:2px solid var(--gold);
    }}
    .year-title {{
      font-family:'Playfair Display',serif;
      font-size:2rem; color:var(--red);
    }}
    .source-link {{
      font-size:12px; color:var(--muted);
      text-decoration:none; border-bottom:1px dashed var(--border);
    }}
    .source-link:hover {{ color:var(--green); }}

    .sub-heading {{
      font-size:11px; font-weight:600;
      letter-spacing:.1em; text-transform:uppercase;
      color:var(--muted); margin:24px 0 12px;
    }}

    /* Table */
    .data-table {{ width:100%; border-collapse:collapse; }}
    .data-table thead tr {{ background:var(--bg); }}
    .data-table th {{
      font-size:11px; font-weight:600; letter-spacing:.08em;
      text-transform:uppercase; color:var(--muted);
      padding:10px 14px; text-align:left;
    }}
    .data-table tbody tr {{
      border-bottom:1px solid var(--border);
      transition:background .12s;
    }}
    .data-table tbody tr:last-child {{ border:none; }}
    .data-table tbody tr:hover {{ background:var(--bg); }}
    .data-table td {{ padding:12px 14px; vertical-align:middle; }}

    .td-party {{ display:flex; align-items:center; gap:10px; font-weight:500; font-size:14px; min-width:200px; }}
    .td-bar {{ width:180px; padding-right:8px; }}
    .bar {{ height:8px; border-radius:4px; min-width:3px; }}
    .td-num {{ font-family:'Inter',sans-serif; font-variant-numeric: tabular-nums; font-size:13px; white-space:nowrap; }}
    .bold {{ font-weight:600; font-size:15px; }}
    .pos {{ color:#166534; }} .neg {{ color:#991b1b; }} .neu {{ color:var(--muted); }}

    .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
    .dot.sm {{ width:8px; height:8px; }}

    /* Constituency */
    .const-grid {{
      display:grid;
      grid-template-columns:repeat(auto-fill, minmax(400px, 1fr));
      gap:14px;
    }}
    .const-card {{
      border:1px solid var(--border);
      border-radius:10px;
      overflow:hidden;
      transition:box-shadow .15s;
    }}
    .const-card:hover {{ box-shadow:0 4px 16px rgba(0,0,0,.08); }}
    .const-head {{
      display:flex; align-items:center; justify-content:space-between; gap:8px;
      padding:12px 14px;
      background:var(--bg);
      border-bottom:1px solid var(--border);
    }}
    .const-name {{ font-weight:600; font-size:13px; }}
    .badge {{
      font-size:11px; font-weight:500;
      padding:3px 10px; border-radius:999px;
      white-space:nowrap; flex-shrink:0;
    }}
    .const-meta {{
      display:flex; gap:16px; padding:8px 14px;
      font-size:11px; color:var(--muted);
      border-bottom:1px solid var(--border);
      background:#fafbf9;
    }}
    .const-meta b {{ color:var(--text); }}
    .const-cands {{ padding:10px 14px; display:flex; flex-direction:column; gap:8px; }}
    .cand {{
      display:grid;
      grid-template-columns:8px 1fr auto 72px 52px 40px;
      align-items:center; gap:6px;
    }}
    .cand-name {{ font-size:12px; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .cand-party {{ font-size:11px; color:var(--muted); white-space:nowrap; }}
    .mini-bar-wrap {{ height:5px; background:var(--border); border-radius:3px; overflow:hidden; }}
    .mini-bar {{ height:100%; border-radius:3px; }}
    .cand-votes {{ font-family:'Inter',sans-serif; font-variant-numeric: tabular-nums; font-size:11px; text-align:right; }}
    .cand-pct   {{ font-family:'Inter',sans-serif; font-variant-numeric: tabular-nums; font-size:10px; color:var(--muted); text-align:right; }}

    /* Footer */
    footer {{
      text-align:center; padding:24px;
      font-size:12px; color:var(--muted);
      border-top:1px solid var(--border);
    }}

    @media(max-width:600px) {{
      .const-grid {{ grid-template-columns:1fr; }}
      .td-bar {{ display:none; }}
      .topbar {{ gap:8px; }}
      .year-section {{ padding:20px 16px; }}
    }}
  </style>
</head>
<body>

<nav class="topbar">
  <span class="topbar-title">Grenada <span>Elections</span></span>
  {nav_links}
</nav>

<div class="wrapper">
  {sections}
</div>

<footer>Generated from Wikipedia election data</footer>

</body>
</html>"""


if __name__ == "__main__":
    results_dir = Path("results")
    if not results_dir.exists():
        print("❌ ERROR: 'results/' folder not found. Run the scraper first.", file=sys.stderr)
        sys.exit(1)

    # Find all year subdirectories that have election_general.json
    year_dirs = sorted(
        [d for d in results_dir.iterdir() if d.is_dir() and d.name.isdigit()],
        key=lambda d: int(d.name),
        reverse=True,
    )

    if not year_dirs:
        print("❌ ERROR: No year folders found in results/.", file=sys.stderr)
        sys.exit(1)

    years_data = []
    for d in year_dirs:
        year     = int(d.name)
        general  = load_json(d / "election_general.json")
        const    = load_json(d / "election_constituency.json")
        if not general:
            print(f"⚠️  Skipping {year} — no election_general.json found.")
            continue
        years_data.append((year, general, const))
        print(f"✅ Loaded {year} — general: ✓  constituency: {'✓' if const else '✗'}")

    if not years_data:
        print("❌ ERROR: No valid election data found.", file=sys.stderr)
        sys.exit(1)

    html = build_page(years_data)
    out  = results_dir / "index.html"
    out.write_text(html, encoding="utf-8")

    print(f"\n✅ Page saved to '{out}'")
    print(f"   Open with: open {out}")