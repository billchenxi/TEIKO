#!/usr/bin/env python3


from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from pandas import DataFrame
from src.db import *

def read_csv(csv_path:Path = CSV_PATH):
	"""
	read and validate the csv
	"""

	if not csv_path.exists():
		raise FileExistsError(
			f"Input file path {csv_path} is not exist"
		)

	df: DataFrame = pd.read_csv(csv_path)

	missing_col = [c for c in REQUIRED_COLUMNS if c not in df.columns]

	if missing_col:
		raise ValueError(f"The input file missing required columns: {missing_col}")

	for col in ("project", "subject", "sample", "condition", "treatment",
				"sample_type", "response", "sex"):
		if col in df.columns:
			df[col] = df[col].astype("string").str.strip()

	for col in ("condition", "treatment", "sample_type", "response"):
		if col in df.columns:
			df[col] = df[col].str.lower()

	if "sex" in df.columns:
		df["sex"] = df["sex"].str.upper().str[0] # keep only M/F

	for col in ("age", "time_from_treatment_start"):
		if col in df.columns:
			df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

	for pop in CELL_POPULATIONS:
		df[pop] = pd.to_numeric(df[pop], errors="coerce").astype("Int64")

	return df


