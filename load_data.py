#!/usr/bin/env python3


from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from pandas import DataFrame
from src.db import *


def read_csv(csv_path: Path = CSV_PATH):
    """
    read and validate the csv
    """

    if not csv_path.exists():
        raise FileExistsError(f"Input file path {csv_path} is not exist")

    df: DataFrame = pd.read_csv(csv_path)

    missing_col = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing_col:
        raise ValueError(f"The input file missing required columns: {missing_col}")

    for col in (
        "project",
        "subject",
        "sample",
        "condition",
        "treatment",
        "sample_type",
        "response",
        "sex",
    ):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    for col in ("condition", "treatment", "sample_type", "response"):
        if col in df.columns:
            df[col] = df[col].str.lower()

    if "sex" in df.columns:
        df["sex"] = df["sex"].str.upper().str[0]  # keep only M/F

    for col in ("age", "time_from_treatment_start"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for pop in CELL_POPULATIONS:
        df[pop] = pd.to_numeric(df[pop], errors="coerce").astype("Int64")

    return df


"""
Load to sqlite
"""


def initialize_schema(conn) -> None:
    conn.executescript(SCHEMA_PATH.read_text())


def _lookup_ids(conn, table, key_col, values):
    clean = sorted({v for v in values if pd.notna(v) and str(v).strip() != ""})
    conn.executemany(
        f"INSERT OR IGNORE INTO {table} ({key_col}) VALUES (?)", [(v,) for v in clean]
    )
    return {
        row[key_col]: row["id"]
        for row in conn.execute(f"SELECT rowid AS id, {key_col} FROM {table}")
    }


def _nullable(value):
    """
    Convert pandas NA to None for sqlite3.
    """
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def load(df: pd.DataFrame, conn) -> dict[str, int]:
    """
    Populate table from the normalized dataframe.
    """
    # --- dimensions ------------------------------------------------------
    project_ids = _lookup_ids(
        conn, "projects", "project_code", df.get("project", pd.Series(dtype="string"))
    )
    condition_ids = _lookup_ids(
        conn,
        "conditions",
        "condition_name",
        df.get("condition", pd.Series(dtype="string")),
    )
    treatment_ids = _lookup_ids(
        conn,
        "treatments",
        "treatment_name",
        df.get("treatment", pd.Series(dtype="string")),
    )
    sample_type_ids = _lookup_ids(
        conn,
        "sample_types",
        "sample_type_name",
        df.get("sample_type", pd.Series(dtype="string")),
    )

    conn.executemany(
        "INSERT OR IGNORE INTO cell_populations (population_name, display_name, sort_order) "
        "VALUES (?, ?, ?)",
        [(p, POPULATION_LABELS[p], i) for i, p in enumerate(CELL_POPULATIONS)],
    )
    population_ids = {
        r["population_name"]: r["population_id"]
        for r in conn.execute(
            "SELECT population_id, population_name FROM cell_populations"
        )
    }

    # --- subjects --------------------------------------------------------
    subject_cols = [
        c for c in ("subject", "project", "condition", "age", "sex") if c in df.columns
    ]
    subjects = df[subject_cols].drop_duplicates(subset=["subject"])

    conn.executemany(
        "INSERT OR IGNORE INTO subjects "
        "(subject_code, project_id, condition_id, age, sex) VALUES (?, ?, ?, ?, ?)",
        [
            (
                row["subject"],
                project_ids.get(row.get("project")),
                condition_ids.get(row.get("condition")),
                _nullable(row.get("age")),
                _nullable(row.get("sex")),
            )
            for _, row in subjects.iterrows()
        ],
    )
    subject_ids = {
        r["subject_code"]: r["subject_id"]
        for r in conn.execute("SELECT subject_id, subject_code FROM subjects")
    }

    # --- samples ---------------------------------------------------------
    conn.executemany(
        "INSERT OR IGNORE INTO samples "
        "(sample_code, subject_id, treatment_id, sample_type_id, response, "
        " time_from_treatment_start) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                row["sample"],
                subject_ids[row["subject"]],
                treatment_ids.get(row.get("treatment")),
                sample_type_ids.get(row.get("sample_type")),
                _nullable(row.get("response")),
                _nullable(row.get("time_from_treatment_start")),
            )
            for _, row in df.iterrows()
        ],
    )
    sample_ids = {
        r["sample_code"]: r["sample_id"]
        for r in conn.execute("SELECT sample_id, sample_code FROM samples")
    }

    # --- measurements (long format) --------------------------------------
    count_rows = []
    for _, row in df.iterrows():
        sid = sample_ids[row["sample"]]
        for pop in CELL_POPULATIONS:
            value = _nullable(row[pop])
            if value is not None:
                count_rows.append((sid, population_ids[pop], int(value)))

    conn.executemany(
        "INSERT OR REPLACE INTO cell_counts (sample_id, population_id, count) "
        "VALUES (?, ?, ?)",
        count_rows,
    )

    return {
        "projects": len(project_ids), # type: ignore
        "subjects": len(subject_ids),
        "samples": len(sample_ids),
        "measurements": len(count_rows),
    }


def main() -> int:
    print(f"Reading {CSV_PATH.relative_to(CSV_PATH.parent.parent)} ...")
    df = read_csv()
    print(f"  {len(df)} row(s), {len(df.columns)} column(s)")

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database {DB_PATH.name}")

    with connect() as conn:
        initialize_schema(conn)
        print(f"Initialized schema in {DB_PATH.name}")
        stats = load(df, conn)
        conn.commit()

    print("Loaded:")
    for key, value in stats.items():
        print(f"  {value:>6}  {key}")
    print(f"\nDatabase written to {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
