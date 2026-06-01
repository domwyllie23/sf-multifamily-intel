"""
Fetch US Census Building Permits Survey data for Bay Area counties.
5+ unit permits = multifamily supply pipeline signal.
Annual and monthly data available from Census API.
"""

import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Bay Area county FIPS (state 06)
BAY_AREA_FIPS = {
    "Alameda":       "06001",
    "Contra Costa":  "06013",
    "Marin":         "06041",
    "Napa":          "06055",
    "San Francisco": "06075",
    "San Mateo":     "06081",
    "Santa Clara":   "06085",
    "Solano":        "06095",
    "Sonoma":        "06097",
}

# Annual permits by county: buildings with 5+ units
# Source: Census Building Permits Survey (bps)
PERMITS_BASE = "https://www.census.gov/construction/bps/csv"


def fetch_annual_permits(start_year: int = 2015, end_year: int = 2023) -> pd.DataFrame:
    """
    Download annual county-level permit data from Census BPS.
    Files are named annualc{YY}a.txt (e.g. annualc23a.txt for 2023).
    Columns: FIPS, county name, 1-unit, 2-unit, 3-4 unit, 5+ units (count + value).
    """
    all_years = []

    for year in range(start_year, end_year + 1):
        yy = str(year)[-2:]
        url = f"{PERMITS_BASE}/annualc{yy}a.txt"
        print(f"Fetching {year} permits from {url}...")
        try:
            # Fixed-width or CSV depending on year; try CSV parsing
            df = pd.read_csv(url, header=0, dtype=str)
            df["year"] = year
            all_years.append(df)
            print(f"  {len(df)} rows")
        except Exception as e:
            print(f"  Failed: {e}")

    if not all_years:
        return pd.DataFrame()

    combined = pd.concat(all_years, ignore_index=True)

    # Filter to Bay Area FIPS
    if "FIPS" in combined.columns:
        combined = combined[combined["FIPS"].isin(BAY_AREA_FIPS.values())]
    elif "fips_code" in combined.columns:
        combined = combined[combined["fips_code"].isin(BAY_AREA_FIPS.values())]

    out_path = RAW_DIR / "census_permits_annual.csv"
    combined.to_csv(out_path, index=False)
    print(f"Saved {len(combined)} rows to {out_path}")
    return combined


def fetch_monthly_permits() -> pd.DataFrame:
    """
    Fetch monthly permit data via Census API for most recent 24 months.
    Uses the Building Permits API endpoint.
    """
    url = "https://api.census.gov/data/timeseries/eits/bps"
    params = {
        "get": "COUNTY,PERMITS,category_code,seasonally_adj",
        "for": "county:" + ",".join(f.replace("06", "") for f in BAY_AREA_FIPS.values()),
        "in": "state:06",
        "time": "from 2020-01",
        "category_code": "5",   # 5+ unit buildings
    }

    print("Fetching monthly 5+ unit permits (Census API)...")
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        df["PERMITS"] = pd.to_numeric(df["PERMITS"], errors="coerce")
        out_path = RAW_DIR / "census_permits_monthly.csv"
        df.to_csv(out_path, index=False)
        print(f"  {len(df)} rows saved to {out_path}")
        return df
    except Exception as e:
        print(f"  Failed: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetch_annual_permits()
    fetch_monthly_permits()
