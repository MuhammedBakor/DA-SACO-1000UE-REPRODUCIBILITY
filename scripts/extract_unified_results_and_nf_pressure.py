import csv
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

output = (
    Path.home()
    / "PREVIOUS-VM-EVIDENCE"
    / "UNIFIED-25-RUN-ANALYSIS"
)

map_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv"
event_path = output / "UNIFIED-25-RUN-AMF-EVENT-AUDIT.csv"

run_csv = output / "UNIFIED-25-RUN-RESULTS.csv"
pressure_csv = output / "UNIFIED-25-RUN-NF-PRESSURE.csv"
method_csv = output / "UNIFIED-5-METHOD-SUMMARY.csv"
report_path = output / "UNIFIED-RESULTS-AND-NF-PRESSURE-REPORT.txt"

TARGET_UES = 1000

def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def percentile_type7(values, probability):
    values = sorted(values)
    count = len(values)

    if count == 0:
        return None

    if count == 1:
        return values[0]

    position = (count - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    weight = position - lower

    return (
        values[lower] * (1.0 - weight)
        + values[upper] * weight
    )

def summarize(values):
    clean = [
        value
        for value in values
        if value is not None and math.isfinite(value)
    ]

    if not clean:
        return {
            "samples": 0,
            "mean": None,
            "median": None,
            "p95": None,
            "p99": None,
            "max": None,
        }

    return {
        "samples": len(clean),
        "mean": statistics.fmean(clean),
        "median": statistics.median(clean),
        "p95": percentile_type7(clean, 0.95),
        "p99": percentile_type7(clean, 0.99),
        "max": max(clean),
    }

def parse_cpu_millicores(value):
    value = str(value or "").strip().lower()

    if not value:
        return None

    if value.endswith("n"):
        parsed = number(value[:-1])
        return None if parsed is None else parsed / 1000000.0

    if value.endswith("u"):
        parsed = number(value[:-1])
        return None if parsed is None else parsed / 1000.0

    if value.endswith("m"):
        return number(value[:-1])

    parsed = number(value)

    return None if parsed is None else parsed * 1000.0

def parse_memory_mib(value):
    value = str(value or "").strip()

    if not value:
        return None

    match = re.fullmatch(
        r"([0-9]+(?:[.][0-9]+)?)([A-Za-z]+)?",
        value,
    )

    if not match:
        return None

    amount = float(match.group(1))
    unit = (match.group(2) or "").lower()

    factors = {
        "": 1.0 / (1024.0 * 1024.0),
        "b": 1.0 / (1024.0 * 1024.0),
        "ki": 1.0 / 1024.0,
        "kib": 1.0 / 1024.0,
        "mi": 1.0,
        "mib": 1.0,
        "gi": 1024.0,
        "gib": 1024.0,
        "k": 1000.0 / (1024.0 * 1024.0),
        "kb": 1000.0 / (1024.0 * 1024.0),
        "m": 1000000.0 / (1024.0 * 1024.0),
        "mb": 1000000.0 / (1024.0 * 1024.0),
        "g": 1000000000.0 / (1024.0 * 1024.0),
        "gb": 1000000000.0 / (1024.0 * 1024.0),
    }

    factor = factors.get(unit)

    if factor is None:
        return None

    return amount * factor

def classify_function(pod):
    value = str(pod or "").lower()

    ordered = [
        ("open5glos", "Open5GLoS"),
        ("ausf", "AUSF"),
        ("amf", "AMF"),
        ("nrf", "NRF"),
        ("pcf", "PCF"),
        ("udm", "UDM"),
        ("udr", "UDR"),
        ("nssf", "NSSF"),
        ("smf", "SMF"),
        ("upf", "UPF"),
        ("mongodb", "MongoDB"),
        ("webui", "WebUI"),
    ]

    for token, name in ordered:
        if token in value:
            return name

    return "OTHER"

def display_run(method, run):
    if method == "R1":
        return run

    match = re.search(r"R[1-5]", run, re.IGNORECASE)

    if match:
        return match.group(0).upper()

    return run

if not map_path.is_file() or not event_path.is_file():
    print("INPUT_GATE=FAIL")
    print(f"CANONICAL_MAP_EXISTS={map_path.is_file()}")
    print(f"EVENT_AUDIT_EXISTS={event_path.is_file()}")
    raise SystemExit(1)

with map_path.open(newline="") as stream:
    map_rows = list(csv.DictReader(stream))

with event_path.open(newline="") as stream:
    event_rows = list(csv.DictReader(stream))

resource_paths = {}

for row in map_rows:
    if row.get("evidence_type") != "RESOURCE":
        continue

    key = (
        row.get("method", "").strip(),
        row.get("run", "").strip(),
    )

    resource_paths[key] = Path(row["canonical_file"])

run_results = []
event_by_method = defaultdict(list)

for row in event_rows:
    method = row.get("method", "").strip()
    method_name = row.get("method_name", "").strip()
    run_original = row.get("run", "").strip()
    run = display_run(method, run_original)

    completed = int(row["registration_complete_unique_supis"])
    rejected = int(row["registration_reject_unique_supis"])
    accepted = int(row["registration_accept_unique_supis"])

    success_rate = completed * 100.0 / TARGET_UES
    not_completed = TARGET_UES - completed

    result = {
        "method": method,
        "method_name": method_name,
        "run": run,
        "run_original": run_original,
        "target_ues": TARGET_UES,
        "registration_accept_unique_supis": accepted,
        "registration_complete_unique_supis": completed,
        "registration_reject_unique_supis": rejected,
        "not_completed_against_target": not_completed,
        "success_rate_percent": success_rate,
        "window_start_utc": row["window_start_utc"],
        "window_end_utc": row["window_end_utc"],
        "amf_file_count": row["amf_file_count"],
        "unparseable_event_lines": row["unparseable_event_lines"],
    }

    run_results.append(result)
    event_by_method[(method, method_name)].append(result)

run_fields = [
    "method",
    "method_name",
    "run",
    "run_original",
    "target_ues",
    "registration_accept_unique_supis",
    "registration_complete_unique_supis",
    "registration_reject_unique_supis",
    "not_completed_against_target",
    "success_rate_percent",
    "window_start_utc",
    "window_end_utc",
    "amf_file_count",
    "unparseable_event_lines",
]

with run_csv.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=run_fields)
    writer.writeheader()
    writer.writerows(run_results)

