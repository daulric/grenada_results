import json
import re
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}
KNOWN_ELECTION_YEARS = [1984, 1990, 1995, 1999, 2003, 2008, 2013, 2018, 2022]


def wiki_url(year: int) -> str:
    return f"https://en.wikipedia.org/wiki/{year}_Grenadian_general_election"


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\[\d+\]", "", text)   # remove footnote refs [1]
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_int(value: str) -> int | None:
    cleaned = re.sub(r"[^\d]", "", value)
    return int(cleaned) if cleaned else None


def parse_float(value: str) -> float | None:
    cleaned = re.sub(r"[^\d.]", "", value)
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def is_results_table(table) -> bool:
    """Return True if this wikitable has Party, Votes, and Seats columns."""
    for row in table.find_all("tr"):
        headers = [th.get_text(strip=True).lower() for th in row.find_all("th")]
        has_party = any("party" in h for h in headers)
        has_votes = any("votes" in h for h in headers)
        has_seats = any("seats" in h for h in headers)
        if has_party and has_votes and has_seats:
            return True
    return False


def find_results_table(soup: BeautifulSoup):
    """Find the party results summary table."""
    for tbl in soup.find_all("table", class_="wikitable"):
        if is_results_table(tbl):
            return tbl
    return None



def is_constituency_table(table) -> bool:
    """Return True if this wikitable has a Constituency column."""
    for row in table.find_all("tr"):
        headers = [th.get_text(strip=True).lower() for th in row.find_all("th")]
        if any("constituency" in h for h in headers):
            return True
    return False


def find_constituency_table(soup: BeautifulSoup) -> object:
    """Find the by-constituency table only if #By_constituency anchor exists."""
    if not soup.find(id="By_constituency"):
        return None
    for tbl in soup.find_all("table", class_="wikitable"):
        if is_constituency_table(tbl):
            return tbl
    return None


