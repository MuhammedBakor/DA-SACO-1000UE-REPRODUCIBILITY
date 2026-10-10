import csv
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

output = (
    Path.home()
    / "PREVIOUS-VM-EVIDENCE"
    / "UNIFIED-25-RUN-ANALYSIS"
)

map_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv"
csv_path = output / "UNIFIED-25-RUN-AMF-EVENT-AUDIT.csv"
report_path = output / "UNIFIED-25-RUN-AMF-EVENT-AUDIT.txt"

timestamp_pattern = re.compile(
    r"([0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:[.][0-9]+)?Z)"
)

supi_pattern = re.compile(
    r"(2089300000\d{5})",
    re.IGNORECASE,
)

event_patterns = {
    "initial_ue_message": re.compile(
        r"Handle InitialUEMessage",
        re.IGNORECASE,
    ),
    "initial_registration": re.compile(
        r"Handle Initial Registration",
        re.IGNORECASE,
    ),
    "registration_accept": re.compile(
        r"(?:Send|Handle) Registration Accept",
        re.IGNORECASE,
    ),
    "registration_complete": re.compile(
        r"Handle Registration Complete",
        re.IGNORECASE,
    ),
    "registration_reject": re.compile(
        r"(?:Send|Receive) Registration Reject",
        re.IGNORECASE,
    ),
}

def parse_time(text):
    match = timestamp_pattern.search(text)

    if not match:
        return None

    value = match.group(1)

    try:
        main = value[:-1]

        if "." in main:
            whole, fraction = main.split(".", 1)
            fraction = (fraction + "000000")[:6]
            main = whole + "." + fraction

        return datetime.fromisoformat(
            main + "+00:00"
        ).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None

def parse_boundary(text):
    value = text.strip()

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)

if not map_path.is_file():
    print("CANONICAL_MAP_GATE=FAIL")
    print(f"MISSING={map_path}")
    sys.exit(1)

with map_path.open(newline="") as stream:
    canonical_rows = list(csv.DictReader(stream))

grouped = defaultdict(list)

for row in canonical_rows:
    key = (
        row.get("method", "").strip(),
        row.get("method_name", "").strip(),
        row.get("run", "").strip(),
        row.get("run_path", "").strip(),
    )
    grouped[key].append(row)

audit_rows = []
report = [
    "===== UNIFIED 25-RUN AMF EVENT AUDIT =====",
    f"CANONICAL_MAP={map_path}",
    "FILTER_MODE=REGISTRATION_WORKLOAD_WINDOW",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
]

