import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

output = (
    Path.home()
    / "PREVIOUS-VM-EVIDENCE"
    / "UNIFIED-25-RUN-ANALYSIS"
)

pressure_path = output / "UNIFIED-25-RUN-NF-PRESSURE.csv"
run_path = output / "UNIFIED-25-RUN-RESULTS.csv"
method_path = output / "UNIFIED-5-METHOD-SUMMARY.csv"

nf_summary_path = output / "UNIFIED-5-METHOD-NF-PRESSURE-SUMMARY.csv"
ranking_path = output / "UNIFIED-NF-PRESSURE-RANKING.csv"
markdown_path = output / "PAPER-RESULTS-PRELIMINARY.md"
report_path = output / "NF-PRESSURE-SUMMARY-REPORT.txt"

def numeric(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    return result if math.isfinite(result) else None

def mean(values):
    clean = [
        value for value in values
        if value is not None and math.isfinite(value)
    ]

    if not clean:
        return None

    return statistics.fmean(clean)

def sample_sd(values):
    clean = [
        value for value in values
        if value is not None and math.isfinite(value)
    ]

    if len(clean) < 2:
        return None

    return statistics.stdev(clean)

def formatted(value, digits=3):
    if value is None:
        return ""

    return f"{value:.{digits}f}"

with pressure_path.open(newline="") as stream:
    pressure_rows = list(csv.DictReader(stream))

with run_path.open(newline="") as stream:
    run_rows = list(csv.DictReader(stream))

with method_path.open(newline="") as stream:
    method_rows = list(csv.DictReader(stream))

grouped = defaultdict(list)

for row in pressure_rows:
    key = (
        row["method"],
        row["method_name"],
        row["function"],
    )
    grouped[key].append(row)

summary_rows = []

for key, rows in sorted(grouped.items()):
    method, method_name, function = key

    cpu_mean_runs = [
        numeric(row["cpu_mean_m"])
        for row in rows
    ]
    cpu_p95_runs = [
        numeric(row["cpu_p95_m"])
        for row in rows
    ]
    cpu_p99_runs = [
        numeric(row["cpu_p99_m"])
        for row in rows
    ]
    cpu_max_runs = [
        numeric(row["cpu_max_m"])
        for row in rows
    ]

    memory_mean_runs = [
        numeric(row["memory_mean_mib"])
        for row in rows
    ]
    memory_p95_runs = [
        numeric(row["memory_p95_mib"])
        for row in rows
    ]
    memory_p99_runs = [
        numeric(row["memory_p99_mib"])
        for row in rows
    ]
    memory_max_runs = [
        numeric(row["memory_max_mib"])
        for row in rows
    ]

    summary_rows.append({
        "method": method,
        "method_name": method_name,
        "function": function,
        "runs_observed": len(rows),
        "cpu_mean_m_across_runs": mean(cpu_mean_runs),
        "cpu_mean_m_sample_sd": sample_sd(cpu_mean_runs),
        "cpu_p95_m_mean_across_runs": mean(cpu_p95_runs),
        "cpu_p99_m_mean_across_runs": mean(cpu_p99_runs),
        "cpu_max_m_mean_across_runs": mean(cpu_max_runs),
        "cpu_max_m_overall": max(
            value for value in cpu_max_runs
            if value is not None
        ),
        "memory_mean_mib_across_runs": mean(memory_mean_runs),
        "memory_mean_mib_sample_sd": sample_sd(memory_mean_runs),
        "memory_p95_mib_mean_across_runs": mean(memory_p95_runs),
        "memory_p99_mib_mean_across_runs": mean(memory_p99_runs),
        "memory_max_mib_mean_across_runs": mean(memory_max_runs),
        "memory_max_mib_overall": max(
            value for value in memory_max_runs
            if value is not None
        ),
    })

summary_fields = [
    "method",
    "method_name",
    "function",
    "runs_observed",
    "cpu_mean_m_across_runs",
    "cpu_mean_m_sample_sd",
    "cpu_p95_m_mean_across_runs",
    "cpu_p99_m_mean_across_runs",
    "cpu_max_m_mean_across_runs",
    "cpu_max_m_overall",
    "memory_mean_mib_across_runs",
    "memory_mean_mib_sample_sd",
    "memory_p95_mib_mean_across_runs",
    "memory_p99_mib_mean_across_runs",
    "memory_max_mib_mean_across_runs",
    "memory_max_mib_overall",
]

with nf_summary_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=summary_fields,
    )
    writer.writeheader()
    writer.writerows(summary_rows)