pressure_rows = []
resource_failures = []
resource_headers = defaultdict(int)

for row in run_results:
    key = (row["method"], row["run_original"])
    path = resource_paths.get(key)

    if path is None or not path.is_file():
        resource_failures.append(
            f"{row['method']}|{row['run_original']}|MISSING"
        )
        continue

    per_function_cpu = defaultdict(list)
    per_function_memory = defaultdict(list)
    invalid_cpu = 0
    invalid_memory = 0

    with path.open(
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as stream:
        reader = csv.DictReader(stream)
        header_value = ",".join(reader.fieldnames or [])
        resource_headers[header_value] += 1

        for sample in reader:
            pod = sample.get("pod", "")
            function = classify_function(pod)

            cpu = parse_cpu_millicores(sample.get("cpu"))
            memory = parse_memory_mib(sample.get("memory"))

            if cpu is None:
                invalid_cpu += 1
            else:
                per_function_cpu[function].append(cpu)

            if memory is None:
                invalid_memory += 1
            else:
                per_function_memory[function].append(memory)

    functions = sorted(
        set(per_function_cpu)
        | set(per_function_memory)
    )

    if not functions:
        resource_failures.append(
            f"{row['method']}|{row['run_original']}|NO_VALID_SAMPLES"
        )

    for function in functions:
        cpu_stats = summarize(per_function_cpu[function])
        memory_stats = summarize(per_function_memory[function])

        pressure_rows.append({
            "method": row["method"],
            "method_name": row["method_name"],
            "run": row["run"],
            "run_original": row["run_original"],
            "function": function,
            "resource_file": str(path),
            "cpu_samples": cpu_stats["samples"],
            "cpu_mean_m": cpu_stats["mean"],
            "cpu_median_m": cpu_stats["median"],
            "cpu_p95_m": cpu_stats["p95"],
            "cpu_p99_m": cpu_stats["p99"],
            "cpu_max_m": cpu_stats["max"],
            "memory_samples": memory_stats["samples"],
            "memory_mean_mib": memory_stats["mean"],
            "memory_median_mib": memory_stats["median"],
            "memory_p95_mib": memory_stats["p95"],
            "memory_p99_mib": memory_stats["p99"],
            "memory_max_mib": memory_stats["max"],
            "invalid_cpu_rows_in_file": invalid_cpu,
            "invalid_memory_rows_in_file": invalid_memory,
        })

pressure_fields = [
    "method",
    "method_name",
    "run",
    "run_original",
    "function",
    "resource_file",
    "cpu_samples",
    "cpu_mean_m",
    "cpu_median_m",
    "cpu_p95_m",
    "cpu_p99_m",
    "cpu_max_m",
    "memory_samples",
    "memory_mean_mib",
    "memory_median_mib",
    "memory_p95_mib",
    "memory_p99_mib",
    "memory_max_mib",
    "invalid_cpu_rows_in_file",
    "invalid_memory_rows_in_file",
]

with pressure_csv.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=pressure_fields,
    )
    writer.writeheader()
    writer.writerows(pressure_rows)

method_rows = []