def parse_by_constituency_table(table) -> list[dict]:
    """
    Parse the single 'By constituency' table.
    Columns: Constituency | Electorate | Turnout | % | Political party | Candidate | Votes | %
    Constituency cells span multiple candidate rows via rowspan.
    """
    rows = table.find_all("tr")
    if not rows:
        return []

    # Find real header row containing "Constituency"
    header_row = None
    header_row_idx = 0
    for i, row in enumerate(rows):
        texts = [th.get_text(strip=True).lower() for th in row.find_all("th")]
        if any("constituency" in t for t in texts):
            header_row = row
            header_row_idx = i
            break

    if not header_row:
        return []

    # Build flat headers expanding colspan
    headers = []
    for th in header_row.find_all("th"):
        text = clean_text(th.get_text()).lower()
        for _ in range(int(th.get("colspan", 1))):
            headers.append(text)

    def col_idx(*names):
        for name in names:
            for i, h in enumerate(headers):
                if name in h:
                    return i
        return None

    const_col     = col_idx("constituency")
    elect_col     = col_idx("electorate")
    turnout_col   = col_idx("turnout")
    party_col     = col_idx("party", "political")
    candidate_col = col_idx("candidate")
    votes_col     = col_idx("votes")
    pct_indices   = [i for i, h in enumerate(headers) if h.strip() in ("%", "percentage")]
    turnout_pct_col = pct_indices[0] if len(pct_indices) >= 1 else None
    pct_col         = pct_indices[1] if len(pct_indices) >= 2 else (pct_indices[0] if pct_indices else None)

    constituencies: dict[str, dict] = {}
    current_constituency = None

    for row in rows[header_row_idx + 1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        row_text = clean_text(row.get_text()).lower()
        if any(kw in row_text for kw in ("total", "source", "valid votes", "invalid", "registered")):
            continue

        first_cell      = cells[0]
        first_cell_text = clean_text(first_cell.get_text())
        is_new = bool(first_cell.get("rowspan")) or (
            const_col == 0
            and first_cell_text
            and not first_cell_text.replace(",", "").replace(".", "").isdigit()
        )

        if is_new and first_cell_text:
            current_constituency = first_cell_text

        if not current_constituency:
            continue

        data_cells = cells[1:] if is_new else cells

        def get(idx):
            if idx is None:
                return ""
            adjusted = idx - 1
            if 0 <= adjusted < len(data_cells):
                return clean_text(data_cells[adjusted].get_text())
            return ""

        electorate = get(elect_col)  if is_new else ""
        turnout    = get(turnout_col) if is_new else ""
        t_pct      = get(turnout_pct_col) if is_new else ""

        party     = get(party_col)
        if not party and party_col is not None:
            party = get(party_col + 1)
        candidate = get(candidate_col)
        votes_str = get(votes_col)
        pct_str   = get(pct_col)

        if not candidate and not votes_str:
            continue

        if current_constituency not in constituencies:
            constituencies[current_constituency] = {
                "constituency": current_constituency,
                "electorate":   parse_int(electorate),
                "turnout":      parse_int(turnout),
                "turnout_pct":  parse_float(t_pct),
                "candidates":   [],
            }

        constituencies[current_constituency]["candidates"].append({
            "candidate":  candidate,
            "party":      party,
            "votes":      parse_int(votes_str),
            "percentage": parse_float(pct_str),
        })

    result = []
    for name, data in constituencies.items():
        candidates = data["candidates"]
        total_votes = sum(c["votes"] for c in candidates if c["votes"] is not None)
        winner = max(
            (c for c in candidates if c["votes"] is not None),
            key=lambda c: c["votes"],
            default=None,
        )
        result.append({
            "constituency": name,
            "electorate":   data["electorate"],
            "turnout":      data["turnout"],
            "turnout_pct":  data["turnout_pct"],
            "total_votes":  total_votes,
            "winner": {
                "candidate": winner["candidate"] if winner else None,
                "party":     winner["party"]     if winner else None,
                "votes":     winner["votes"]     if winner else None,
            },
            "candidates": candidates,
        })

    return result

def parse_results_table(table) -> list[dict]:
    """
    Parse the party summary results table.
    Columns: Party | Votes | % | Seats | +/-
    """
    rows = table.find_all("tr")
    if not rows:
        return []

    # Find real header row
    header_row = None
    header_row_idx = 0
    for i, row in enumerate(rows):
        ths = row.find_all("th")
        texts = [th.get_text(strip=True).lower() for th in ths]
        if any("votes" in t for t in texts):
            header_row = row
            header_row_idx = i
            break

    if not header_row:
        return []

    # Build flat headers expanding colspan
    headers = []
    for th in header_row.find_all("th"):
        text = clean_text(th.get_text()).lower()
        span = int(th.get("colspan", 1))
        for _ in range(span):
            headers.append(text)

    def col_idx(*names):
        for name in names:
            for i, h in enumerate(headers):
                if name in h:
                    return i
        return None

    party_col = col_idx("party")
    votes_col = col_idx("votes")
    seats_col = col_idx("seats")
    pct_indices = [i for i, h in enumerate(headers) if h.strip() == "%"]
    pct_col = pct_indices[0] if pct_indices else None
    change_col = col_idx("+", "change", "swing")

    results = []
    for row in rows[header_row_idx + 1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        row_text = clean_text(row.get_text()).lower()
        if any(kw in row_text for kw in ("total", "source", "valid", "invalid", "registered", "blank")):
            continue

        def get(idx):
            if idx is not None and idx < len(cells):
                return clean_text(cells[idx].get_text())
            return ""

        party = get(party_col)
        # Party col has colspan=2 (color swatch + name); if empty, try next cell
        if not party and party_col is not None:
            party = get(party_col + 1)
        votes = get(votes_col)
        pct   = get(pct_col)
        seats = get(seats_col)
        change = get(change_col)

        if not party and not votes:
            continue

        results.append({
            "party":   party,
            "votes":   parse_int(votes),
            "percentage": parse_float(pct),
            "seats":   parse_int(seats),
            "change":  change,
        })

    return results


def scrape_election_results(year: int, debug: bool = False) -> dict:
    url = wiki_url(year)

    # ------------------------------------------------------------------ #
    # Fetch page
    # ------------------------------------------------------------------ #
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: Could not connect to Wikipedia.\n   {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out.", file=sys.stderr)
        sys.exit(1)

    if resp.status_code == 404:
        nearby = [y for y in KNOWN_ELECTION_YEARS if y != year]
        print(
            f"❌ ERROR: No Wikipedia article found for the {year} Grenadian general election.\n"
            f"   URL attempted: {url}\n"
            f"   Known election years: {', '.join(str(y) for y in nearby)}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not resp.ok:
        print(f"❌ ERROR: Wikipedia returned HTTP {resp.status_code} for {url}", file=sys.stderr)
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    # ------------------------------------------------------------------ #
    # Find the "By constituency" table
    # ------------------------------------------------------------------ #
    table = find_results_table(soup)

    if not table:
        print(
            f"❌ ERROR: Could not find a by-constituency table in the {year} article.\n"
            f"   Check manually: {url}",
            file=sys.stderr,
        )
        sys.exit(1)

    # ------------------------------------------------------------------ #
    # Parse
    # ------------------------------------------------------------------ #
    if debug:
        rows = table.find_all("tr")
        print(f"\n🔍 DEBUG: Table found with {len(rows)} rows", file=sys.stderr)
        # Print ALL header rows (some tables have 2 header rows)
        for i, row in enumerate(rows[:3]):
            ths = row.find_all("th")
            tds = row.find_all("td")
            print(f"   Header row {i}: th={[t.get_text(strip=True)[:25] for t in ths]} td={[t.get_text(strip=True)[:25] for t in tds]}", file=sys.stderr)
        print(f"   ---", file=sys.stderr)
        for i, row in enumerate(rows[1:8], 1):
            cells = row.find_all(["td", "th"])
            cell_info = [(c.name, c.get_text(strip=True)[:25], c.get("rowspan"), c.get("colspan")) for c in cells]
            print(f"   Row {i}: {cell_info}", file=sys.stderr)

    results = parse_results_table(table)

    if not results:
        print(
            f"❌ ERROR: Found the table for {year} but could not parse any rows.\n"
            f"   Check: {url}#Results",
            file=sys.stderr,
        )
        sys.exit(1)

    return {
        "election": f"{year} Grenadian General Election",
        "year":     year,
        "results":  results,
    }


if __name__ == "__main__":
    debug = "--debug" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(args) != 1:
        print(
            "Usage:   uv run scrape_grenada_election.py <year> [--debug]\n"
            "Example: uv run scrape_grenada_election.py 2022\n"
            "         uv run scrape_grenada_election.py 2018 --debug",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        year = int(args[0])
    except ValueError:
        print(f"❌ ERROR: '{args[0]}' is not a valid year.", file=sys.stderr)
        sys.exit(1)

    print(f"Scraping {year} Grenadian General Election results ...")
    data = scrape_election_results(year, debug=debug)

    output_dir = Path("results") / str(year)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"election_general.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! Results saved to '{output_file}'")
    print(f"   Parties scraped: {len(data['results'])}")
    for r in data["results"]:
        votes_str = f"{r['votes']:,}" if r['votes'] is not None else "?"
        print(f"   • {r['party']:<40} {votes_str:>8} votes  {r['percentage']}%  {r['seats']} seats")

    # --- Constituency breakdown (only if #By_constituency exists) ---
    soup = BeautifulSoup(
        requests.get(wiki_url(year), headers=HEADERS, timeout=15).text, "html.parser"
    )
    const_table = find_constituency_table(soup)
    if const_table:
        constituencies = parse_by_constituency_table(const_table)
        if constituencies:
            const_file = output_dir / f"election_constituency.json"
            with open(const_file, "w", encoding="utf-8") as f:
                json.dump({
                    "election":       f"{year} Grenadian General Election",
                    "year":           year,
                    "constituencies": constituencies,
                }, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Constituency data saved to '{const_file}'")
            print(f"   Constituencies scraped: {len(constituencies)}")
            for c in constituencies:
                w = c["winner"]
                v = f"{w['votes']:,}" if w["votes"] is not None else "?"
                print(f"   • {c['constituency']:<35} -> {w['candidate']} ({w['party']}) – {v} votes")
    else:
        print(f"\nℹ️  No #By_constituency section found for {year} — skipping constituency file.")