"""
Operation Get Employed — Portfolio Project 1
Quick exploration script — sanity-checks the story before building
SQL/Power BI on top of it.

Run this on energy_clean.csv (output of clean_energy_data.py).

pip install pandas (if not already installed)
"""

import pandas as pd

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 10)

df = pd.read_csv("energy_clean.csv")

print("=" * 70)
print("1) ELECTRICITY PRODUCTION TREND — Nigeria vs peers (latest year available)")
print("=" * 70)
electricity_total = df[
    (df["commodity_group"] == "Electricity (Total)")
    & (df["metric_type"] == "Production")
]
latest_year = electricity_total["year"].max()
print(f"Latest year with data: {latest_year}\n")

latest = electricity_total[electricity_total["year"] == latest_year]
print(
    latest.groupby("country_or_area")["quantity"]
    .sum()
    .sort_values(ascending=False)
)

print("\n" + "=" * 70)
print("2) ELECTRICITY PRODUCTION OVER TIME — full trend by country")
print("=" * 70)
trend = (
    electricity_total.groupby(["country_or_area", "year"])["quantity"]
    .sum()
    .reset_index()
    .pivot(index="year", columns="country_or_area", values="quantity")
)
print(trend.tail(10))  # last 10 years of data

print("\n" + "=" * 70)
print("3) RENEWABLE SHARE — Solar + Wind + Hydro vs total electricity (by source)")
print("=" * 70)
by_source = df[
    (df["commodity_group"] == "Electricity (By Source)")
    & (df["metric_type"] == "Sub-breakdown")
].copy()

RENEWABLE_KEYWORDS = ["hydro", "solar", "wind", "geothermal"]
by_source["is_renewable"] = by_source["commodity"].str.lower().apply(
    lambda x: any(k in x for k in RENEWABLE_KEYWORDS)
)

latest_source_year = by_source["year"].max()
latest_sources = by_source[by_source["year"] == latest_source_year]

summary = (
    latest_sources.groupby(["country_or_area", "is_renewable"])["quantity"]
    .sum()
    .unstack(fill_value=0)
)
summary["renewable_share_%"] = (
    summary.get(True, 0) / (summary.get(True, 0) + summary.get(False, 0)) * 100
).round(1)

print(f"Latest year with source breakdown: {latest_source_year}\n")
print(summary[["renewable_share_%"]].sort_values("renewable_share_%", ascending=False))

print("\n" + "=" * 70)
print("4) DATA COVERAGE CHECK — years available per country (Electricity Total)")
print("=" * 70)
coverage = electricity_total.groupby("country_or_area")["year"].agg(["min", "max", "count"])
print(coverage)

print("\n" + "=" * 70)
print("5) UNITS CHECK — make sure everything you're comparing uses the same unit")
print("=" * 70)
print(electricity_total.groupby("country_or_area")["unit"].unique())

print("\n" + "=" * 70)
print("DONE — eyeball the sections above before building dashboards")
print("Things to look for:")
print("- Does any country have way less data (short date range)? -> footnote it")
print("- Are units consistent across countries for the same commodity_group?")
print("- Does the renewable share story actually show a meaningful contrast?")
print("=" * 70)