for (method, method_name), rows in sorted(
    event_by_method.items()
):
    completed = [
        row["registration_complete_unique_supis"]
        for row in rows
    ]

    rates = [
        row["success_rate_percent"]
        for row in rows
    ]

    rejects = [
        row["registration_reject_unique_supis"]
        for row in rows
    ]

    completed_stats = summarize(completed)
    rate_stats = summarize(rates)
    reject_stats = summarize(rejects)

    sample_sd = (
        statistics.stdev(rates)
        if len(rates) >= 2
        else None
    )

    ci_margin = (
        2.7764451051977987
        * sample_sd
        / math.sqrt(len(rates))
        if sample_sd is not None
        else None
    )

    method_rows.append({
        "method": method,
        "method_name": method_name,
        "runs": len(rows),
        "target_ues_per_run": TARGET_UES,
        "completed_mean": completed_stats["mean"],
        "completed_median": completed_stats["median"],
        "completed_min": min(completed),
        "completed_max": max(completed),
        "success_rate_mean_percent": rate_stats["mean"],
        "success_rate_sample_sd": sample_sd,
        "success_rate_95ci_low": (
            rate_stats["mean"] - ci_margin
            if ci_margin is not None
            else None
        ),
        "success_rate_95ci_high": (
            rate_stats["mean"] + ci_margin
            if ci_margin is not None
            else None
        ),
        "reject_unique_supis_mean": reject_stats["mean"],
        "reject_unique_supis_max": reject_stats["max"],
    })

method_fields = [
    "method",
    "method_name",
    "runs",
    "target_ues_per_run",
    "completed_mean",
    "completed_median",
    "completed_min",
    "completed_max",
    "success_rate_mean_percent",
    "success_rate_sample_sd",
    "success_rate_95ci_low",
    "success_rate_95ci_high",
    "reject_unique_supis_mean",
    "reject_unique_supis_max",
]

with method_csv.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=method_fields,
    )
    writer.writeheader()
    writer.writerows(method_rows)

run_gate = len(run_results) == 25
method_gate = len(method_rows) == 5
resource_file_gate = len(resource_paths) == 25
resource_parse_gate = not resource_failures
pressure_gate = len(pressure_rows) > 0
unparseable_gate = all(
    int(row["unparseable_event_lines"]) == 0
    for row in run_results
)

final_gate = all([
    run_gate,
    method_gate,
    resource_file_gate,
    resource_parse_gate,
    pressure_gate,
    unparseable_gate,
])

report = [
    "===== UNIFIED RESULTS AND NF PRESSURE EXTRACTION =====",
    "ANALYSIS_SCOPE=25_RUNS_5_METHODS_1000_UE",
    "SUCCESS_EVENT=Handle Registration Complete",
    "SUCCESS_DENOMINATOR=1000_PLANNED_UE_PER_RUN",
    "PERCENTILE_METHOD=HYNDMAN_FAN_TYPE_7",
    "CPU_UNIT=millicores",
    "MEMORY_UNIT=MiB",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
    "===== METHOD REGISTRATION RESULTS =====",
]

for row in method_rows:
    report.append(
        "METHOD="
        f"{row['method']}|{row['method_name']}"
        f"|runs={row['runs']}"
        f"|completed_mean={row['completed_mean']:.3f}"
        f"|success_rate_mean_percent="
        f"{row['success_rate_mean_percent']:.3f}"
        f"|sample_sd={row['success_rate_sample_sd']:.3f}"
        f"|ci95_low={row['success_rate_95ci_low']:.3f}"
        f"|ci95_high={row['success_rate_95ci_high']:.3f}"
    )

report.extend([
    "",
    "===== RESOURCE SCHEMAS =====",
])

for resource_header, count in sorted(resource_headers.items()):
    report.append(
        f"RESOURCE_SCHEMA=count={count}|{resource_header}"
    )

report.extend([
    "",
    "===== EXTRACTION GATES =====",
    f"RUN_RESULTS_COUNT={len(run_results)}",
    f"METHOD_RESULTS_COUNT={len(method_rows)}",
    f"RESOURCE_PATH_COUNT={len(resource_paths)}",
    f"NF_PRESSURE_ROWS={len(pressure_rows)}",
    f"RESOURCE_FAILURE_COUNT={len(resource_failures)}",
])

for failure in resource_failures:
    report.append(f"RESOURCE_FAILURE={failure}")

report.extend([
    f"RUN_25_GATE={'PASS' if run_gate else 'FAIL'}",
    f"METHOD_5_GATE={'PASS' if method_gate else 'FAIL'}",
    (
        "RESOURCE_25_FILE_GATE="
        f"{'PASS' if resource_file_gate else 'FAIL'}"
    ),
    (
        "RESOURCE_PARSE_GATE="
        f"{'PASS' if resource_parse_gate else 'FAIL'}"
    ),
    (
        "NF_PRESSURE_GATE="
        f"{'PASS' if pressure_gate else 'FAIL'}"
    ),
    (
        "AMF_UNPARSEABLE_ZERO_GATE="
        f"{'PASS' if unparseable_gate else 'FAIL'}"
    ),
    (
        "UNIFIED_EXTRACTION_GATE="
        f"{'PASS' if final_gate else 'REVIEW'}"
    ),
    (
        "NEXT_ACTION="
        + (
            "GENERATE_PAPER_TABLES_FIGURES_AND_GITHUB_PACKAGE"
            if final_gate
            else "REVIEW_REPORTED_RESOURCE_FAILURES"
        )
    ),
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"RUN_RESULTS={run_csv}",
    f"NF_PRESSURE_RESULTS={pressure_csv}",
    f"METHOD_SUMMARY={method_csv}",
    f"REPORT={report_path}",
])

report_path.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)

print("\n".join(report))

raise SystemExit(0 if final_gate else 1)
