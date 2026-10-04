# Nigeria's Electricity Growth in Context (1990-2014)

I compared Nigeria's electricity production and renewable energy adoption against five other African economies (South Africa, Egypt, Ghana, Kenya, and Morocco), using 25 years of UN energy statistics. I wanted to see how Nigeria's power sector actually stacks up against its regional peers, not just assume it.

## Summary

Nigeria's electricity production grew more slowly than most of its peers between 2005 and 2014, and its renewable energy mix is still underdeveloped compared to hydro-heavy countries like Kenya and Ghana. This project walks through how I cleaned and analyzed the data, and what I found.

## Key findings

**Scale.** In 2014, Nigeria produced about 234,000 GWh of electricity. That puts it in the middle of the pack: well behind South Africa (roughly 2.0M GWh) and Egypt (roughly 1.3M GWh), but ahead of Ghana (about 97,000 GWh) and Kenya (about 75,000 GWh).

**Growth from 2005 to 2014.** Nigeria's production grew by 32.4% over the decade. That's slower than Ghana (82.1%), Morocco (70.3%), Kenya (60.2%), and Egypt (58.0%). Only South Africa grew slower, at 3.4%, but South Africa was already close to its production ceiling as the region's dominant producer, so that's not really a fair comparison.

**Volatility.** Nigeria's year-over-year growth isn't steady. There were real declines in 2008 (down 7.8%) and 2009 (down 5.5%), around the same time as the global financial crisis and well-documented domestic power sector problems, followed by a sharp jump in 2010 (up 27.7%).

**Renewable share in 2014.** Renewables (hydro, solar, wind, and geothermal combined) made up only 17.6% of Nigeria's electricity mix. Kenya and Ghana, both heavily reliant on hydro, sit at 71.6% and 63.8%. Nigeria is still ahead of Morocco (14.7%), Egypt (8.8%), and South Africa (4.1%, which runs mostly on coal).

## Data source

[UN International Energy Statistics](https://www.kaggle.com/datasets/unitednations/international-energy-statistics) on Kaggle, originally sourced from the UN Statistics Division's Energy Statistics Database.

## Methodology

I started by filtering the raw dataset (about 1.2 million rows) down to the six countries I cared about and the relevant commodities. The raw data had inconsistent naming for some commodities (typos, inconsistent capitalization), so I fixed those, and split the combined `commodity_transaction` field into two separate columns: `commodity` and `transaction`.

Each row also got tagged with a `metric_type`: Production, Capacity, Reserves, or Sub-breakdown. This mattered more than I expected going in. The raw data mixes energy-flow numbers (kilowatt-hours, which measure actual production) with power-capacity numbers (kilowatts, which measure how much a plant *could* produce) under the exact same commodity name. Without separating these, totals would silently blend two different kinds of measurement into one meaningless number.

For the SQL side, I loaded the cleaned data into a database and wrote queries using `GROUP BY`/`SUM` aggregation, a self-join to compare growth between 2005 and 2014, `CASE WHEN` logic to classify renewable sources, and a `LAG()` window function to look at year-over-year changes. I cross-checked every one of these against the same calculations done in Python, to make sure the numbers actually matched.

The dashboard itself was built in Power BI: a trend line showing production over time, a bar chart ranking countries in 2014, a renewable share comparison, and a chart isolating Nigeria's year-over-year swings.

## Process and challenges

This section exists because the bugs I hit while building this taught me more than the clean final numbers did, and I think they're worth writing down.

**Splitting a combined field.** The raw data stores a commodity and its transaction type together in one string, like "Electricity - Gross production." I split this into two columns using a simple string split on " - " in pandas.

**Typos and inconsistent naming in the raw data.** I found "Hrad coal" where it should have said "Hard coal," and "Natural Gas" spelled with a different capitalization than "Natural gas" elsewhere in the same column. Left alone, these would have quietly split what should be one category into two, undercounting totals without throwing any error. I built a small lookup table to normalize these before doing any analysis.

**A duplicate column bug.** At one point I renamed a cleaned column (`commodity_clean`) to `commodity`, but forgot I still had the original `commodity` column sitting in the dataframe. That left two columns with the same name, which crashed `sort_values()` with a "column label is not unique" error. The fix was simple once I found it: drop the old column before renaming the new one.

**The bug that actually mattered: mixed units hiding under one name.** This was the trickiest one. The "Electricity" commodity in the raw data contains both production rows, measured in kilowatt-hours, and capacity rows, measured in kilowatts, both labeled identically as "Electricity." My first attempt at classifying rows only checked the commodity's name for the word "capacity," which missed this case completely. The production totals I was calculating were silently adding energy and power together, numbers that look fine on the surface but don't actually mean anything. I fixed it by checking the unit text itself (looking for "hour" in the unit) instead of relying on the name alone.

**A cross-product bug in my SQL growth query.** My first version of the year-over-year growth calculation joined a 2005 subquery to a 2014 subquery without aggregating either one down to a single row per country first. Since several transaction types share the same commodity and year, that join multiplied rows against each other instead of matching them cleanly, producing growth rates in the thousands of percent. I fixed it by adding `GROUP BY` and `SUM()` inside each subquery before the join happened.

**The same bug came back in a different query.** When I applied a `LAG()` window function to look at Nigeria's year-over-year changes, I ran into the same root problem: raw, unaggregated rows meant the query was stepping through roughly sixteen rows per year instead of one. Same fix as before: aggregate to one row per year first, then apply `LAG()` on top of that.

**Small tooling friction.** The `sqlite3` command-line tool isn't included with a typical Windows Python install, which I didn't realize until I tried to run my queries and got a "command not recognized" error. I switched to DB Browser for SQLite instead, a free GUI tool, which ended up being easier to work with anyway while I was debugging the issues above.

**Checking my own work.** I reproduced every key number in this project twice: once in Python and once in SQL. That's partly good practice, but it's also specifically how I caught the unit-mixing bug and the cross-product bug before they reached the dashboard.

## Tools used

Python (pandas) for data cleaning and exploratory analysis. SQL (SQLite) for aggregation, self-joins, conditional logic, and window functions. Power BI for the dashboard.

## Files

| File | Description |
|---|---|
| `clean_energy_data.py` | Cleans and classifies the raw dataset |
| `explore_energy_data.py` | Exploratory analysis and sanity checks |
| `energy_clean.csv` | Cleaned, analysis-ready dataset |
| `load_to_sqlite.py` | Loads the cleaned data into SQLite |
| `queries.sql` | SQL analysis queries (SQLite syntax) |
| `energy_powerbi.pbix` | Power BI dashboard |
| `Dashboard_screenshot.pdf` | Dashboard preview, no Power BI install needed to view it |

Not included in this repo: the raw `all_energy_statistics.csv` (too large; [download it from Kaggle](https://www.kaggle.com/datasets/unitednations/international-energy-statistics) if you want to reproduce this) and `energy.db` (regenerated locally by `load_to_sqlite.py`).

## Reproducing this analysis

```
pip install pandas
python clean_energy_data.py
python explore_energy_data.py
python load_to_sqlite.py
```

Then open `energy.db` in a SQLite client and run `queries.sql`, or import `energy_clean.csv` directly into Power BI.

## Caveats

Data coverage runs from 1990 to 2014 for all six countries, so this doesn't reflect anything more recent. Renewable share is calculated only from rows that break electricity down by source (hydro, solar, wind, geothermal, and non-renewable sources individually), so it leaves out any source the original dataset didn't itemize separately. These figures come straight from UN-reported statistics and I haven't cross-checked them against national energy ministry data.
