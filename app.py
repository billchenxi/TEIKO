import matplotlib

matplotlib.use("Agg")  # MUST precede importing src.stats (it imports pyplot)

import streamlit as st
from src.db import require_database
from src.analysis import population_freq
from src.stats import cohort_freq, compare_populations, plot_response_boxplot
from src.subsets import (
    baseline_cohort,
    samples_per_project,
    subjects_by_response,
    subjects_by_sex,
)

st.set_page_config(page_title="Loblaw Bio — Cell Counts", layout="wide")

# Friendly error if the DB hasn't been built yet (instead of a raw traceback)
try:
    require_database()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

st.title("Loblaw Bio — Immune Cell Analysis")

# ---- Part 2 ----------------------------------------------------------
st.header("Part 2: Population frequencies")
st.caption("Relative frequency of each population within each sample.")
st.dataframe(population_freq(), use_container_width=True, height=300)

# ---- Part 3 ----------------------------------------------------------
st.header("Part 3: Responders vs non-responders (melanoma: miraclib: PBMC)")
cohort = cohort_freq()
stats = compare_populations(cohort)

fig, _ = plot_response_boxplot(
    cohort, save=False
)  # save=False: don't rewrite the PNG each load
st.pyplot(fig)

st.subheader("Significance — Mann–Whitney U + BH correction")
st.dataframe(stats, use_container_width=True)
sig = list(stats.loc[stats.significant, "population"])
if sig:
    st.success(f"Significant after correction: {', '.join(sig)}")
else:
    st.info(
        "No population significant at FDR < 0.05 after BH correction "
        "(CD4 T cells strongest, uncorrected p ≈ 0.013)."
    )

# ---- Part 4 ----------------------------------------------------------
st.header("Part 4: Baseline subset (melanoma: miraclib PBMC: time 0)")
st.metric("Baseline samples", len(baseline_cohort()))
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Samples / project")
    st.dataframe(samples_per_project(), use_container_width=True)
with c2:
    st.subheader("Subjects / response")
    st.dataframe(subjects_by_response(), use_container_width=True)
with c3:
    st.subheader("Subjects / sex")
    st.dataframe(subjects_by_sex(), use_container_width=True)
