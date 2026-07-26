from __future__ import annotations
from src.db import *


BASELINE_SQL = """
WITH baseline AS (
	SELECT
		sm.sample_code AS sample,
		su.subject_code AS subject,
		pr.project_code AS project,
		sm.response,
		su.sex
	FROM samples sm
	JOIN subjects su ON su.subject_id=sm.subject_id
	JOIN conditions cond on cond.condition_id = su.condition_id
	JOIN treatments tr ON tr.treatment_id = sm.treatment_id
	JOIN sample_types st ON st.sample_type_id = sm.sample_type_id
	JOIN projects pr ON pr.project_id = su.project_id
	WHERE cond.condition_name = :condition
		AND st.sample_type_name = :sample_type
		AND tr.treatment_name = :treatment
		AND sm.time_from_treatment_start = :baseline
	ORDER BY pr.project_code, su.subject_code
)

"""


_PARAMS = {
	"condition": "melanoma",
	"treatment": "miraclib",
	"sample_type": "pbmc",
	"baseline": 0,
}

def baseline_cohort(condition="melanoma", treatment="miraclib",sample_type="pbmc", baseline=0):
	return query(
		BASELINE_SQL + """
			SELECT * FROM baseline
		""",
		params=_PARAMS,
	)

def samples_per_project():
	return query(
		BASELINE_SQL + "SELECT project AS project, COUNT(*) AS n_samples FROM baseline GROUP BY project ORDER BY project",
		params=_PARAMS,
	)


def subjects_by_response():
	return query(
		BASELINE_SQL + "SELECT response, COUNT(DISTINCT subject) AS n_subjects FROM baseline GROUP BY response ORDER BY response",
		params=_PARAMS,
	)


def subjects_by_sex():
	return query(
		BASELINE_SQL + "SELECT sex, COUNT(DISTINCT subject) AS n_subjects FROM baseline GROUP BY sex ORDER BY sex",
		params=_PARAMS,
	)


def main():
	cohort = baseline_cohort()
	print(f"Baseline subset: {len(cohort)} samples\n")

	for title, table in [
		("Samples per project",  samples_per_project()),
		("Subjects by response", subjects_by_response()),
		("Subjects by sex",      subjects_by_sex()),
	]:
		print(title)
		print(table.to_string(index=False))
		print()
	return 0
	

if __name__ == "__main__":
	raise SystemExit(main())
