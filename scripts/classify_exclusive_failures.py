import csv
import re
from collections import defaultdict
from pathlib import Path

output = (
    Path.home()
    / "PREVIOUS-VM-EVIDENCE"
    / "UNIFIED-25-RUN-ANALYSIS"
)

map_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv"
outcome_path = output / "UNIFIED-25-RUN-SUPI-OUTCOMES.csv"
summary_path = output / "UNIFIED-25-RUN-EXCLUSIVE-FAILURE-CAUSES.csv"
method_path = output / "UNIFIED-5-METHOD-EXCLUSIVE-FAILURE-CAUSES.csv"
report_path = output / "UNIFIED-EXCLUSIVE-FAILURE-CLASSIFICATION.txt"

supi_pattern = re.compile(
    r"(2089300000[0-9]{5})",
    re.IGNORECASE,
)

patterns = [
    (
        "EXPLICIT_REGISTRATION_REJECT",
        re.compile(
            r"(?:Send|Receive) Registration Reject",
            re.IGNORECASE,
        ),
    ),
    (
        "AUTHENTICATION_REJECT",
        re.compile(
            r"Authentication Reject",
            re.IGNORECASE,
        ),
    ),
    (
        "DEPENDENCY_FAILURE",
        re.compile(
            r"(?:context deadline exceeded|"
            r"connection refused|"
            r"NF discovery failure|"
            r"Authenticate Request Failed|"
            r"System failure)",
            re.IGNORECASE,
        ),
    ),
    (
        "SECURITY_MODE_TIMEOUT",
        re.compile(
            r"(?:T3560 expires|Security Mode timeout)",
            re.IGNORECASE,
        ),
    ),
    (
        "REGISTRATION_ACCEPT_TIMEOUT",
        re.compile(
            r"(?:T3550 expires|Registration Accept timeout)",
            re.IGNORECASE,
        ),
    ),
    (
        "WRONG_SECURITY_HEADER",
        re.compile(
            r"wrong security header",
            re.IGNORECASE,
        ),
    ),
    (
        "STATE_MISMATCH",
        re.compile(
            r"state mismatch",
            re.IGNORECASE,
        ),
    ),
]

with map_path.open(newline="") as stream:
    map_rows = list(csv.DictReader(stream))

with outcome_path.open(newline="") as stream:
    outcome_rows = list(csv.DictReader(stream))

amf_files = defaultdict(list)
run_names = {}

for row in map_rows:
    if row.get("evidence_type") != "AMF":
        continue

    key = (
        row["method"].strip(),
        row["run"].strip(),
    )

    amf_files[key].append(
        Path(row["canonical_file"])
    )

    run_names[key] = row.get("method_name", "").strip()

planned_supis = {
    str(value)
    for value in range(
        208930000007001,
        208930000008001,
    )
}

completed_supis = defaultdict(set)

for row in outcome_rows:
    if row.get("completed", "").lower() != "true":
        continue

    key = (
        row["method"].strip(),
        row["run"].strip(),
    )

    completed_supis[key].add(
        row["supi"].replace("imsi-", "").strip()
    )

failed_supis = {}

for key in sorted(amf_files):
    failed_supis[key] = (
        planned_supis
        - completed_supis.get(key, set())
    )

summary_rows = []
method_totals = defaultdict(
    lambda: defaultdict(int)
)

