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
        general_html  = render_general(year, general)
        const_html    = render_constituency(constituency) if constituency else ""

        sections += f"""<section class="year-section" id="year-{year}">
        <div class="year-header">
          <h2 class="year-title">{year}</h2>
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
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    /* Material Design 3 tokens – Grenada-inspired */
    :root {{
      --md-sys-color-primary: #006A44;
      --md-sys-color-on-primary: #FFFFFF;
      --md-sys-color-primary-container: #B8F397;
      --md-sys-color-on-primary-container: #002200;
      --md-sys-color-secondary: #CE1126;
      --md-sys-color-on-secondary: #FFFFFF;
      --md-sys-color-primary-container-alt: #FCD116;
      --md-sys-color-on-primary-container-alt: #1C1B00;
      --md-sys-color-surface: #FDFDF6;
      --md-sys-color-on-surface: #1C1B16;
      --md-sys-color-on-surface-variant: #4F4E45;
      --md-sys-color-outline: #80786E;
      --md-sys-color-outline-variant: #E8E2D9;
      --md-sys-color-surface-container: #F3F0E8;
      --md-sys-color-surface-container-high: #EDE9E0;
      --md-sys-color-surface-container-highest: #E8E4DB;
      --md-sys-color-error: #BA1A1A;
      --md-sys-color-on-error: #FFFFFF;
      --md-sys-color-tertiary: #166534;
      --md-sys-color-on-tertiary: #FFFFFF;
      --md-sys-color-inverse-tertiary: #991b1b;
      --md-sys-shape-corner-extra-large: 28px;
      --md-sys-shape-corner-large: 16px;
      --md-sys-shape-corner-medium: 12px;
      --md-sys-shape-corner-small: 8px;
      --md-sys-shape-corner-full: 9999px;
      --md-sys-elevation-1: 0 1px 2px rgba(0,0,0,.3), 0 1px 3px rgba(0,0,0,.15);
      --md-sys-elevation-2: 0 1px 2px rgba(0,0,0,.3), 0 2px 6px rgba(0,0,0,.2);
      --md-sys-elevation-3: 0 4px 8px rgba(0,0,0,.15), 0 1px 3px rgba(0,0,0,.1);
    }}
    *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}

    body {{
      font-family:'Roboto',sans-serif;
      font-size:14px;
      background:var(--md-sys-color-surface-container);
      color:var(--md-sys-color-on-surface);
      line-height:1.5;
    }}

    /* Top app bar – MD3 */
    .topbar {{
      background:var(--md-sys-color-surface);
      position:sticky; top:0; z-index:100;
      display:flex; align-items:center; gap:12px;
      padding:0 24px; height:64px;
      box-shadow:var(--md-sys-elevation-2);
      border-bottom:1px solid var(--md-sys-color-outline-variant);
    }}
    .topbar::before {{
      content:'';
      position:absolute;
      top:0; left:0; right:0; height:4px;
      background:linear-gradient(90deg, var(--md-sys-color-secondary) 0%, var(--md-sys-color-primary-container-alt) 50%, var(--md-sys-color-primary) 100%);
    }}
    .topbar-title {{
      font-size:1.25rem; font-weight:600; letter-spacing:.02em;
      color:var(--md-sys-color-on-surface);
      margin-right:auto;
    }}
    .topbar-title span {{ color:var(--md-sys-color-primary); }}
    .nav-chip {{
      font-size:13px; font-weight:500;
      color:var(--md-sys-color-on-surface-variant);
      padding:6px 14px; border-radius:var(--md-sys-shape-corner-full);
      text-decoration:none;
      background:var(--md-sys-color-surface-container);
      border:1px solid var(--md-sys-color-outline-variant);
      transition:background .2s, color .2s, border-color .2s;
    }}
    .nav-chip:hover {{
      background:var(--md-sys-color-surface-container-high);
      color:var(--md-sys-color-on-surface);
      border-color:var(--md-sys-color-outline);
    }}

    /* Layout */
    .wrapper {{ max-width:960px; margin:0 auto; padding:24px 16px 80px; }}

    .year-section {{
      background:var(--md-sys-color-surface);
      border-radius:var(--md-sys-shape-corner-extra-large);
      box-shadow:var(--md-sys-elevation-1);
      border:1px solid var(--md-sys-color-outline-variant);
      padding:24px;
      margin-bottom:24px;
      animation:fadeUp .35s cubic-bezier(0.2,0,0,1) both;
      scroll-margin-top:80px;
    }}
    @keyframes fadeUp {{
      from{{ opacity:0; transform:translateY(16px); }}
      to{{ opacity:1; transform:translateY(0); }}
    }}

    .year-header {{
      display:flex; align-items:center; justify-content:space-between;
      margin-bottom:20px;
      padding-bottom:16px;
      border-bottom:1px solid var(--md-sys-color-outline-variant);
    }}
    .year-title {{
      font-size:1.5rem; font-weight:500; letter-spacing:.01em;
      color:var(--md-sys-color-secondary);
    }}

    .sub-heading {{
      font-size:11px; font-weight:600;
      letter-spacing:.1em; text-transform:uppercase;
      color:var(--md-sys-color-on-surface-variant);
      margin:20px 0 12px;
    }}

    /* Table – MD3 */
    .data-table {{ width:100%; border-collapse:collapse; }}
    .data-table thead tr {{ background:var(--md-sys-color-surface-container); }}
    .data-table th {{
      font-size:11px; font-weight:600; letter-spacing:.08em;
      text-transform:uppercase; color:var(--md-sys-color-on-surface-variant);
      padding:12px 16px; text-align:left;
    }}
    .data-table tbody tr {{
      border-bottom:1px solid var(--md-sys-color-outline-variant);
      transition:background .12s;
    }}
    .data-table tbody tr:last-child {{ border:none; }}
    .data-table tbody tr:hover {{ background:var(--md-sys-color-surface-container); }}
    .data-table td {{ padding:12px 16px; vertical-align:middle; }}

    .td-party {{ display:flex; align-items:center; gap:12px; font-weight:500; font-size:14px; min-width:200px; }}
    .td-bar {{ width:160px; padding-right:8px; }}
    .bar {{ height:8px; border-radius:var(--md-sys-shape-corner-full); min-width:4px; }}
    .td-num {{ font-variant-numeric:tabular-nums; font-size:13px; white-space:nowrap; }}
    .bold {{ font-weight:600; font-size:15px; }}
    .pos {{ color:var(--md-sys-color-tertiary); }}
    .neg {{ color:var(--md-sys-color-inverse-tertiary); }}
    .neu {{ color:var(--md-sys-color-on-surface-variant); }}

    .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
    .dot.sm {{ width:8px; height:8px; }}

    /* Constituency cards – MD3 filled */
    .const-grid {{
      display:grid;
      grid-template-columns:repeat(auto-fill, minmax(360px, 1fr));
      gap:16px;
    }}
    .const-card {{
      background:var(--md-sys-color-surface-container);
      border-radius:var(--md-sys-shape-corner-large);
      border:1px solid var(--md-sys-color-outline-variant);
      overflow:hidden;
      transition:box-shadow .2s, border-color .2s;
    }}
    .const-card:hover {{ box-shadow:var(--md-sys-elevation-2); border-color:var(--md-sys-color-outline); }}
    .const-head {{
      display:flex; align-items:center; justify-content:space-between; gap:8px;
      padding:12px 16px;
      background:var(--md-sys-color-surface-container-high);
      border-bottom:1px solid var(--md-sys-color-outline-variant);
    }}
    .const-name {{ font-weight:600; font-size:13px; }}
    .badge {{
      font-size:11px; font-weight:500;
      padding:4px 12px; border-radius:var(--md-sys-shape-corner-full);
      white-space:nowrap; flex-shrink:0;
    }}
    .const-meta {{
      display:flex; gap:16px; padding:10px 16px;
      font-size:11px; color:var(--md-sys-color-on-surface-variant);
      border-bottom:1px solid var(--md-sys-color-outline-variant);
    }}
    .const-meta b {{ color:var(--md-sys-color-on-surface); }}
    .const-cands {{ padding:12px 16px; display:flex; flex-direction:column; gap:8px; }}
    .cand {{
      display:grid;
      grid-template-columns:8px 1fr auto 72px 52px 40px;
      align-items:center; gap:8px;
    }}
    .cand-name {{ font-size:12px; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .cand-party {{ font-size:11px; color:var(--md-sys-color-on-surface-variant); white-space:nowrap; }}
    .mini-bar-wrap {{ height:6px; background:var(--md-sys-color-outline-variant); border-radius:var(--md-sys-shape-corner-full); overflow:hidden; }}
    .mini-bar {{ height:100%; border-radius:var(--md-sys-shape-corner-full); }}
    .cand-votes {{ font-variant-numeric:tabular-nums; font-size:11px; text-align:right; }}
    .cand-pct {{ font-variant-numeric:tabular-nums; font-size:10px; color:var(--md-sys-color-on-surface-variant); text-align:right; }}

    /* Footer */
    footer {{
      text-align:center; padding:24px;
      font-size:12px; color:var(--md-sys-color-on-surface-variant);
      border-top:1px solid var(--md-sys-color-outline-variant);
      background:var(--md-sys-color-surface);
    }}

    @media(max-width:600px) {{
      .const-grid {{ grid-template-columns:1fr; }}
      .td-bar {{ display:none; }}
      .topbar {{ gap:8px; padding:0 12px; }}
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

<footer><a href="https://instagram.com/daulricc">Instagram @daulricc</a></footer>

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