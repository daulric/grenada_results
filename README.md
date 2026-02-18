# Grenada General Election Results Scraper

This tool scrapes Grenada General Election results from Wikipedia, extracting both overall party performance and detailed constituency-level data.

It supports historical election data from 1984 to 2022.

## Features

- **Historical Data**: Supports election years 1984, 1990, 1995, 1999, 2003, 2008, 2013, 2018, and 2022.
- **Dual Extraction**:
  - **Overall Results**: Party vote counts, percentages, seat allocations, and swings.
  - **Constituency Breakdown**: Detailed results for each constituency, including candidates, votes, and turnout.
- **Structured Output**: Saves data in clean, machine-readable JSON format, organized by year.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd election_results
    ```

2.  Install dependencies:
    ```bash
    uv sync
    ```
    Or manually:
    ```bash
    pip install requests beautifulsoup4
    ```

## Usage

Run the script by providing the election year you want to scrape:

```bash
uv run main.py <year>
```

### Examples

Scrape the 2022 election:
```bash
uv run main.py 2022
```

Scrape the 1984 election:
```bash
uv run main.py 1984
```

Enable debug mode for troubleshooting:
```bash
uv run main.py 2022 --debug
```

## Output

The script generates JSON files in the `results/` directory, organized by year:

### 1. Overall Results (`results/<year>/election_general.json`)
Contains the summary of the election, including total votes and seats per party.

```json
{
  "election": "2022 Grenadian General Election",
  "year": 2022,
  "source": "https://en.wikipedia.org/wiki/2022_Grenadian_general_election",
  "results": [
    {
      "party": "National Democratic Congress",
      "votes": 31430,
      "percentage": 51.8,
      "seats": 9,
      "change": "+9"
    },
    ...
  ]
}
```

### 2. Constituency Results (`results/<year>/election_constituency.json`)
Contains detailed breakdowns for each constituency (if available for that year).

```json
{
  "election": "2022 Grenadian General Election",
  "constituencies": [
    {
      "constituency": "Carriacou and Petite Martinique",
      "electorate": 5352,
      "turnout": 3894,
      "turnout_pct": 72.76,
      "winner": {
        "candidate": "Tevin Andrews",
        "party": "National Democratic Congress",
        "votes": 1954
      },
      "candidates": [
        {
          "candidate": "Tevin Andrews",
          "party": "National Democratic Congress",
          "votes": 1954,
          "percentage": 50.18
        },
        ...
      ]
    }
  ]
}
```

By (daulric)[https://daulric.dev]
Instagram: https://instagram.com/daulricc