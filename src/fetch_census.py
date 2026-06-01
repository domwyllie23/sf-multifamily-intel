"""
Fetch Census ACS 5-year (2022) data for Bay Area multifamily analysis.
Uses direct file downloads — no API key required.

Tables fetched:
  B25003 — Housing tenure (owner vs renter)
  B25002 — Occupancy status (vacancy)
  B25070 — Gross rent as % of income (rent burden)
  B25058 — Median contract rent
  B19013 — Median household income
  B25024 — Units in structure (multifamily share)
  B01003 — Total population
"""

import requests
import pandas as pd
from io import StringIO
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

ACS_BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData"

# GEO_ID prefix for California zip codes: 8600000US{zip}
# GEO_ID prefix for California counties: 0500000US06{fips3}
CA_ZIP_PREFIX = "860Z200US"    # e.g. 860Z200US94102
CA_COUNTY_PREFIX = "0500000US06"  # e.g. 0500000US06075

BAY_AREA_FIPS3 = ["001", "013", "041", "055", "075", "081", "085", "095", "097"]

TABLES = {
    "b25003": {
        "url": f"{ACS_BASE}/acsdt5y2022-b25003.dat",
        "cols": {
            "B25003_E001": "total_housing_units",
            "B25003_E002": "owner_occupied",
            "B25003_E003": "renter_occupied_units",
        },
    },
    "b25002": {
        "url": f"{ACS_BASE}/acsdt5y2022-b25002.dat",
        "cols": {
            "B25002_E001": "total_units_for_occupancy",
            "B25002_E003": "vacant_units",
        },
    },
    "b25070": {
        "url": f"{ACS_BASE}/acsdt5y2022-b25070.dat",
        "cols": {
            "B25070_E001": "renter_households",
            "B25070_E010": "rent_burden_over50pct",
        },
    },
    "b25058": {
        "url": f"{ACS_BASE}/acsdt5y2022-b25058.dat",
        "cols": {"B25058_E001": "median_contract_rent"},
    },
    "b19013": {
        "url": f"{ACS_BASE}/acsdt5y2022-b19013.dat",
        "cols": {"B19013_E001": "median_household_income"},
    },
    "b25024": {
        "url": f"{ACS_BASE}/acsdt5y2022-b25024.dat",
        "cols": {
            "B25024_E005": "units_5_to_9",
            "B25024_E006": "units_10_to_19",
            "B25024_E007": "units_20_to_49",
            "B25024_E008": "units_50_plus",
            "B25024_E001": "total_units_in_structure",
        },
    },
    "b01003": {
        "url": f"{ACS_BASE}/acsdt5y2022-b01003.dat",
        "cols": {"B01003_E001": "total_population"},
    },
}


def fetch_table(name: str, info: dict) -> pd.DataFrame:
    print(f"  Fetching {name}...")
    resp = requests.get(info["url"], timeout=120)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text), sep="|", dtype={"GEO_ID": str})

    # Keep only columns we care about
    keep = ["GEO_ID"] + list(info["cols"].keys())
    existing = [c for c in keep if c in df.columns]
    df = df[existing].rename(columns=info["cols"])

    # Convert numeric
    for new_name in info["cols"].values():
        if new_name in df.columns:
            df[new_name] = pd.to_numeric(df[new_name], errors="coerce")

    return df


def filter_and_merge(level: str = "zip") -> pd.DataFrame:
    """Fetch all tables and merge into one dataframe. level = 'zip' or 'county'."""
    dfs = []
    for name, info in TABLES.items():
        df = fetch_table(name, info)
        dfs.append(df)

    # Merge on GEO_ID
    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on="GEO_ID", how="outer")

    if level == "zip":
        merged = merged[merged["GEO_ID"].str.startswith(CA_ZIP_PREFIX)].copy()
        merged["zip_code"] = merged["GEO_ID"].str.replace(CA_ZIP_PREFIX, "", regex=False)
        # Keep only California zips (94xxx, 95xxx, 96xxx range)
        merged = merged[merged["zip_code"].str.match(r"^9[456]\d{3}$", na=False)]
    else:
        bay_geo_ids = [f"{CA_COUNTY_PREFIX}{f}" for f in BAY_AREA_FIPS3]
        merged = merged[merged["GEO_ID"].isin(bay_geo_ids)].copy()
        merged["county_fips3"] = merged["GEO_ID"].str[-3:]

    # Derived metrics
    merged["renter_pct"] = merged["renter_occupied_units"] / merged["total_housing_units"]
    merged["vacancy_rate"] = merged["vacant_units"] / merged["total_housing_units"]
    merged["rent_burden_rate"] = merged["rent_burden_over50pct"] / merged["renter_households"]
    merged["rent_to_income_ratio"] = (merged["median_contract_rent"] * 12) / merged["median_household_income"]
    merged["multifamily_units"] = (
        merged.get("units_5_to_9", 0).fillna(0) +
        merged.get("units_10_to_19", 0).fillna(0) +
        merged.get("units_20_to_49", 0).fillna(0) +
        merged.get("units_50_plus", 0).fillna(0)
    )
    merged["multifamily_share"] = merged["multifamily_units"] / merged["total_units_in_structure"]

    return merged


def fetch_all():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching zip-level ACS data...")
    zip_df = filter_and_merge("zip")
    out = RAW_DIR / "census_acs_zip.csv"
    zip_df.to_csv(out, index=False)
    print(f"  {len(zip_df)} CA zips saved to {out}")

    print("Fetching county-level ACS data...")
    county_df = filter_and_merge("county")
    out = RAW_DIR / "census_acs_county.csv"
    county_df.to_csv(out, index=False)
    print(f"  {len(county_df)} Bay Area counties saved to {out}")

    return zip_df, county_df


if __name__ == "__main__":
    fetch_all()
