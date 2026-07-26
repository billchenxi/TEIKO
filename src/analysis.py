from __future__ import annotations
from matplotlib import artist
import pandas as pd
from src.db import *

import argparse

POPULATION_FREQ_SQL = """
SELECT 
	s.sample_code AS sample,
	t.total_count,
	p.population_name AS population,
	cc.count,
	ROUND(100.0 * cc.count / t.total_count, 2) AS percentage
FROM cell_counts AS cc
JOIN samples s ON s.sample_id=cc.sample_id
JOIN cell_populations p ON p.population_id=cc.population_id
JOIN view_sample_total t ON t.sample_id=cc.sample_id
ORDER BY 1, p.sort_order
"""

def population_freq():
	return query(POPULATION_FREQ_SQL)

def main(io_print = False):
    df = population_freq()
    if io_print:
        print(df.to_string(index=False))

    ensure_output_dirs()
    out = TABLE_DIR / "population_freq.csv"
    df.to_csv(out, index=False)
    print(f"\n\n{df.shape[0]} rows >>> {out}")
    return 0


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute per-sample cell population frequencies."
    )
    parser.add_argument(
        "--print",
        dest="io_print",
        action="store_true",  # default stays False; passing the flag makes it True
        help="Print the table to stdout.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(main(io_print=args.io_print))
