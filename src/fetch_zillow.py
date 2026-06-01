"""
Fetch Zillow Research data for Bay Area multifamily analysis.
Downloads ZORI (rent index) and ZHVI (home value index) CSVs directly from Zillow Research.
"""

import pandas as pd
import requests
import os
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

BAY_AREA_COUNTIES = [
    "Alameda County", "Contra Costa County", "Marin County",
    "Napa County", "San Francisco County", "San Mateo County",
    "Santa Clara County", "Solano County", "Sonoma County"
]

BAY_AREA_METROS = ["San Francisco-Oakland-Fremont, CA", "San Jose-Sunnyvale-Santa Clara, CA"]

ZILLOW_URLS = {
    # Zillow Observed Rent Index — All Homes (apartment-focused), by zip
    "zori_zip": "https://files.zillowstatic.com/research/public_csvs/zori/Zip_ZORI_AllHomesPlusMultifamily_Smoothed.csv",
    # ZORI by metro
    "zori_metro": "https://files.zillowstatic.com/research/public_csvs/zori/Metro_ZORI_AllHomesPlusMultifamily_Smoothed.csv",
    # ZHVI — All homes, by zip (price index)
    "zhvi_zip": "https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    # Median days on market by zip
    "dom_zip": "https://files.zillowstatic.com/research/public_csvs/days_on_market/Zip_median_daystoclose_uc_sfrcondo_month.csv",
    # Inventory by zip
    "inventory_zip": "https://files.zillowstatic.com/research/public_csvs/invt_fs/Zip_invt_fs_uc_sfrcondo_month.csv",
    # Price cuts by zip
    "price_cuts_zip": "https://files.zillowstatic.com/research/public_csvs/perc_listings_price_cut/Zip_perc_listings_price_cut_uc_sfrcondo_month.csv",
}


def download_and_filter(name: str, url: str, geo_col: str = "RegionName") -> pd.DataFrame:
    print(f"Fetching {name}...")
    try:
        df = pd.read_csv(url, dtype={geo_col: str})
    except Exception as e:
        print(f"  Failed: {e}")
        return pd.DataFrame()

    # Filter to Bay Area — county-level files have CountyName, zip files have CountyName too
    if "CountyName" in df.columns:
        df = df[df["CountyName"].isin(BAY_AREA_COUNTIES)]
    elif "Metro" in df.columns:
        df = df[df["Metro"].isin(BAY_AREA_METROS)]

    if df.empty:
        # Try state filter as fallback
        if "State" in df.columns:
            df_ca = df[df["State"] == "CA"]
            if "CountyName" in df_ca.columns:
                df = df_ca[df_ca["CountyName"].isin(BAY_AREA_COUNTIES)]

    print(f"  {len(df)} rows after Bay Area filter")
    out_path = RAW_DIR / f"zillow_{name}.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved to {out_path}")
    return df


def fetch_all():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, url in ZILLOW_URLS.items():
        results[name] = download_and_filter(name, url)
    return results


if __name__ == "__main__":
    fetch_all()
