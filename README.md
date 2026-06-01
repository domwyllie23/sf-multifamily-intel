# SF Bay Area Multifamily Investment Intelligence

A data pipeline and analysis toolkit that replicates the top-of-funnel workflow of a multifamily acquisitions team — market selection, distressed deal sourcing, and price forecasting — using entirely public data sources.

Built as a portfolio project targeting real estate acquisitions analyst roles.

---

## What it does

### 1. Market Selection (`notebooks/01_market_selection.ipynb`)
Scores all 274 Bay Area zip codes on 8 investment factors and produces a composite ranking:

| Factor | Signal |
|--------|--------|
| Renter % of households | Structural multifamily demand |
| Vacancy rate | Market tightness and pricing power |
| Rent-to-income ratio | Headroom for rent growth |
| Rent burden rate | Affordability ceiling |
| Multifamily housing share | Established MF market, permissive zoning |
| 1-year price momentum | Appreciation trend |
| Price cut rate | Seller vs. buyer power |
| Inventory change | Supply tightness |

Output: ranked zip code table, factor heatmap, and interactive choropleth map.

### 2. Distressed Signal Detection (`notebooks/02_distressed_signals.ipynb`)
Uses SF eviction notice data and building permit activity to surface neighborhoods with motivated sellers:

- **Eviction rate per 1,000 renter units** — operator financial distress
- **Ellis Act withdrawals** — owners exiting the rental market entirely
- **Owner move-in evictions** — repositioning signal
- **Permit activity gap** — deferred maintenance from capital-constrained operators

Key output: **Opportunity Matrix** — a scatter plot of distress score vs. market attractiveness, highlighting zip codes with motivated sellers in fundamentally strong submarkets.

### 3. Price Forecasting (`notebooks/03_price_forecasting.ipynb`)
SARIMA time series models fit on Zillow Home Value Index data (monthly, 2018–present) to produce 12-month price forecasts with 80% confidence intervals for each Bay Area county.

Also includes Redfin transaction-level market health indicators: days on market, months of supply, sale-to-list ratio, and price drop frequency.

---

## Data Sources

All free and publicly available:

| Source | Data | Update frequency |
|--------|------|-----------------|
| [Zillow Research](https://www.zillow.com/research/data/) | ZHVI price index, inventory, price cuts (zip-level) | Monthly |
| [Redfin Data Center](https://www.redfin.com/news/data-center/) | Transaction metrics by metro and property type | Monthly |
| [US Census ACS 5-year](https://www.census.gov/programs-surveys/acs) | Renter rates, vacancy, rent burden, MF housing share | Annual |
| [SF OpenData](https://data.sfgov.org) | Eviction notices, building permits | Monthly |

---

## Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/sf-multifamily-intel.git
cd sf-multifamily-intel

# Install dependencies
pip install -r requirements.txt

# Fetch data (takes ~5 minutes)
python src/fetch_zillow.py
python src/fetch_redfin.py
python src/fetch_census.py
python src/fetch_opendata.py
python src/fetch_permits_supply.py

# Launch Jupyter
jupyter lab
```

Run notebooks in order: `01_market_selection` → `02_distressed_signals` → `03_price_forecasting`.

---

## Key Outputs

After running, `outputs/` contains:

```
outputs/
├── charts/
│   ├── factor_heatmap_top10.png      # Factor breakdown for top 10 zip codes
│   ├── opportunity_matrix.png        # Distress vs. market quality scatter
│   ├── price_forecasts.png           # 12-month SARIMA forecasts by county
│   ├── county_price_history.png      # ZHVI history 2015–present
│   ├── evictions_by_neighborhood.png # SF distress signals by neighborhood
│   └── ...
├── maps/
│   └── market_selection_map.html     # Interactive choropleth (open in browser)
└── tables/
    ├── market_selection_ranked.csv   # All 274 zip codes, scored and ranked
    ├── distress_scores_ranked.csv    # Zip codes ranked by distress signal
    └── price_forecasts_12mo.csv      # 12-month forecasts by county
```

---

## Sample Findings (May 2026 run)

**Top markets by investment score:** SF zip codes dominate — 94117 (Haight-Ashbury), 94123 (Marina), 94114 (Castro) — driven by 65–75% renter rates and sub-10% vacancy.

**Highest distress signals:** 94110 (Mission) — 39 Ellis Act withdrawals since 2022. 94103 (SoMa) and 94107 (Potrero) lead on eviction rate per 1,000 renter units.

**12-month price forecasts:** SF County +6.5%, San Mateo +4.4%, Contra Costa +0.4%, Santa Clara -1.0%, Alameda -1.2%.

---

## Limitations

- Price data is ZHVI (all-home repeat-sales index) — multifamily-specific cap rate or NOI data requires CoStar/RCA access
- Rent index (ZORI) became paywalled; median contract rent from ACS used as proxy
- Distressed signal analysis is limited to San Francisco city data; Oakland open data API was unavailable
- Forecasts are statistical projections, not fundamental underwriting

---

## Stack

Python 3.13 · pandas · numpy · statsmodels (SARIMA) · matplotlib · folium · requests · beautifulsoup4
