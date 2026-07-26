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

REQUIRED_COLUMNS = ["project", "subject", "sample"] + CELL_POPULATIONS

OPTIONAL_COLUMNS = [
    "condition",
    "age",
    "sex",
    "treatment",
    "response",
    "sample_type",
    "time_from_treatment_start",
]

def connect(db_path: Path | str = DB_PATH):
	_conn = sqlite3.Connection(
		database=str(object=db_path)
	)

	_conn.execute("PRAGMA foreign_keys=ON;")
	_conn.row_factory = sqlite3.Row

	return _conn

def query(sql_q: str, params: tuple | dict = (), db_path: Path | str = DB_PATH) -> pd.DataFrame:
    """
    Run a query and return the result as a DataFrame.
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(sql_q, conn, params=params)


def ensure_output_dirs() -> None:
    """
    Create the outputs if it does not already exist.
    """
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def require_database(db_path: Path | str = DB_PATH) -> None:
    if not Path(db_path).exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}.\n"
            "Run `python load_data.py` (or `make pipeline`) first."
        )