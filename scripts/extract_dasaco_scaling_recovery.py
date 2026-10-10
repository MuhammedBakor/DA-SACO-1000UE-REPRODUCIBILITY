import csv
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

output = (
    Path.home()
    / "PREVIOUS-VM-EVIDENCE"
    / "UNIFIED-25-RUN-ANALYSIS"
)

map_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv"

detail_path = output / "DA-SACO-5-RUN-SCALING-RECOVERY.csv"
run_summary_path = output / "DA-SACO-5-RUN-SCALING-RECOVERY-SUMMARY.csv"
report_path = output / "DA-SACO-SCALING-RECOVERY-REPORT.txt"
markdown_path = output / "DA-SACO-SCALING-RECOVERY-RESULTS.md"

def parse_time(value):
    value = str(value or "").strip()

    if not value:
        return None

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)

def read_window(path):
    values = {}

    for line in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return {
        "run_start": parse_time(values.get("RUN_START_UTC")),
        "workload_end": parse_time(values.get("WORKLOAD_END_UTC")),
        "recovery_end": parse_time(values.get("RECOVERY_END_UTC")),
    }

def integer(value):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None

def mean(values):
    clean = [
        value
        for value in values
        if value is not None and math.isfinite(value)
    ]

    if not clean:
        return None

    return statistics.fmean(clean)

def median(values):
    clean = [
        value
        for value in values
        if value is not None and math.isfinite(value)
    ]

    if not clean:
        return None

    return statistics.median(clean)

def fmt(value, digits=3):
    if value is None:
        return ""

    return f"{value:.{digits}f}"

if not map_path.is_file():
    print("CANONICAL_MAP_GATE=FAIL")
    print(f"MISSING={map_path}")
    raise SystemExit(1)

with map_path.open(newline="") as stream:
    map_rows = list(csv.DictReader(stream))

grouped = defaultdict(lambda: defaultdict(list))

for row in map_rows:
    if row.get("method", "").strip() != "R1":
        continue

    run = row.get("run", "").strip()
    evidence_type = row.get("evidence_type", "").strip()

    grouped[run][evidence_type].append(
        Path(row["canonical_file"])
    )

detail_rows = []
run_summary_rows = []
failures = []