for key in sorted(failed_supis):
    method, run = key
    method_name = run_names.get(key, "")
    failed = failed_supis[key]

    evidence = {
        category: set()
        for category, _ in patterns
    }

    for path in amf_files.get(key, []):
        with path.open(
            encoding="utf-8",
            errors="replace",
        ) as stream:
            for line in stream:
                match = supi_pattern.search(line)

                if not match:
                    continue

                supi = match.group(1)

                if supi not in failed:
                    continue

                for category, pattern in patterns:
                    if pattern.search(line):
                        evidence[category].add(supi)

    unassigned = set(failed)
    exclusive = {}

    for category, _ in patterns:
        assigned = unassigned & evidence[category]
        exclusive[category] = assigned
        unassigned -= assigned

    exclusive["UNCLASSIFIED_NOT_COMPLETED"] = unassigned

    row = {
        "method": method,
        "method_name": method_name,
        "run": run,
        "not_completed_total": len(failed),
    }

    for category, _ in patterns:
        row[category.lower()] = len(
            exclusive[category]
        )

    row["unclassified_not_completed"] = len(
        unassigned
    )

    classified_total = sum(
        len(values)
        for values in exclusive.values()
    )

    row["exclusive_total"] = classified_total
    row["matches_not_completed"] = str(
        classified_total == len(failed)
    ).lower()

    summary_rows.append(row)

    method_key = (method, method_name)
    method_totals[method_key]["runs"] += 1
    method_totals[method_key]["not_completed"] += len(failed)

    for category, values in exclusive.items():
        method_totals[method_key][category] += len(values)

summary_fields = [
    "method",
    "method_name",
    "run",
    "not_completed_total",
    "explicit_registration_reject",
    "authentication_reject",
    "dependency_failure",
    "security_mode_timeout",
    "registration_accept_timeout",
    "wrong_security_header",
    "state_mismatch",
    "unclassified_not_completed",
    "exclusive_total",
    "matches_not_completed",
]

with summary_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=summary_fields,
    )
    writer.writeheader()
    writer.writerows(summary_rows)

method_rows = []

for key, values in sorted(method_totals.items()):
    method, method_name = key
    total = values["not_completed"]

    row = {
        "method": method,
        "method_name": method_name,
        "runs": values["runs"],
        "not_completed_total": total,
    }

    for category, _ in patterns:
        count = values[category]
        field = category.lower()
        row[field] = count
        row[field + "_percent"] = (
            count * 100.0 / total
            if total
            else 0.0
        )

    unclassified = values[
        "UNCLASSIFIED_NOT_COMPLETED"
    ]

    row["unclassified_not_completed"] = unclassified
    row["unclassified_not_completed_percent"] = (
        unclassified * 100.0 / total
        if total
        else 0.0
    )

    method_rows.append(row)

method_fields = list(method_rows[0])

with method_path.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=method_fields,
    )
    writer.writeheader()
    writer.writerows(method_rows)

gate = (
    len(summary_rows) == 25
    and all(
        row["matches_not_completed"] == "true"
        for row in summary_rows
    )
)

report = [
    "===== ALL-METHODS EXCLUSIVE FAILURE CLASSIFICATION =====",
    f"RUNS_CLASSIFIED={len(summary_rows)}",
    f"METHODS_CLASSIFIED={len(method_rows)}",
    "CLASSIFICATION_INPUT=CANONICAL_AMF_AND_RECONCILED_FAILED_SUPIS",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
    "===== METHOD RESULTS =====",
]

for row in method_rows:
    report.append(
        "METHOD="
        f"{row['method']}|{row['method_name']}"
        f"|not_completed={row['not_completed_total']}"
        f"|explicit_reject="
        f"{row['explicit_registration_reject']}"
        f"|authentication_reject="
        f"{row['authentication_reject']}"
        f"|dependency_failure="
        f"{row['dependency_failure']}"
        f"|security_mode_timeout="
        f"{row['security_mode_timeout']}"
        f"|registration_accept_timeout="
        f"{row['registration_accept_timeout']}"
        f"|wrong_security_header="
        f"{row['wrong_security_header']}"
        f"|state_mismatch={row['state_mismatch']}"
        f"|unclassified="
        f"{row['unclassified_not_completed']}"
    )

report.extend([
    "",
    (
        "EXCLUSIVE_FAILURE_CLASSIFICATION_GATE="
        + ("PASS" if gate else "REVIEW")
    ),
    (
        "NEXT_ACTION="
        + (
            "FINAL_STATISTICAL_COMPARISON"
            if gate
            else "REVIEW_FAILED_SUPI_RECONCILIATION"
        )
    ),
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"RUN_RESULTS={summary_path}",
    f"METHOD_RESULTS={method_path}",
    f"REPORT={report_path}",
])

report_path.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8",
)

print("\n".join(report))

raise SystemExit(0 if gate else 1)
