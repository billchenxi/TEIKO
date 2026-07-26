from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

# --------- Paths
ROOT_DIR = Path(__file__).resolve().parent.parent # proj path
DB_PATH = ROOT_DIR / "cell_counts.db"
SCHEMA_PATH = ROOT_DIR / "src" / "schema.sql"
DATA_DIR = ROOT_DIR / "data"
CSV_PATH = DATA_DIR / "cell-count.csv"
OUTPUT_DIR = ROOT_DIR / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"

CELL_POPULATIONS = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]

POPULATION_LABELS = {
    "b_cell": "B cell",
    "cd8_t_cell": "CD8 T cell",
    "cd4_t_cell": "CD4 T cell",
    "nk_cell": "NK cell",
    "monocyte": "Monocyte",
}