for run in sorted(grouped):
    evidence = grouped[run]

    replica_files = evidence.get("REPLICA", [])
    window_files = evidence.get("RUN_WINDOW", [])

    if len(replica_files) != 1 or len(window_files) != 1:
        failures.append(
            f"{run}|REPLICA_FILES={len(replica_files)}"
            f"|WINDOW_FILES={len(window_files)}"
        )
        continue

    replica_path = replica_files[0]
    window_path = window_files[0]

    if not replica_path.is_file() or not window_path.is_file():
        failures.append(f"{run}|MISSING_INPUT_FILE")
        continue

    window = read_window(window_path)

    if any(value is None for value in window.values()):
        failures.append(f"{run}|INVALID_RUN_WINDOW")
        continue

    samples_by_function = defaultdict(list)
    invalid_rows = 0

    with replica_path.open(
        encoding="utf-8",
        errors="replace",
        newline="",
    ) as stream:
        reader = csv.DictReader(stream)

        required = {
            "timestamp_utc",
            "function",
            "desired",
            "ready",
        }

        if not required.issubset(set(reader.fieldnames or [])):
            failures.append(
                f"{run}|INVALID_REPLICA_SCHEMA|"
                + ",".join(reader.fieldnames or [])
            )
            continue

        for row in reader:
            timestamp = parse_time(row.get("timestamp_utc"))
            function = str(row.get("function") or "").strip()
            desired = integer(row.get("desired"))
            ready = integer(row.get("ready"))

            if (
                timestamp is None
                or not function
                or desired is None
                or ready is None
            ):
                invalid_rows += 1
                continue

            if timestamp < window["run_start"]:
                continue

            if timestamp > window["recovery_end"]:
                continue

            samples_by_function[function].append({
                "timestamp": timestamp,
                "desired": desired,
                "ready": ready,
            })

    functions_scaled = 0
    functions_recovered = 0
    functions_not_recovered = 0
    first_scale_offsets = []
    ready_scale_offsets = []
    recovery_offsets = []
    overall_recovery_candidates = []

    for function, samples in sorted(samples_by_function.items()):
        samples.sort(key=lambda item: item["timestamp"])

        if not samples:
            continue

        baseline_desired = samples[0]["desired"]
        baseline_ready = samples[0]["ready"]

        max_desired = max(item["desired"] for item in samples)
        max_ready = max(item["ready"] for item in samples)

        scale_out_samples = [
            item
            for item in samples
            if item["desired"] > baseline_desired
        ]

        ready_above_samples = [
            item
            for item in samples
            if item["ready"] > baseline_ready
        ]

        scaled = bool(scale_out_samples)

        first_scale_time = (
            scale_out_samples[0]["timestamp"]
            if scale_out_samples
            else None
        )

        first_ready_above_time = (
            ready_above_samples[0]["timestamp"]
            if ready_above_samples
            else None
        )

        scale_out_from_start_seconds = (
            (first_scale_time - window["run_start"]).total_seconds()
            if first_scale_time
            else None
        )

        ready_above_from_start_seconds = (
            (
                first_ready_above_time
                - window["run_start"]
            ).total_seconds()
            if first_ready_above_time
            else None
        )

        ready_after_scale_seconds = (
            (
                first_ready_above_time
                - first_scale_time
            ).total_seconds()
            if (
                first_scale_time is not None
                and first_ready_above_time is not None
                and first_ready_above_time >= first_scale_time
            )
            else None
        )

        desired_transitions_up = 0
        desired_transitions_down = 0
        ready_transitions_up = 0
        ready_transitions_down = 0

        previous = samples[0]

        for current in samples[1:]:
            if current["desired"] > previous["desired"]:
                desired_transitions_up += 1
            elif current["desired"] < previous["desired"]:
                desired_transitions_down += 1

            if current["ready"] > previous["ready"]:
                ready_transitions_up += 1
            elif current["ready"] < previous["ready"]:
                ready_transitions_down += 1

            previous = current

        above_baseline_seconds = 0.0

        for current, following in zip(samples, samples[1:]):
            interval_end = min(
                following["timestamp"],
                window["recovery_end"],
            )

            if interval_end <= current["timestamp"]:
                continue

            if current["desired"] > baseline_desired:
                above_baseline_seconds += (
                    interval_end - current["timestamp"]
                ).total_seconds()

        last = samples[-1]

        if (
            last["timestamp"] < window["recovery_end"]
            and last["desired"] > baseline_desired
        ):
            above_baseline_seconds += (
                window["recovery_end"]
                - last["timestamp"]
            ).total_seconds()

        post_workload = [
            item
            for item in samples
            if item["timestamp"] >= window["workload_end"]
        ]

        recovery_time = None

        if scaled:
            for index, item in enumerate(post_workload):
                if (
                    item["desired"] != baseline_desired
                    or item["ready"] != baseline_ready
                ):
                    continue

                stable = all(
                    later["desired"] == baseline_desired
                    and later["ready"] == baseline_ready
                    for later in post_workload[index:]
                )

                if stable:
                    recovery_time = item["timestamp"]
                    break

        recovered = (
            not scaled
            or recovery_time is not None
        )

        recovery_after_workload_seconds = (
            (
                recovery_time
                - window["workload_end"]
            ).total_seconds()
            if recovery_time is not None
            else 0.0 if not scaled else None
        )

        desired_at_end = samples[-1]["desired"]
        ready_at_end = samples[-1]["ready"]

        at_baseline_at_end = (
            desired_at_end == baseline_desired
            and ready_at_end == baseline_ready
        )

        if scaled:
            functions_scaled += 1

            if scale_out_from_start_seconds is not None:
                first_scale_offsets.append(
                    scale_out_from_start_seconds
                )

            if ready_after_scale_seconds is not None:
                ready_scale_offsets.append(
                    ready_after_scale_seconds
                )

            if recovered:
                functions_recovered += 1

                if recovery_after_workload_seconds is not None:
                    recovery_offsets.append(
                        recovery_after_workload_seconds
                    )
                    overall_recovery_candidates.append(
                        recovery_after_workload_seconds
                    )
            else:
                functions_not_recovered += 1

        detail_rows.append({
            "run": run,
            "function": function,
            "sample_count": len(samples),
            "run_start_utc": window["run_start"].isoformat(),
            "workload_end_utc": window["workload_end"].isoformat(),
            "recovery_end_utc": window["recovery_end"].isoformat(),
            "baseline_desired": baseline_desired,
            "baseline_ready": baseline_ready,
            "max_desired": max_desired,
            "max_ready": max_ready,
            "scaled_out": str(scaled).lower(),
            "first_scale_out_utc": (
                first_scale_time.isoformat()
                if first_scale_time
                else ""
            ),
            "first_scale_out_from_start_seconds": (
                scale_out_from_start_seconds
            ),
            "first_ready_above_baseline_utc": (
                first_ready_above_time.isoformat()
                if first_ready_above_time
                else ""
            ),
            "first_ready_above_from_start_seconds": (
                ready_above_from_start_seconds
            ),
            "ready_after_scale_seconds": ready_after_scale_seconds,
            "desired_scale_out_transitions": desired_transitions_up,
            "desired_scale_in_transitions": desired_transitions_down,
            "ready_increase_transitions": ready_transitions_up,
            "ready_decrease_transitions": ready_transitions_down,
            "seconds_desired_above_baseline": above_baseline_seconds,
            "recovered_to_stable_baseline": str(recovered).lower(),
            "recovery_utc": (
                recovery_time.isoformat()
                if recovery_time
                else ""
            ),
            "recovery_after_workload_seconds": (
                recovery_after_workload_seconds
            ),
            "desired_at_recovery_end": desired_at_end,
            "ready_at_recovery_end": ready_at_end,
            "at_baseline_at_recovery_end": (
                str(at_baseline_at_end).lower()
            ),
            "replica_file": str(replica_path),
            "invalid_replica_rows_in_run": invalid_rows,
        })

    overall_recovery_seconds = (
        max(overall_recovery_candidates)
        if overall_recovery_candidates
        else 0.0 if functions_scaled == 0 else None
    )

    run_recovered = (
        functions_not_recovered == 0
    )

    run_summary_rows.append({
        "run": run,
        "functions_observed": len(samples_by_function),
        "functions_scaled": functions_scaled,
        "functions_recovered": functions_recovered,
        "functions_not_recovered": functions_not_recovered,
        "run_recovered_by_recovery_end": (
            str(run_recovered).lower()
        ),
        "first_scale_out_from_start_seconds": (
            min(first_scale_offsets)
            if first_scale_offsets
            else None
        ),
        "median_ready_after_scale_seconds": (
            median(ready_scale_offsets)
        ),
        "overall_recovery_after_workload_seconds": (
            overall_recovery_seconds
        ),
        "mean_function_recovery_after_workload_seconds": (
            mean(recovery_offsets)
        ),
        "invalid_replica_rows": invalid_rows,
        "replica_file": str(replica_path),
        "window_file": str(window_path),
    })

