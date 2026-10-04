"""
Operation Get Employed — Portfolio Project 1
Cleaning script for the UN International Energy Statistics dataset
(kaggle.com/datasets/unitednations/international-energy-statistics)

v2 — adds:
- Typo/capitalization fixes for commodity names
- A 'commodity_clean' column with consistent naming
- A 'commodity_group' column (Coal, Electricity, Natural Gas, etc.)
  so you can analyze by broad category without double-counting
- A 'metric_type' flag separating:
    - "Production"      -> actual output/generation (what you'll usually sum)
    - "Capacity"         -> generating capacity, NOT output (don't sum with production)
    - "Reserves"         -> resource reserves, NOT a flow (don't sum with production)
    - "Sub-breakdown"    -> electricity broken out by source/producer type
                            (e.g. 'Hydro – Main activity') — these are PARTS of
                            total 'Electricity', so summing Electricity + all
                            sub-breakdowns together double-counts

What this does:
1. Loads the raw all_energy_statistics.csv
2. Filters down to Nigeria + a set of peer/comparison countries
3. Splits 'commodity_transaction' into separate 'commodity' and 'transaction' columns
4. Cleans commodity names (typos, casing) and tags group + metric_type
5. Pivots into a wide, analysis-ready shape (one row per country/commodity/year)
6. Saves a cleaned CSV you can load into SQL or Power BI

Before running:
- Download all_energy_statistics.csv from Kaggle and place it in the same folder
  as this script (or update RAW_FILE below with the correct path).
- pip install pandas
"""

import pandas as pd

# ---------- CONFIG ----------
RAW_FILE = "all_energy_statistics.csv"
OUTPUT_FILE = "energy_clean.csv"

# Nigeria + a comparison set. Edit this list to whichever countries
# you want your story to focus on.
COUNTRIES = [
    "Nigeria",
    "South Africa",
    "Egypt",
    "Ghana",
    "Kenya",
    "Morocco",
]

# Commodities to keep. The raw data has many (coal, oil, gas, biofuels, etc.)
# Start narrow — you can widen this list later once you see what's available.
COMMODITIES_KEEP = [
    "Electricity",
    "Hydro",
    "Solar",
    "Wind",
    "Natural gas",
    "Coal",
]

# Known typos / inconsistent casing -> corrected name.
# Add to this dict as you spot more issues in future runs.
TYPO_FIXES = {
    "Hrad coal": "Hard coal",
    "Natural Gas (including LNG)": "Natural gas (including LNG)",
}

# Maps a (cleaned) commodity name to a broad group, for category-level analysis.
COMMODITY_GROUP_MAP = {
    "Coal": "Coal",
    "Hard coal": "Coal",
    "Brown coal briquettes": "Coal",
    "Lignite brown coal": "Coal",
    "Lignite brown coal- recoverable resources": "Coal",
    "Other bituminous coal": "Coal",
    "Coking coal": "Coal",
    "Charcoal": "Coal",
    "Natural gas (including LNG)": "Natural Gas",
    "Natural gas liquids": "Natural Gas",
    "Other hydrocarbons": "Other Hydrocarbons",
    "Electricity": "Electricity (Total)",
    "Electricity generating capacity": "Electricity (Total)",
    "From combustible fuels – Autoproducer – Electricity plants": "Electricity (By Source)",
    "From combustible fuels – Main activity – Electricity plants": "Electricity (By Source)",
    "Hydro – Main activity": "Electricity (By Source)",
    "Hydro – Autoproducer": "Electricity (By Source)",
    "Of which: Pumped hydro – Main activity": "Electricity (By Source)",
    "Solar – Main activity": "Electricity (By Source)",
    "Solar photovoltaic – Main activity": "Electricity (By Source)",
    "Wind – Main activity": "Electricity (By Source)",
    "Geothermal – Main activity – Electricity plants": "Electricity (By Source)",
    "Nuclear – Main activity – Electricity plants": "Electricity (By Source)",
    "Direct use of solar thermal heat": "Solar (Direct Use)",
}

# Flags rows that are NOT comparable to production/generation flows.
# These should usually be excluded (or analyzed separately) rather than
# summed together with production figures.
CAPACITY_KEYWORDS = ["generating capacity"]
RESERVE_KEYWORDS = ["recoverable resources"]
SUB_BREAKDOWN_KEYWORDS = [
    "main activity",
    "autoproducer",
    "pumped hydro",
    "electricity plants",
]
# -----------------------------


def load_raw(path: str) -> pd.DataFrame:
    print(f"Loading {path} ...")
    df = pd.read_csv(path, low_memory=False)
    print(f"Raw shape: {df.shape}")
    return df


