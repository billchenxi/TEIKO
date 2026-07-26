from __future__ import annotations
import numpy as np
import pandas as pd
from src.db import *

from scipy.stats import false_discovery_control, mannwhitneyu

import matplotlib.pyplot as plt


COHORT_FREQ_SQL = """
SELECT
	sm.sample_code AS sample,
	sm.response AS response,
	p.population_name AS population,
	cc.count,
	vt.total_count,
	(100.0 * cc.count / vt.total_count) AS percentage
FROM cell_counts cc
JOIN samples sm ON sm.sample_id = cc.sample_id
JOIN subjects su ON su.subject_id = sm.subject_id
JOIN conditions cond on cond.condition_id=su.condition_id
JOIN treatments tr ON tr.treatment_id=sm.treatment_id
JOIN sample_types st on st.sample_type_id = sm.sample_type_id
JOIN cell_populations p on p.population_id=cc.population_id
JOIN view_sample_total vt on vt.sample_id = cc.sample_id
WHERE cond.condition_name = :condition
	AND tr.treatment_name = :treatment
	AND st.sample_type_name = :sample_type
	AND sm.response IN ('yes', 'no')
ORDER BY p.sort_order, sm.response, sm.sample_code
"""

def cohort_freq(condition="melanoma", treatment="miraclib", sample_type="pbmc"):
	return query(
		COHORT_FREQ_SQL,
		params={
			"condition": condition,
			"treatment": treatment,
			"sample_type": sample_type,
		},
	)


def _benjamini_hochberg(pvals):
	"""
	Return BH-adjusted p-values (FDR control across the 5 tests).
	
	https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html#r4c2dbc17006a-1
	
	When run each test, there's \alpha=0.05 chance of a false positive, so run 5 tests,
	there will be 1-(0.95)^5~0.23 false positibe. Using the BH correction.
	"""

	return false_discovery_control(pvals, method="bh")


def compare_populations(df=None, alpha=0.05):
	"""
	Mann–Whitney U per population, responders (yes) vs non-responders (no).
	- Since the relative frequence is bounded percentage, might not follow Normal Dist
	- MW is non-parametric, it commonly used for comparing ranks and distributuion, not assume Normal dist
	- set a = 0.05
	"""
	
	if df is None:
		df = cohort_freq()

	rows = []
	for pop, sub in df.groupby("population", sort=False):  # sort=False keeps sort_order
		resp = sub.loc[sub.response == "yes", "percentage"]
		nonr = sub.loc[sub.response == "no", "percentage"]
		u, p = mannwhitneyu(resp, nonr, alternative="two-sided") # ----MWU
		rows.append(
			{
				"population": pop,
				"n_resp": len(resp),
				"n_nonresp": len(nonr),
				"median_resp": round(resp.median(), 2),
				"median_nonresp": round(nonr.median(), 2),
				"median_diff": round(resp.median() - nonr.median(), 2),
				"U": u,
				"p_value": p,
			}
		)

	res = pd.DataFrame(rows)
	res["p_adj"] = _benjamini_hochberg(res["p_value"].values)
	res["significant"] = res["p_adj"] < alpha
	return res.sort_values("p_adj").reset_index(drop=True)


# Plot
def plot_response_boxplot(df=None, stats=None, save=True):

    if df is None:
        df = cohort_freq()

    pops = list(dict.fromkeys(df["population"]))
    fig, axes = plt.subplots(1, len(pops), figsize=(14, 4), sharey=True)
    for ax, pop in zip(axes, pops):
        sub = df[df.population == pop]
        data = [
            sub[sub.response == "no"].percentage,
            sub[sub.response == "yes"].percentage,
        ]
        ax.boxplot(data, tick_labels=["non-resp", "resp"])
        ax.set_title(pop)
    axes[0].set_ylabel("Relative frequency (%)")
    fig.tight_layout()

    if save:
        ensure_output_dirs()
        out = FIGURE_DIR / "responder_vs_nonresponder_boxplot.png"
        fig.savefig(out, dpi=150)
        print(f"figure -> {out}")
    return fig, axes


def main(io_print=True):
    df = cohort_freq()
    stats = compare_populations(df)
    if io_print:
        print(stats.to_string(index=False))
    plot_response_boxplot(df, stats=stats)
    ensure_output_dirs()
    stats.to_csv(TABLE_DIR / "responder_stats.csv", index=False)
    print(
        f"\nSignificant: {list(stats.loc[stats.significant, 'population']) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