for key, rows in sorted(grouped.items()):
    method, method_name, run, run_path_text = key
    run_path = Path(run_path_text)

    by_type = defaultdict(list)

    for row in rows:
        by_type[row.get("evidence_type", "")].append(
            Path(row["canonical_file"])
        )

    if method == "R1":
        window_file = by_type["RUN_WINDOW"][0]
        values = {}

        for line in window_file.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            if "=" in line:
                name, value = line.split("=", 1)
                values[name.strip()] = value.strip()

        start = parse_boundary(values["RUN_START_UTC"])
        end = parse_boundary(values["WORKLOAD_END_UTC"])
        boundary_source = "RUN_START_UTC_TO_WORKLOAD_END_UTC"
    else:
        start_file = by_type["START_UTC"][0]
        end_file = by_type["END_UTC"][0]

        start = parse_boundary(
            start_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )
        end = parse_boundary(
            end_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )
        boundary_source = "START_UTC_TO_END_UTC"

    raw_counts = {
        name: 0
        for name in event_patterns
    }

    supi_sets = {
        name: set()
        for name in event_patterns
    }

    timestamped_lines = 0
    in_window_lines = 0
    unparseable_event_lines = 0
    amf_files = by_type["AMF"]

    for amf_file in amf_files:
        with amf_file.open(
            encoding="utf-8",
            errors="replace",
        ) as stream:
            for line in stream:
                matched_events = [
                    name
                    for name, pattern in event_patterns.items()
                    if pattern.search(line)
                ]

                if not matched_events:
                    continue

                timestamp = parse_time(line)

                if timestamp is None:
                    unparseable_event_lines += 1
                    continue

                timestamped_lines += 1

                if timestamp < start or timestamp > end:
                    continue

                in_window_lines += 1
                supi_match = supi_pattern.search(line)
                supi = (
                    supi_match.group(1)
                    if supi_match
                    else ""
                )

                for event_name in matched_events:
                    raw_counts[event_name] += 1

                    if supi:
                        supi_sets[event_name].add(supi)

    row = {
        "method": method,
        "method_name": method_name,
        "run": run,
        "run_path": str(run_path),
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "boundary_source": boundary_source,
        "amf_file_count": len(amf_files),
        "timestamped_event_lines": timestamped_lines,
        "in_window_event_lines": in_window_lines,
        "unparseable_event_lines": unparseable_event_lines,
    }

    for event_name in event_patterns:
        row[f"{event_name}_raw"] = raw_counts[event_name]
        row[f"{event_name}_unique_supis"] = len(
            supi_sets[event_name]
        )

    audit_rows.append(row)

    report.append(
        "RUN="
        f"{method}|{method_name}|{run}"
        f"|start={start.isoformat()}"
        f"|end={end.isoformat()}"
    )
    report.append(
        "EVENTS="
        f"initial_ue_message={raw_counts['initial_ue_message']}"
        f"/{len(supi_sets['initial_ue_message'])}"
        f"|initial_registration="
        f"{raw_counts['initial_registration']}"
        f"/{len(supi_sets['initial_registration'])}"
        f"|accept={raw_counts['registration_accept']}"
        f"/{len(supi_sets['registration_accept'])}"
        f"|complete={raw_counts['registration_complete']}"
        f"/{len(supi_sets['registration_complete'])}"
        f"|reject={raw_counts['registration_reject']}"
        f"/{len(supi_sets['registration_reject'])}"
    )
    report.append(
        "PARSE="
        f"timestamped={timestamped_lines}"
        f"|in_window={in_window_lines}"
        f"|unparseable={unparseable_event_lines}"
    )
    report.append("")

fieldnames = [
    "method",
    "method_name",
    "run",
    "run_path",
    "window_start_utc",
    "window_end_utc",
    "boundary_source",
    "amf_file_count",
    "timestamped_event_lines",
    "in_window_event_lines",
    "unparseable_event_lines",
]

for event_name in event_patterns:
    fieldnames.extend([
        f"{event_name}_raw",
        f"{event_name}_unique_supis",
    ])

with csv_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
    )
    writer.writeheader()
    writer.writerows(audit_rows)

run_gate = len(audit_rows) == 25

window_event_gate = (
    run_gate
    and all(
        int(row["in_window_event_lines"]) > 0
        for row in audit_rows
    )
)

complete_coverage = sum(
    1
    for row in audit_rows
    if int(row["registration_complete_raw"]) > 0
)

report.extend([
    "===== FINAL AMF EVENT AUDIT DECISION =====",
    f"AUDITED_RUNS={len(audit_rows)}",
    f"RUN_25_GATE={'PASS' if run_gate else 'FAIL'}",
    (
        "ALL_WINDOWS_HAVE_AMF_EVENTS_GATE="
        f"{'PASS' if window_event_gate else 'REVIEW'}"
    ),
    f"COMPLETE_EVENT_COVERAGE={complete_coverage}/25",
    (
        "NEXT_ACTION="
        + (
            "REVIEW_EVENT_AUDIT_THEN_EXTRACT_METRICS"
            if run_gate and window_event_gate
            else "REVIEW_EMPTY_OR_UNPARSEABLE_WINDOWS"
        )
    ),
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"CSV={csv_path}",
    f"REPORT={report_path}",
])

report_path.write_text("\n".join(report) + "\n")
print("\n".join(report))

sys.exit(0 if run_gate and window_event_gate else 1)