ranking_rows = []

for row in summary_rows:
    ranking_rows.append({
        **row,
        "pressure_score": (
            (row["cpu_p95_m_mean_across_runs"] or 0.0)
            * (row["memory_p95_mib_mean_across_runs"] or 0.0)
        ),
    })

ranking_rows.sort(
    key=lambda row: (
        row["pressure_score"],
        row["cpu_p95_m_mean_across_runs"] or 0.0,
    ),
    reverse=True,
)

ranking_fields = summary_fields + ["pressure_score"]

with ranking_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=ranking_fields,
    )
    writer.writeheader()
    writer.writerows(ranking_rows)

method_order = {
    "B0": 0,
    "B1": 1,
    "B2": 2,
    "B3": 3,
    "R1": 4,
}

method_rows.sort(
    key=lambda row: method_order.get(row["method"], 99)
)

markdown = [
    "# Preliminary Results: Unified 1000-UE Evaluation",
    "",
    "## Experimental Scope",
    "",
    (
        "The evaluation contains five methods with five independent "
        "1000-UE runs per method, producing 25 analyzed runs."
    ),
    "",
    (
        "A successful registration is defined by a unique SUPI with "
        "`Handle Registration Complete` inside the canonical workload "
        "window."
    ),
    "",
    "## Registration Success",
    "",
    "| Method | Runs | Mean completed UEs | Mean success rate | Sample SD | Minimum | Maximum |",
    "|---|---:|---:|---:|---:|---:|---:|",
]

for row in method_rows:
    markdown.append(
        "| "
        + row["method_name"]
        + " | "
        + row["runs"]
        + " | "
        + formatted(numeric(row["completed_mean"]), 1)
        + " | "
        + formatted(
            numeric(row["success_rate_mean_percent"]),
            2,
        )
        + "% | "
        + formatted(
            numeric(row["success_rate_sample_sd"]),
            2,
        )
        + " | "
        + formatted(numeric(row["completed_min"]), 0)
        + " | "
        + formatted(numeric(row["completed_max"]), 0)
        + " |"
    )

markdown.extend([
    "",
    "## Registration Result Interpretation",
    "",
    (
        "Open5GLoS achieved the highest mean raw registration success "
        "rate. DA-SACO ranked second and exceeded Static, AMF-HPA, and "
        "Admission-only in mean completed registrations."
    ),
    "",
    (
        "The run-level dispersion is substantial for several methods. "
        "Consequently, conclusions must consider run variability, "
        "resource pressure, scaling behavior, and recovery behavior "
        "rather than the registration mean alone."
    ),
    "",
    "## Per-Function Resource Pressure",
    "",
    (
        "CPU is reported in millicores and memory in MiB. Run-level "
        "P95 and P99 values use Hyndman and Fan Type 7 interpolation."
    ),
    "",
    "| Method | Function | Runs | CPU mean | CPU P95 | CPU peak | Memory mean | Memory P95 | Memory peak |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|",
])

for row in sorted(
    summary_rows,
    key=lambda item: (
        method_order.get(item["method"], 99),
        item["function"],
    ),
):
    markdown.append(
        "| "
        + row["method_name"]
        + " | "
        + row["function"]
        + " | "
        + str(row["runs_observed"])
        + " | "
        + formatted(row["cpu_mean_m_across_runs"])
        + " | "
        + formatted(row["cpu_p95_m_mean_across_runs"])
        + " | "
        + formatted(row["cpu_max_m_overall"])
        + " | "
        + formatted(row["memory_mean_mib_across_runs"])
        + " | "
        + formatted(row["memory_p95_mib_mean_across_runs"])
        + " | "
        + formatted(row["memory_max_mib_overall"])
        + " |"
    )

markdown.extend([
    "",
    "## Highest Observed Function-Method Pressure Combinations",
    "",
    "| Rank | Method | Function | CPU P95 | CPU overall peak | Memory P95 | Memory overall peak |",
    "|---:|---|---|---:|---:|---:|---:|",
])

for index, row in enumerate(ranking_rows[:20], start=1):
    markdown.append(
        "| "
        + str(index)
        + " | "
        + row["method_name"]
        + " | "
        + row["function"]
        + " | "
        + formatted(row["cpu_p95_m_mean_across_runs"])
        + " | "
        + formatted(row["cpu_max_m_overall"])
        + " | "
        + formatted(row["memory_p95_mib_mean_across_runs"])
        + " | "
        + formatted(row["memory_max_mib_overall"])
        + " |"
    )