detail_fields = [
    "run",
    "function",
    "sample_count",
    "run_start_utc",
    "workload_end_utc",
    "recovery_end_utc",
    "baseline_desired",
    "baseline_ready",
    "max_desired",
    "max_ready",
    "scaled_out",
    "first_scale_out_utc",
    "first_scale_out_from_start_seconds",
    "first_ready_above_baseline_utc",
    "first_ready_above_from_start_seconds",
    "ready_after_scale_seconds",
    "desired_scale_out_transitions",
    "desired_scale_in_transitions",
    "ready_increase_transitions",
    "ready_decrease_transitions",
    "seconds_desired_above_baseline",
    "recovered_to_stable_baseline",
    "recovery_utc",
    "recovery_after_workload_seconds",
    "desired_at_recovery_end",
    "ready_at_recovery_end",
    "at_baseline_at_recovery_end",
    "replica_file",
    "invalid_replica_rows_in_run",
]

with detail_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=detail_fields,
    )
    writer.writeheader()
    writer.writerows(detail_rows)

run_fields = [
    "run",
    "functions_observed",
    "functions_scaled",
    "functions_recovered",
    "functions_not_recovered",
    "run_recovered_by_recovery_end",
    "first_scale_out_from_start_seconds",
    "median_ready_after_scale_seconds",
    "overall_recovery_after_workload_seconds",
    "mean_function_recovery_after_workload_seconds",
    "invalid_replica_rows",
    "replica_file",
    "window_file",
]

