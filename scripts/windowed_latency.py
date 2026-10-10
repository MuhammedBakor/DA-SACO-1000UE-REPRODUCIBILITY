import csv
import math
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

map_path = Path(sys.argv[1])
output = Path(sys.argv[2])

details_csv = output / "UNIFIED-25-RUN-POST-SECURITY-LATENCY-DETAIL.csv"
runs_csv = output / "UNIFIED-25-RUN-POST-SECURITY-LATENCY-SUMMARY.csv"
methods_csv = output / "UNIFIED-5-METHOD-POST-SECURITY-LATENCY-SUMMARY.csv"
report_txt = output / "UNIFIED-POST-SECURITY-LATENCY-REPORT.txt"

ts_re = re.compile(
    r"([0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:[.][0-9]+)?Z)"
)

supi_re = re.compile(r"(2089300000[0-9]{5})")
start_re = re.compile(r"Handle InitialRegistration", re.I)
end_re = re.compile(r"Handle Registration Complete", re.I)

def parse_time(text):
    match = ts_re.search(text)

    if not match:
        return None

    value = match.group(1)[:-1]

    if "." in value:
        whole, fraction = value.split(".", 1)
        value = whole + "." + (fraction + "000000")[:6]

    return datetime.fromisoformat(
        value + "+00:00"
    ).astimezone(timezone.utc)

def parse_boundary(text):
    return datetime.fromisoformat(
        text.strip().replace("Z", "+00:00")
    ).astimezone(timezone.utc)

def percentile(values, probability):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower

    return (
        values[lower] * (1.0 - weight)
        + values[upper] * weight
    )

def summarize(values):
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "maximum": max(values),
    }

with map_path.open(newline="") as stream:
    evidence = list(csv.DictReader(stream))

runs = defaultdict(list)

for row in evidence:
    key = (
        row["method"].strip(),
        row["method_name"].strip(),
        row["run"].strip(),
        row["run_path"].strip(),
    )
    runs[key].append(row)

detail_rows = []
run_rows = []
method_runs = defaultdict(list)

for key, rows in sorted(runs.items()):
    method, method_name, run, run_path_text = key
    run_path = Path(run_path_text)
    by_type = defaultdict(list)

    for row in rows:
        by_type[row["evidence_type"]].append(
            Path(row["canonical_file"])
        )

    if method == "R1":
        window_values = {}

        for line in by_type["RUN_WINDOW"][0].read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            if "=" in line:
                name, value = line.split("=", 1)
                window_values[name.strip()] = value.strip()

        window_start = parse_boundary(
            window_values["RUN_START_UTC"]
        )
        window_end = parse_boundary(
            window_values["WORKLOAD_END_UTC"]
        )
    else:
        window_start = parse_boundary(
            by_type["START_UTC"][0].read_text(
                encoding="utf-8",
                errors="replace",
            )
        )
        window_end = parse_boundary(
            by_type["END_UTC"][0].read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

    starts = defaultdict(list)
    completes = defaultdict(list)

    for amf_file in by_type["AMF"]:
        with amf_file.open(
            encoding="utf-8",
            errors="replace",
        ) as stream:
            for line in stream:
                is_start = bool(start_re.search(line))
                is_end = bool(end_re.search(line))

                if not is_start and not is_end:
                    continue

                timestamp = parse_time(line)
                supi_match = supi_re.search(line)

                if timestamp is None or supi_match is None:
                    continue

                if not window_start <= timestamp <= window_end:
                    continue

                supi = supi_match.group(1)

                if is_start:
                    starts[supi].append(timestamp)

                if is_end:
                    completes[supi].append(timestamp)

    completed_supis = set(completes)
    latency_values = []

    for supi in sorted(set(starts) & completed_supis):
        start = min(starts[supi])

        possible_ends = [
            timestamp
            for timestamp in completes[supi]
            if timestamp >= start
        ]

        if not possible_ends:
            continue

        complete = min(possible_ends)
        latency_ms = (
            complete - start
        ).total_seconds() * 1000.0

        latency_values.append(latency_ms)

        detail_rows.append({
            "method": method,
            "method_name": method_name,
            "run": run,
            "supi": "imsi-" + supi,
            "start_timestamp": start.isoformat(),
            "complete_timestamp": complete.isoformat(),
            "latency_ms": latency_ms,
        })

    if not latency_values:
        continue

    stats = summarize(latency_values)
    coverage = (
        stats["count"] * 100.0 / len(completed_supis)
    )

    run_row = {
        "method": method,
        "method_name": method_name,
        "run": run,
        "completed_unique_supis": len(completed_supis),
        "valid_latency_supis": stats["count"],
        "coverage_percent": coverage,
        "mean_ms": stats["mean"],
        "median_ms": stats["median"],
        "p95_ms": stats["p95"],
        "p99_ms": stats["p99"],
        "max_ms": stats["maximum"],
    }

    run_rows.append(run_row)
    method_runs[(method, method_name)].append(run_row)

    if method == "B3":
        existing_file = run_path / "per-ue-latency.csv"

        if existing_file.is_file():
            existing = {}

            with existing_file.open(newline="") as stream:
                for row in csv.DictReader(stream):
                    existing[row["supi"]] = float(
                        row["latency_ms"]
                    )

            reconstructed = {
                row["supi"]: row["latency_ms"]
                for row in detail_rows
                if row["method"] == method
                and row["run"] == run
            }

            shared = set(existing) & set(reconstructed)

            differences = [
                abs(existing[supi] - reconstructed[supi])
                for supi in shared
            ]

            print(
                "B3_VALIDATION="
                + run
                + "|existing="
                + str(len(existing))
                + "|reconstructed="
                + str(len(reconstructed))
                + "|shared="
                + str(len(shared))
                + "|max_difference_ms="
                + str(max(differences) if differences else "")
            )

detail_fields = [
    "method",
    "method_name",
    "run",
    "supi",
    "start_timestamp",
    "complete_timestamp",
    "latency_ms",
]

with details_csv.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=detail_fields,
    )
    writer.writeheader()
    writer.writerows(detail_rows)