markdown.extend([
    "",
    "## Reproducibility and Data-Quality Notes",
    "",
    "- Source experiment files were analyzed in read-only mode.",
    "- Twenty archived baseline runs and five current DA-SACO runs were included.",
    "- Invalid, failed, dry-run, diagnostic, and historical attempt subtrees were excluded.",
    "- B0-B3 resource files use `timestamp,pod,cpu,memory,restarts,ready`.",
    "- DA-SACO resource files use `timestamp_utc,pod,cpu,memory`.",
    "- CPU values were normalized to millicores.",
    "- Memory values were normalized to MiB.",
    "- Nanosecond AMF timestamps were normalized to microseconds for Python datetime processing.",
    "- All 25 AMF workload windows contained parseable registration events.",
    "- Registration completion evidence was present in all 25 runs.",
    "- `InitialUEMessage` usually lacks SUPI and was not used as the unique-UE denominator.",
    "",
    "## Current Limitations",
    "",
    (
        "- Rejected-only and rejected-then-completed devices still "
        "require SUPI-set reconciliation."
    ),
    (
        "- Registration latency still requires identity-aware event "
        "pairing or validated per-UE latency evidence."
    ),
    (
        "- DA-SACO scaling and recovery results will be derived from "
        "`replica-timeseries.csv` through `RECOVERY_END_UTC`."
    ),
    (
        "- Raw Student t confidence intervals may exceed the logical "
        "0-100 percent range and should not be reported without an "
        "explicit bounded-interval policy."
    ),
    "",
    "## Generated Evidence Files",
    "",
    "- `UNIFIED-25-RUN-RESULTS.csv`",
    "- `UNIFIED-25-RUN-NF-PRESSURE.csv`",
    "- `UNIFIED-5-METHOD-SUMMARY.csv`",
    "- `UNIFIED-5-METHOD-NF-PRESSURE-SUMMARY.csv`",
    "- `UNIFIED-NF-PRESSURE-RANKING.csv`",
    "- `UNIFIED-RESULTS-AND-NF-PRESSURE-REPORT.txt`",
    "",
])

markdown_path.write_text(
    "\n".join(markdown) + "\n",
    encoding="utf-8",
)

methods = {
    row["method"]
    for row in summary_rows
}

functions = {
    row["function"]
    for row in summary_rows
}

gate = (
    len(methods) == 5
    and len(method_rows) == 5
    and len(run_rows) == 25
    and len(summary_rows) > 0
)

report = [
    "===== PAPER AND GITHUB NF-PRESSURE SUMMARY =====",
    f"INPUT_PRESSURE_ROWS={len(pressure_rows)}",
    f"RUN_RESULT_ROWS={len(run_rows)}",
    f"METHOD_RESULT_ROWS={len(method_rows)}",
    f"METHODS_IN_NF_SUMMARY={len(methods)}",
    f"FUNCTIONS_DISCOVERED={len(functions)}",
    f"NF_SUMMARY_ROWS={len(summary_rows)}",
    f"RANKING_ROWS={len(ranking_rows)}",
    "FUNCTION_LIST=" + ",".join(sorted(functions)),
    (
        "PAPER_GITHUB_SUMMARY_GATE="
        + ("PASS" if gate else "REVIEW")
    ),
    (
        "NEXT_ACTION="
        + (
            "EXTRACT_LATENCY_SCALING_RECOVERY_AND_GENERATE_FIGURES"
            if gate
            else "REVIEW_PRESSURE_SUMMARY"
        )
    ),
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"NF_SUMMARY={nf_summary_path}",
    f"RANKING={ranking_path}",
    f"MARKDOWN={markdown_path}",
    f"REPORT={report_path}",
]

report_path.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)

print("\n".join(report))

print()
print("===== TOP 20 NF PRESSURE COMBINATIONS =====")

for index, row in enumerate(ranking_rows[:20], start=1):
    print(
        f"{index:02d}|"
        f"{row['method_name']}|"
        f"{row['function']}|"
        f"CPU_P95_M={formatted(row['cpu_p95_m_mean_across_runs'])}|"
        f"CPU_PEAK_M={formatted(row['cpu_max_m_overall'])}|"
        f"MEM_P95_MIB="
        f"{formatted(row['memory_p95_mib_mean_across_runs'])}|"
        f"MEM_PEAK_MIB={formatted(row['memory_max_mib_overall'])}"
    )

raise SystemExit(0 if gate else 1)