with run_summary_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=run_fields,
    )
    writer.writeheader()
    writer.writerows(run_summary_rows)

report = [
    "===== DA-SACO SCALING AND RECOVERY RESULTS =====",
    f"RUNS_ANALYZED={len(run_summary_rows)}",
    f"FUNCTION_RUN_ROWS={len(detail_rows)}",
    f"FAILURE_COUNT={len(failures)}",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
    "===== PER-RUN RESULTS =====",
]

for row in run_summary_rows:
    report.append(
        "RUN="
        f"{row['run']}"
        f"|functions={row['functions_observed']}"
        f"|scaled={row['functions_scaled']}"
        f"|recovered={row['functions_recovered']}"
        f"|not_recovered={row['functions_not_recovered']}"
        f"|first_scale_s="
        f"{fmt(row['first_scale_out_from_start_seconds'])}"
        f"|ready_delay_median_s="
        f"{fmt(row['median_ready_after_scale_seconds'])}"
        f"|overall_recovery_s="
        f"{fmt(row['overall_recovery_after_workload_seconds'])}"
        f"|run_recovered="
        f"{row['run_recovered_by_recovery_end']}"
    )

report.extend([
    "",
    "===== SCALED FUNCTIONS =====",
])

for row in detail_rows:
    if row["scaled_out"] != "true":
        continue

    report.append(
        "FUNCTION="
        f"{row['run']}|{row['function']}"
        f"|baseline={row['baseline_desired']}"
        f"/{row['baseline_ready']}"
        f"|max={row['max_desired']}"
        f"/{row['max_ready']}"
        f"|scale_s="
        f"{fmt(row['first_scale_out_from_start_seconds'])}"
        f"|ready_delay_s="
        f"{fmt(row['ready_after_scale_seconds'])}"
        f"|above_baseline_s="
        f"{fmt(row['seconds_desired_above_baseline'])}"
        f"|recovery_s="
        f"{fmt(row['recovery_after_workload_seconds'])}"
        f"|recovered="
        f"{row['recovered_to_stable_baseline']}"
    )

for failure in failures:
    report.append(f"FAILURE={failure}")

run_gate = len(run_summary_rows) == 5
detail_gate = len(detail_rows) > 0
failure_gate = len(failures) == 0

final_gate = run_gate and detail_gate and failure_gate

report.extend([
    "",
    "===== FINAL DECISION =====",
    f"DA_SACO_5_RUN_GATE={'PASS' if run_gate else 'FAIL'}",
    f"FUNCTION_RESULTS_GATE={'PASS' if detail_gate else 'FAIL'}",
    f"SCALING_PARSE_GATE={'PASS' if failure_gate else 'FAIL'}",
    (
        "SCALING_RECOVERY_EXTRACTION_GATE="
        + ("PASS" if final_gate else "REVIEW")
    ),
    (
        "NEXT_ACTION="
        + (
            "EXTRACT_LATENCY_AND_RECONCILE_SUPI_OUTCOMES"
            if final_gate
            else "REVIEW_REPLICA_TIMESERIES_FAILURES"
        )
    ),
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"DETAIL_RESULTS={detail_path}",
    f"RUN_SUMMARY={run_summary_path}",
    f"REPORT={report_path}",
    f"MARKDOWN={markdown_path}",
])