def filter_countries(df: pd.DataFrame, countries: list) -> pd.DataFrame:
    out = df[df["country_or_area"].isin(countries)].copy()
    print(f"After country filter: {out.shape}")
    return out


def split_commodity_transaction(df: pd.DataFrame) -> pd.DataFrame:
    split_cols = df["commodity_transaction"].str.split(" - ", n=1, expand=True)
    df["commodity"] = split_cols[0].str.strip()
    df["transaction"] = split_cols[1].str.strip() if split_cols.shape[1] > 1 else None
    return df


def filter_commodities(df: pd.DataFrame, commodities: list) -> pd.DataFrame:
    pattern = "|".join(commodities)
    out = df[df["commodity"].str.contains(pattern, case=False, na=False)].copy()
    print(f"After commodity filter: {out.shape}")
    return out


def clean_commodity_names(df: pd.DataFrame) -> pd.DataFrame:
    df["commodity_clean"] = df["commodity"].replace(TYPO_FIXES)
    return df


def tag_commodity_group(df: pd.DataFrame) -> pd.DataFrame:
    df["commodity_group"] = df["commodity_clean"].map(COMMODITY_GROUP_MAP)
    unmapped = df[df["commodity_group"].isna()]["commodity_clean"].unique()
    if len(unmapped) > 0:
        print(f"WARNING: these commodities have no group mapping yet: {list(unmapped)}")
        df["commodity_group"] = df["commodity_group"].fillna("Unmapped")
    return df


def tag_metric_type(df: pd.DataFrame) -> pd.DataFrame:
    name_lower = df["commodity_clean"].str.lower()
    unit_lower = df["unit"].fillna("").str.lower()

    is_capacity_name = name_lower.apply(lambda x: any(k in x for k in CAPACITY_KEYWORDS))
    is_reserve = name_lower.apply(lambda x: any(k in x for k in RESERVE_KEYWORDS))
    is_sub_breakdown = name_lower.apply(lambda x: any(k in x for k in SUB_BREAKDOWN_KEYWORDS))

    # Unit-based capacity detection: a commodity can be named 'Electricity' for
    # BOTH its production rows (measured in energy: kilowatt-HOURS) and its
    # capacity rows (measured in power: kilowatts, no "hours"). The name alone
    # can't tell these apart — the unit can. Treat "kilowatts"/"watts" without
    # "hour" in the unit as a capacity reading, not a production flow.
    is_capacity_unit = unit_lower.str.contains("watt") & ~unit_lower.str.contains("hour")

    df["metric_type"] = "Production"
    df.loc[is_sub_breakdown, "metric_type"] = "Sub-breakdown"
    df.loc[is_reserve, "metric_type"] = "Reserves"
    df.loc[is_capacity_name | is_capacity_unit, "metric_type"] = "Capacity"
    return df


def clean_quantity(df: pd.DataFrame) -> pd.DataFrame:
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["quantity"])
    print(f"Dropped {before - len(df)} rows with non-numeric/missing quantity")
    return df


def main():
    df = load_raw(RAW_FILE)

    expected_cols = {
        "country_or_area",
        "commodity_transaction",
        "year",
        "unit",
        "quantity",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        print(f"WARNING: expected columns not found: {missing}")
        print(f"Actual columns: {list(df.columns)}")

    df = filter_countries(df, COUNTRIES)
    df = split_commodity_transaction(df)
    df = filter_commodities(df, COMMODITIES_KEEP)
    df = clean_commodity_names(df)
    df = tag_commodity_group(df)
    df = tag_metric_type(df)
    df = clean_quantity(df)

    # Drop the original messy 'commodity' column before renaming
    # 'commodity_clean' to 'commodity' — otherwise you end up with two
    # columns sharing the same name.
    df = df.drop(columns=["commodity"]).rename(columns={"commodity_clean": "commodity"})

    keep_cols = [
        "country_or_area",
        "year",
        "commodity",
        "commodity_group",
        "metric_type",
        "transaction",
        "unit",
        "quantity",
    ]
    df = df[keep_cols].sort_values(
        ["country_or_area", "commodity_group", "commodity", "year"]
    )

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved cleaned file: {OUTPUT_FILE} ({df.shape[0]} rows)")

    print("\nSample of cleaned data:")
    print(df.head(10))

    print("\nCountries present after filtering:")
    print(df["country_or_area"].unique())

    print("\nCommodity groups present:")
    print(df["commodity_group"].unique())

    print("\nMetric types present (use this to decide what to sum together):")
    print(df["metric_type"].value_counts())


if __name__ == "__main__":
    main()
