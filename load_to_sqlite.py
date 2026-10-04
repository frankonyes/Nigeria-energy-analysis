"""
Operation Get Employed — Portfolio Project 1
Loads energy_clean.csv into a local SQLite database so you can practice
SQL against real data instead of toy exercises.

pip install pandas (if not already installed)
sqlite3 is built into Python — no extra install needed.
"""

import sqlite3
import pandas as pd

CSV_FILE = "energy_clean.csv"
DB_FILE = "energy.db"
TABLE_NAME = "energy_stats"

df = pd.read_csv(CSV_FILE)

conn = sqlite3.connect(DB_FILE)
df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

print(f"Loaded {len(df)} rows into {DB_FILE} -> table '{TABLE_NAME}'")

# Quick sanity check
cur = conn.cursor()
cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
print("Row count in DB:", cur.fetchone()[0])

cur.execute(f"PRAGMA table_info({TABLE_NAME})")
print("\nColumns:")
for col in cur.fetchall():
    print(" -", col[1], f"({col[2]})")

conn.close()
print(f"\nDone. Open {DB_FILE} with any SQLite client (e.g. DB Browser for SQLite),")
print("or run queries.sql against it using: sqlite3 energy.db < queries.sql")
