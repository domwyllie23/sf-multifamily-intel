"""
Fetch SF OpenData and Oakland/Alameda open data for distressed multifamily signals.

SF Socrata API endpoints (no key required, but rate-limited without one):
  - Eviction notices
  - Building permit applications
  - Code enforcement complaints / violations

Oakland open data via their Socrata instance.
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

SF_BASE = "https://data.sfgov.org/resource"
OAKLAND_BASE = "https://data.oaklandca.gov/resource"

# Socrata dataset endpoints
DATASETS = {
    # SF Eviction Notices — strong distressed operator signal
    "sf_evictions": f"{SF_BASE}/5cei-gny5.json",
    # SF Building Permits — look for lack of recent permits (deferred maintenance)
    "sf_permits": f"{SF_BASE}/i98e-djp9.json",
    # SF Code Enforcement Cases
    "sf_complaints": f"{SF_BASE}/k6e8-nw6w.json",
    # Oakland Building Permits
    "oak_permits": f"{OAKLAND_BASE}/ydr8-5enu.json",
}

# How far back to pull (years)
LOOKBACK_YEARS = 5


def fetch_socrata(name: str, url: str, limit: int = 50000, date_field: str = None) -> pd.DataFrame:
    print(f"Fetching {name}...")
    params = {"$limit": limit}

    if date_field:
        cutoff = (datetime.now() - timedelta(days=365 * LOOKBACK_YEARS)).strftime("%Y-%m-%dT00:00:00")
        params["$where"] = f"{date_field} >= '{cutoff}'"

    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
        print(f"  {len(df)} rows")
        out_path = RAW_DIR / f"{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"  Saved to {out_path}")
        return df
    except Exception as e:
        print(f"  Failed: {e}")
        return pd.DataFrame()


def fetch_sf_evictions() -> pd.DataFrame:
    return fetch_socrata("sf_evictions", DATASETS["sf_evictions"], date_field="file_date")


def fetch_sf_permits() -> pd.DataFrame:
    """Fetch building permits — filter to residential, look for multifamily."""
    df = fetch_socrata("sf_permits", DATASETS["sf_permits"], date_field="filed_date")
    if df.empty:
        return df
    # Keep residential permits
    if "permit_type_definition" in df.columns:
        df = df[df["permit_type_definition"].str.contains("residential|apartment|dwelling", case=False, na=False)]
    out_path = RAW_DIR / "sf_permits_residential.csv"
    df.to_csv(out_path, index=False)
    return df


def fetch_sf_complaints() -> pd.DataFrame:
    return fetch_socrata("sf_complaints", DATASETS["sf_complaints"], date_field="opened_date")


def fetch_oak_permits() -> pd.DataFrame:
    return fetch_socrata("oak_permits", DATASETS["oak_permits"], date_field="issued_date")


def fetch_all():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetch_sf_evictions()
    fetch_sf_permits()
    fetch_sf_complaints()
    fetch_oak_permits()


if __name__ == "__main__":
    fetch_all()
