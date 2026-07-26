# Immune Cell Count Analysis

**Live dashboard:** https://n7iytjbqhd7s8dg8yvadwl.streamlit.app/

## Quick start
```bash
make setup       # install dependencies (pip install -r requirements.txt)
make pipeline    # run Parts 1–4 end to end, regenerating the DB and all outputs
make dashboard   # launch the dashboard locally at http://localhost:8501
```

Requires Python 3.11+.

## Run steps individually

```bash
python load_data.py     # Part 1: build cell_counts.db from data/cell-count.csv
python -m src.analysis  # Part 2: per-sample population frequency table
python -m src.stats     # Part 3: responder vs non-responder stats + boxplot
python -m src.subsets   # Part 4: baseline subset breakdowns
```

Tables are written to `outputs/tables/`, figures to `outputs/figures/`.

## Project structure

```
load_data.py        # Part 1 entry point (root, no args) — creates cell_counts.db
app.py              # Streamlit dashboard (Parts 2–4)
Makefile            # setup / pipeline / dashboard targets
requirements.txt
src/
  db.py             # paths, connection, query() helper, output-dir helpers
  schema.sql        # SQLite schema (tables + view)
  analysis.py       # Part 2: population frequency summary
  stats.py          # Part 3: Mann–Whitney U + BH correction, boxplot
  subsets.py        # Part 4: baseline subset queries
data/cell-count.csv # input data
cell_counts.db      # generated database (committed so the dashboard runs)
outputs/            # generated tables and figures
```

## Database schema
- **Lookup tables** — `projects`, `conditions`, `treatments`, `sample_types`,
  `cell_populations`. Each categorical value stored once, referenced by id.
- **Entities** — `subjects` (subject-level: project, condition, age, sex) and
  `samples` (sample-level: treatment, sample_type, response,
  time_from_treatment_start). Splitting them avoids repeating a subject's
  attributes on every one of their samples.
- **Fact table** — `cell_counts (sample_id, population_id, count)` in **long
  format**: one row per sample × population. `view_sample_total` sums counts
  per sample for reuse.

**Why this design**
- Normalization removes duplicated strings and enforces referential integrity
  via foreign keys (`PRAGMA foreign_keys=ON`).
- Long-format counts mean adding a sixth cell population is a *row*, not a
  schema change, and make percentage / GROUP BY analytics clean and tidy.
- The subject/sample split matches the biology (many samples per subject over time).

**How it scales** (hundreds of projects, thousands of samples)
- **Indexes on the foreign-key columns** (`cell_counts.population_id`,
  `samples.subject_id`, `samples.treatment_id`, …) keep joins on the long fact
  table fast — these are in the schema and confirmed used by the query planner
  (`SEARCH ... USING INDEX`).
- **Common rollups are wrapped in views** — e.g. `view_sample_total` for
  per-sample totals; on a larger engine, hot ones can be promoted to
  materialized views.
- The same schema **ports directly to Postgres**; `cell_counts` can be
  partitioned by project or time window if it grows large. The model's shape
  doesn't change.