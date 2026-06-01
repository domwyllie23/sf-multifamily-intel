"""
Fetch Redfin market tracker data for Bay Area multifamily analysis.
Metro file: ~110MB compressed, downloaded fully.
Zip file: ~1.5GB compressed, streamed and filtered on the fly.
"""

import requests
import pandas as pd
import gzip
import io
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

METRO_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/redfin_metro_market_tracker.tsv000.gz"
ZIP_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/zip_code_market_tracker.tsv000.gz"

BAY_AREA_METROS = [
    "San Francisco, CA",
    "Oakland, CA",
    "San Jose, CA",
    "Fremont, CA",
    "Santa Rosa, CA",
    "Vallejo, CA",
]

# Bay Area zip codes (all 9 counties)
# We filter by state + known metro regions in the data
BAY_AREA_STATE = "CA"
BAY_AREA_METRO_KEYWORDS = ["San Francisco", "San Jose", "Oakland", "Vallejo", "Santa Rosa", "Napa"]

MULTIFAMILY_TYPES = ["Multi-Family (2-4 Unit)", "Condo/Co-op", "Townhouse"]


def fetch_metro_data() -> pd.DataFrame:
    print("Downloading Redfin metro data (~110MB)...")
    resp = requests.get(METRO_URL, stream=True, timeout=300)
    resp.raise_for_status()

    content = b""
    total = 0
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        content += chunk
        total += len(chunk)
        if total % (10 * 1024 * 1024) == 0:
            print(f"  {total // 1024 // 1024}MB downloaded...")

    print("  Decompressing...")
    with gzip.open(io.BytesIO(content)) as f:
        df = pd.read_csv(f, sep="\t", low_memory=False)

    # Filter to Bay Area metros and multifamily/condo property types
    mask_metro = df["PARENT_METRO_REGION"].str.contains(
        "|".join(BAY_AREA_METRO_KEYWORDS), case=False, na=False
    )
    mask_state = df["STATE_CODE"] == BAY_AREA_STATE
    df_bay = df[mask_metro & mask_state].copy()

    out_path = RAW_DIR / "redfin_metro_bayarea.csv"
    df_bay.to_csv(out_path, index=False)
    print(f"  {len(df_bay)} rows saved to {out_path}")

    # Also save multifamily subset
    mf_mask = df_bay["PROPERTY_TYPE"].isin(MULTIFAMILY_TYPES)
    df_mf = df_bay[mf_mask]
    mf_path = RAW_DIR / "redfin_metro_bayarea_multifamily.csv"
    df_mf.to_csv(mf_path, index=False)
    print(f"  {len(df_mf)} multifamily rows saved to {mf_path}")

    return df_bay


def fetch_zip_data_streaming() -> pd.DataFrame:
    """Stream the 1.5GB zip file and filter to Bay Area without loading it all into memory."""
    print("Streaming Redfin zip data (1.5GB compressed — filtering on the fly)...")
    resp = requests.get(ZIP_URL, stream=True, timeout=600)
    resp.raise_for_status()

    # Buffer compressed content
    print("  Buffering... (this takes a few minutes)")
    content = b""
    total = 0
    for chunk in resp.iter_content(chunk_size=4 * 1024 * 1024):
        content += chunk
        total += len(chunk)
        if total % (100 * 1024 * 1024) == 0:
            print(f"  {total // 1024 // 1024}MB buffered...")

    print("  Decompressing and filtering...")
    with gzip.open(io.BytesIO(content)) as f:
        chunks = []
        reader = pd.read_csv(f, sep="\t", chunksize=50000, low_memory=False)
        for i, chunk in enumerate(reader):
            bay = chunk[
                chunk["STATE_CODE"].eq(BAY_AREA_STATE) &
                chunk["PARENT_METRO_REGION"].str.contains(
                    "|".join(BAY_AREA_METRO_KEYWORDS), case=False, na=False
                )
            ]
            if not bay.empty:
                chunks.append(bay)
            if i % 50 == 0:
                print(f"  Processed chunk {i}...")

    if not chunks:
        print("  No Bay Area data found.")
        return pd.DataFrame()

    df = pd.concat(chunks, ignore_index=True)
    out_path = RAW_DIR / "redfin_zip_bayarea.csv"
    df.to_csv(out_path, index=False)
    print(f"  {len(df)} rows saved to {out_path}")
    return df


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetch_metro_data()
    # Zip file is optional — takes ~10min; comment out if not needed
    # fetch_zip_data_streaming()