report_path.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)

markdown = [
    "# DA-SACO Scaling and Recovery Results",
    "",
    (
        "Scaling was analyzed from each run's canonical "
        "`replica-timeseries.csv` between `RUN_START_UTC` and "
        "`RECOVERY_END_UTC`."
    ),
    "",
    "| Run | Functions observed | Functions scaled | Recovered | Not recovered | First scale-out (s) | Median replica-ready delay (s) | Overall recovery after workload (s) |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]

for row in run_summary_rows:
    markdown.append(
        "| "
        + row["run"]
        + " | "
        + str(row["functions_observed"])
        + " | "
        + str(row["functions_scaled"])
        + " | "
        + str(row["functions_recovered"])
        + " | "
        + str(row["functions_not_recovered"])
        + " | "
        + fmt(row["first_scale_out_from_start_seconds"])
        + " | "
        + fmt(row["median_ready_after_scale_seconds"])
        + " | "
        + fmt(row["overall_recovery_after_workload_seconds"])
        + " |"
    )

markdown.extend([
    "",
    "## Per-Function Scaling",
    "",
    "| Run | Function | Baseline desired/ready | Maximum desired/ready | First scale-out (s) | Ready delay (s) | Time above baseline (s) | Recovery after workload (s) | Recovered |",
    "|---|---|---:|---:|---:|---:|---:|---:|---|",
])

for row in detail_rows:
    if row["scaled_out"] != "true":
        continue

    markdown.append(
        "| "
        + row["run"]
        + " | "
        + row["function"]
        + " | "
        + str(row["baseline_desired"])
        + "/"
        + str(row["baseline_ready"])
        + " | "
        + str(row["max_desired"])
        + "/"
        + str(row["max_ready"])
        + " | "
        + fmt(row["first_scale_out_from_start_seconds"])
        + " | "
        + fmt(row["ready_after_scale_seconds"])
        + " | "
        + fmt(row["seconds_desired_above_baseline"])
        + " | "
        + fmt(row["recovery_after_workload_seconds"])
        + " | "
        + row["recovered_to_stable_baseline"]
        + " |"
    )

markdown.extend([
    "",
    "## Interpretation Rules",
    "",
    "- Baseline is the first valid desired/ready observation inside the canonical run window.",
    "- Scale-out occurs when desired replicas exceed the baseline desired value.",
    "- Replica-ready delay is measured from the first desired scale-out to the first ready count above baseline.",
    "- Recovery is accepted only when desired and ready return to baseline after workload completion and remain there through the remaining observations.",
    "- A missing recovery value means the function did not demonstrate stable baseline recovery before the canonical recovery window ended.",
    "- Source experiment files were read only and were not modified.",
    "",
])

markdown_path.write_text(
    "\n".join(markdown) + "\n",
    encoding="utf-8",
)

print("\n".join(report))

print()
print("===== DIRECT SCALING AND RECOVERY RESULTS =====")

for row in run_summary_rows:
    print(
        f"{row['run']}|"
        f"FUNCTIONS_SCALED={row['functions_scaled']}|"
        f"FUNCTIONS_RECOVERED={row['functions_recovered']}|"
        f"FUNCTIONS_NOT_RECOVERED={row['functions_not_recovered']}|"
        f"FIRST_SCALE_OUT_S="
        f"{fmt(row['first_scale_out_from_start_seconds'])}|"
        f"READY_DELAY_MEDIAN_S="
        f"{fmt(row['median_ready_after_scale_seconds'])}|"
        f"OVERALL_RECOVERY_S="
        f"{fmt(row['overall_recovery_after_workload_seconds'])}"
    )

raise SystemExit(0 if final_gate else 1)
