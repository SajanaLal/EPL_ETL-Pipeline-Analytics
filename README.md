# EPL ETL Pipeline & Analytics (Python · SQL Server · Power BI)

Raw Premier League data turned into a reliable warehouse and dashboard: API-Football → Python extraction → SQL Server staging → star-schema warehouse → Power BI.

## Dashboard

### Season Overview

![Season Overview dashboard](Season%20Overview.png)

### Team Performance

![Team Performance dashboard](Performance%20Analysis.png)

### Match Analysis

![Match Analysis dashboard](Match%20Analysis.png)


## Pipeline

`main.py` runs six logged steps:

1. **Extract** (`src/extract.py`): teams, fixtures and standings from API-Football (league 39, season 2024), with retry logic and raw JSON snapshots saved per run
2. **Transform** (`src/transform.py`): nested JSON flattened into clean Pandas dataframes
3. **Validate** (`src/validate.py`): the pipeline stops if a required check fails — null IDs, unknown team references, duplicate standings, and football logic checks (points = wins×3 + draws, goal difference = goals for − against, played = W+D+L)
4. **Stage** (`src/load_staging.py`): full-refresh load into `stg` schema with row-count verification (20 teams, 380 fixtures, 20 standings)
5. **Load warehouse** (`src/load_warehouse.py` + `sql/WarehouseLoad.sql`): upsert into a `dw` star schema — DimTeam, DimDate, FactFixture, FactStandings
6. **Audit** (`src/audit.py`): SQL audits on the finished warehouse — zero duplicate team IDs, fixture IDs or standings positions, no orphaned facts, row counts reconciled

## Reporting

SQL views (`sql/`) for team match performance, match analysis and standings analysis feed a Power BI dashboard (`Final_EPL_Dashboard.pbix`) on team performance and match outcomes.

## Structure

```
main.py                  # pipeline orchestrator with file + console logging
src/
  extract.py             # API pulls with retries, raw JSON snapshots
  transform.py           # JSON to clean dataframes
  validate.py            # fail-fast data quality checks
  load_staging.py        # staging refresh with verification
  load_warehouse.py      # dimensional upserts
  audit.py               # post-load warehouse audits
  config.py              # paths, API and SQL Server config (.env driven)
sql/                     # DDL, warehouse load and reporting views
EPL_ETL_PipelineDocumentation.ipynb   # walkthrough notebook
Final_EPL_Dashboard.pbix              # Power BI report
```

## Setup

1. `pip install requests pandas pyodbc python-dotenv`
2. Create a `.env` with `APISPORTS_API_KEY`, `EPL_SQL_SERVER`, `EPL_SQL_DATABASE`
3. Run `sql/DB_Creation.sql`, then `python main.py`

## Tools

Python (Requests, Pandas, pyodbc), SQL Server (staging, star schema, views), Power BI

## What it demonstrates

The full ETL flow from a live API to a validated dimensional model, with the habits that matter in real data work: fail-fast validation, idempotent loads, and auditing the warehouse before trusting the dashboard.