run_fields = list(run_rows[0])

with runs_csv.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=run_fields,
    )
    writer.writeheader()
    writer.writerows(run_rows)

method_rows = []

for key, rows in sorted(method_runs.items()):
    method, method_name = key

    def average(field):
        return statistics.fmean(
            float(row[field]) for row in rows
        )

    method_rows.append({
        "method": method,
        "method_name": method_name,
        "runs": len(rows),
        "valid_latency_supis": sum(
            int(row["valid_latency_supis"])
            for row in rows
        ),
        "mean_coverage_percent": average(
            "coverage_percent"
        ),
        "mean_of_run_means_ms": average("mean_ms"),
        "mean_of_run_medians_ms": average("median_ms"),
        "mean_of_run_p95_ms": average("p95_ms"),
        "mean_of_run_p99_ms": average("p99_ms"),
        "maximum_latency_ms": max(
            float(row["max_ms"])
            for row in rows
        ),
    })

method_fields = list(method_rows[0])

with methods_csv.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=method_fields,
    )
    writer.writeheader()
    writer.writerows(method_rows)

lines = [
    "===== WINDOW-FILTERED POST-SECURITY LATENCY =====",
    "START_EVENT=Handle InitialRegistration",
    "END_EVENT=Handle Registration Complete",
    "NOT_END_TO_END_LATENCY=true",
    "PERCENTILE_METHOD=HYNDMAN_FAN_TYPE_7",
    f"RUNS_ANALYZED={len(run_rows)}",
    f"METHODS_ANALYZED={len(method_rows)}",
    f"PER_UE_ROWS={len(detail_rows)}",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
]

for row in run_rows:
    lines.append(
        "RUN="
        f"{row['method']}|{row['method_name']}|{row['run']}"
        f"|completed={row['completed_unique_supis']}"
        f"|valid={row['valid_latency_supis']}"
        f"|coverage={row['coverage_percent']:.3f}"
        f"|mean_ms={row['mean_ms']:.3f}"
        f"|median_ms={row['median_ms']:.3f}"
        f"|p95_ms={row['p95_ms']:.3f}"
        f"|p99_ms={row['p99_ms']:.3f}"
        f"|max_ms={row['max_ms']:.3f}"
    )

lines.append("")

for row in method_rows:
    lines.append(
        "METHOD="
        f"{row['method']}|{row['method_name']}"
        f"|runs={row['runs']}"
        f"|valid={row['valid_latency_supis']}"
        f"|coverage={row['mean_coverage_percent']:.3f}"
        f"|mean_of_means_ms="
        f"{row['mean_of_run_means_ms']:.3f}"
        f"|mean_of_medians_ms="
        f"{row['mean_of_run_medians_ms']:.3f}"
        f"|mean_p95_ms={row['mean_of_run_p95_ms']:.3f}"
        f"|mean_p99_ms={row['mean_of_run_p99_ms']:.3f}"
        f"|max_ms={row['maximum_latency_ms']:.3f}"
    )

gate = (
    len(run_rows) == 25
    and len(method_rows) == 5
)

lines.extend([
    "",
    (
        "WINDOWED_LATENCY_GATE="
        + ("PASS" if gate else "REVIEW")
    ),
    (
        "NEXT_ACTION="
        + (
            "VALIDATE_B3_AND_RUN_INTEGRATED_STATISTICS"
            if gate
            else "REVIEW_MISSING_WINDOWED_LATENCY_RUNS"
        )
    ),
    f"DETAIL={details_csv}",
    f"RUN_SUMMARY={runs_csv}",
    f"METHOD_SUMMARY={methods_csv}",
])

report_txt.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print("\n".join(lines))

raise SystemExit(0 if gate else 1)
