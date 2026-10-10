import csv
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

output = (
    Path.home()
    / "PREVIOUS-VM-EVIDENCE"
    / "UNIFIED-25-RUN-ANALYSIS"
)

map_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv"
summary_path = output / "UNIFIED-25-RUN-SUPI-OUTCOME-SUMMARY.csv"
detail_path = output / "UNIFIED-25-RUN-SUPI-OUTCOMES.csv"
report_path = output / "UNIFIED-SUPI-OUTCOME-RECONCILIATION.txt"

TARGET_UES = 1000

timestamp_pattern = re.compile(
    r"([0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:[.][0-9]+)?Z)"
)

supi_pattern = re.compile(
    r"(2089300000[0-9]{5})",
    re.IGNORECASE,
)

complete_pattern = re.compile(
    r"Handle Registration Complete",
    re.IGNORECASE,
)

reject_pattern = re.compile(
    r"(?:Send|Receive) Registration Reject",
    re.IGNORECASE,
)

def parse_time(text):
    match = timestamp_pattern.search(text)

    if not match:
        return None

    value = match.group(1)
    main = value[:-1]

    if "." in main:
        whole, fraction = main.split(".", 1)
        fraction = (fraction + "000000")[:6]
        main = whole + "." + fraction

    try:
        return datetime.fromisoformat(
            main + "+00:00"
        ).astimezone(timezone.utc)
    except ValueError:
        return None

def boundary(value):
    return datetime.fromisoformat(
        value.strip().replace("Z", "+00:00")
    ).astimezone(timezone.utc)

def run_window(rows, method):
    by_type = defaultdict(list)

    for row in rows:
        by_type[row["evidence_type"]].append(
            Path(row["canonical_file"])
        )

    if method == "R1":
        values = {}

        for line in by_type["RUN_WINDOW"][0].read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()

        return (
            boundary(values["RUN_START_UTC"]),
            boundary(values["WORKLOAD_END_UTC"]),
            by_type["AMF"],
        )

    start = boundary(
        by_type["START_UTC"][0].read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    end = boundary(
        by_type["END_UTC"][0].read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    return start, end, by_type["AMF"]

with map_path.open(newline="") as stream:
    map_rows = list(csv.DictReader(stream))

grouped = defaultdict(list)

for row in map_rows:
    key = (
        row["method"].strip(),
        row["method_name"].strip(),
        row["run"].strip(),
        row["run_path"].strip(),
    )
    grouped[key].append(row)

summary_rows = []
detail_rows = []

for key, rows in sorted(grouped.items()):
    method, method_name, run, run_path = key
    start, end, amf_files = run_window(rows, method)

    completed = set()
    rejected = set()

    for amf_file in amf_files:
        with amf_file.open(
            encoding="utf-8",
            errors="replace",
        ) as stream:
            for line in stream:
                is_complete = bool(complete_pattern.search(line))
                is_reject = bool(reject_pattern.search(line))

                if not is_complete and not is_reject:
                    continue

                timestamp = parse_time(line)

                if timestamp is None:
                    continue

                if timestamp < start or timestamp > end:
                    continue

                match = supi_pattern.search(line)

                if not match:
                    continue

                supi = match.group(1)

                if is_complete:
                    completed.add(supi)

                if is_reject:
                    rejected.add(supi)

    rejected_then_completed = completed & rejected
    completed_only = completed - rejected
    rejected_only = rejected - completed
    not_completed = TARGET_UES - len(completed)

    for supi in sorted(completed | rejected):
        if supi in rejected_then_completed:
            outcome = "REJECTED_THEN_COMPLETED"
        elif supi in completed_only:
            outcome = "COMPLETED_ONLY"
        else:
            outcome = "REJECTED_ONLY"

        detail_rows.append({
            "method": method,
            "method_name": method_name,
            "run": run,
            "supi": supi,
            "completed": str(supi in completed).lower(),
            "rejected": str(supi in rejected).lower(),
            "outcome": outcome,
            "run_path": run_path,
        })

    summary_rows.append({
        "method": method,
        "method_name": method_name,
        "run": run,
        "target_ues": TARGET_UES,
        "completed_unique_supis": len(completed),
        "rejected_unique_supis": len(rejected),
        "completed_only": len(completed_only),
        "rejected_then_completed": len(
            rejected_then_completed
        ),
        "rejected_only": len(rejected_only),
        "not_completed_against_target": not_completed,
        "success_rate_percent": (
            len(completed) * 100.0 / TARGET_UES
        ),
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "run_path": run_path,
    })

summary_fields = [
    "method",
    "method_name",
    "run",
    "target_ues",
    "completed_unique_supis",
    "rejected_unique_supis",
    "completed_only",
    "rejected_then_completed",
    "rejected_only",
    "not_completed_against_target",
    "success_rate_percent",
    "window_start_utc",
    "window_end_utc",
    "run_path",
]

with summary_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=summary_fields,
    )
    writer.writeheader()
    writer.writerows(summary_rows)

detail_fields = [
    "method",
    "method_name",
    "run",
    "supi",
    "completed",
    "rejected",
    "outcome",
    "run_path",
]

with detail_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=detail_fields,
    )
    writer.writeheader()
    writer.writerows(detail_rows)

gate = len(summary_rows) == 25

report = [
    "===== UNIFIED SUPI OUTCOME RECONCILIATION =====",
    f"RUNS_RECONCILED={len(summary_rows)}",
    f"SUPI_OUTCOME_ROWS={len(detail_rows)}",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
]

for row in summary_rows:
    report.append(
        "RUN="
        f"{row['method']}|{row['method_name']}|{row['run']}"
        f"|completed={row['completed_unique_supis']}"
        f"|completed_only={row['completed_only']}"
        f"|rejected_then_completed="
        f"{row['rejected_then_completed']}"
        f"|rejected_only={row['rejected_only']}"
        f"|not_completed="
        f"{row['not_completed_against_target']}"
    )

report.extend([
    "",
    f"SUPI_RECONCILIATION_GATE={'PASS' if gate else 'FAIL'}",
    (
        "NEXT_ACTION="
        + (
            "EXTRACT_VALIDATED_REGISTRATION_LATENCY"
            if gate
            else "REVIEW_RECONCILIATION_INPUTS"
        )
    ),
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"SUMMARY={summary_path}",
    f"DETAIL={detail_path}",
    f"REPORT={report_path}",
])

report_path.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)

print("\n".join(report))

raise SystemExit(0 if gate else 1)
