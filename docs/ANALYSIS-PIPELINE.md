# Analysis Pipeline

## Script Order

1. `create_canonical_map.py`
2. `audit_amf_events_in_windows.py`
3. `extract_unified_results_and_nf_pressure.py`
4. `summarize_nf_pressure_for_paper.py`
5. `extract_dasaco_scaling_recovery.py`
6. `reconcile_supi_outcomes.py`
7. `aggregate_nf_cost.py`
8. `classify_exclusive_failures.py`
9. `windowed_latency.py`

## Rules

- Use only the 25 canonical runs selected by the manifests.
- Treat the run as the independent statistical unit.
- Calculate per-pod pressure separately from aggregate NF cost.
- Use Hyndman and Fan Type 7 for P95 and P99.
- Assign each failed SUPI to at most one exclusive failure category.
- Preserve source experiment evidence in read-only mode.

## Latency Definition

Latency equals `Handle Registration Complete` minus `Handle InitialRegistration` for the same SUPI inside the canonical workload window.

This is post-security registration-completion latency, not end-to-end registration latency.

## Statistical Methods

- Kruskal-Wallis overall test
- Exact two-sided Mann-Whitney U comparisons
- Holm multiple-comparison correction
- Cliff's delta effect size
- Five run-level observations per method
