-- Operation Get Employed — Portfolio Project 1
-- SQL practice queries against energy_stats (loaded via load_to_sqlite.py)
--
-- Run interactively with: sqlite3 energy.db
-- Then paste queries one at a time, or run the whole file with:
--   sqlite3 energy.db < queries.sql
--
-- These queries reproduce the same findings the Python exploration
-- script showed you — but now you're writing the SQL yourself.
-- Try to read and understand each one before running it, then tweak
-- the filters (different countries, years, commodities) to practice.

-- ============================================================
-- 1) ELECTRICITY PRODUCTION — latest year (2014), ranked
-- ============================================================
SELECT
    country_or_area,
    SUM(quantity) AS total_production_gwh
FROM energy_stats
WHERE commodity_group = 'Electricity (Total)'
  AND metric_type = 'Production'
  AND year = 2014
GROUP BY country_or_area
ORDER BY total_production_gwh DESC;


-- ============================================================
-- 2) ELECTRICITY PRODUCTION TREND — all years, all countries
--    (This is the long version of the pivot table from Python —
--     SQL doesn't pivot natively, so you'll get one row per
--     country/year instead of a wide table. That's normal.)
-- ============================================================
SELECT
    country_or_area,
    year,
    SUM(quantity) AS total_production_gwh
FROM energy_stats
WHERE commodity_group = 'Electricity (Total)'
  AND metric_type = 'Production'
GROUP BY country_or_area, year
ORDER BY country_or_area, year;


-- ============================================================
-- 3) GROWTH RATE 2005 -> 2014 per country
--    Uses a self-join: one copy of the table for 2005, one for 2014.
-- ============================================================
SELECT
    a.country_or_area,
    a.quantity AS production_2005,
    b.quantity AS production_2014,
    ROUND(((b.quantity - a.quantity) / a.quantity) * 100, 1) AS growth_pct
FROM
    (SELECT country_or_area, quantity
     FROM energy_stats
     WHERE commodity_group = 'Electricity (Total)'
       AND metric_type = 'Production'
       AND year = 2005) a
JOIN
    (SELECT country_or_area, quantity
     FROM energy_stats
     WHERE commodity_group = 'Electricity (Total)'
       AND metric_type = 'Production'
       AND year = 2014) b
ON a.country_or_area = b.country_or_area
ORDER BY growth_pct DESC;


-- ============================================================
-- 4) RENEWABLE SHARE — 2014, by country
--    Uses CASE WHEN to classify renewable vs non-renewable sources,
--    then divides renewable sum by total sum.
-- ============================================================
SELECT
    country_or_area,
    SUM(CASE
            WHEN LOWER(commodity) LIKE '%hydro%'
              OR LOWER(commodity) LIKE '%solar%'
              OR LOWER(commodity) LIKE '%wind%'
              OR LOWER(commodity) LIKE '%geothermal%'
            THEN quantity ELSE 0
        END) AS renewable_qty,
    SUM(quantity) AS total_qty,
    ROUND(
        SUM(CASE
                WHEN LOWER(commodity) LIKE '%hydro%'
                  OR LOWER(commodity) LIKE '%solar%'
                  OR LOWER(commodity) LIKE '%wind%'
                  OR LOWER(commodity) LIKE '%geothermal%'
                THEN quantity ELSE 0
            END) * 100.0 / SUM(quantity),
        1
    ) AS renewable_share_pct
FROM energy_stats
WHERE commodity_group = 'Electricity (By Source)'
  AND metric_type = 'Sub-breakdown'
  AND year = 2014
GROUP BY country_or_area
ORDER BY renewable_share_pct DESC;


-- ============================================================
-- 5) DATA COVERAGE CHECK — min/max year and row count per country
-- ============================================================
SELECT
    country_or_area,
    MIN(year) AS first_year,
    MAX(year) AS last_year,
    COUNT(*) AS row_count
FROM energy_stats
WHERE commodity_group = 'Electricity (Total)'
  AND metric_type = 'Production'
GROUP BY country_or_area;


-- ============================================================
-- 6) PRACTICE: window function example
--    Year-over-year change in Nigeria's electricity production
--    using LAG() to grab the previous year's value.
-- ============================================================
SELECT
    year,
    quantity AS production_gwh,
    LAG(quantity) OVER (ORDER BY year) AS prev_year_production,
    ROUND(
        (quantity - LAG(quantity) OVER (ORDER BY year)) * 100.0
        / LAG(quantity) OVER (ORDER BY year),
        1
    ) AS yoy_change_pct
FROM energy_stats
WHERE country_or_area = 'Nigeria'
  AND commodity_group = 'Electricity (Total)'
  AND metric_type = 'Production'
ORDER BY year;
