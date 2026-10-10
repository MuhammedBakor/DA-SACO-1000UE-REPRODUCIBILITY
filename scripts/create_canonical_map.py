import csv
import sys
from pathlib import Path

output = Path.home() / "PREVIOUS-VM-EVIDENCE/UNIFIED-25-RUN-ANALYSIS"
manifest_path = output / "UNIFIED-25-RUN-MANIFEST.csv"
csv_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv"
report_path = output / "UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP-REPORT.txt"

rows_out = []
results = []
report = [
    "===== UNIFIED 25-RUN CANONICAL EVIDENCE MAP =====",
    f"MANIFEST={manifest_path}",
    "MODE=READ_ONLY",
    "INVALID_ATTEMPT_SUBTREES_INCLUDED=false",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    "",
]

if not manifest_path.is_file():
    print("MANIFEST_GATE=FAIL")
    print(f"MISSING={manifest_path}")
    sys.exit(1)

with manifest_path.open(newline="") as stream:
    manifest = [
        row for row in csv.DictReader(stream)
        if row.get("selected", "").strip().lower() == "true"
    ]

def header(path):
    if not path or path.suffix.lower() != ".csv":
        return ""
    try:
        with path.open(
            encoding="utf-8",
            errors="replace",
            newline="",
        ) as stream:
            return stream.readline().strip()
    except OSError:
        return ""

def add(row, run_path, evidence_type, path, reason):
    if not path or not path.is_file():
        return

    rows_out.append({
        "method": row["method"].strip(),
        "method_name": row.get("method_name", "").strip(),
        "run": row["run"].strip(),
        "source": row.get("source", "").strip(),
        "run_path": str(run_path),
        "evidence_type": evidence_type,
        "canonical_file": str(path),
        "relative_file": str(path.relative_to(run_path)),
        "size_bytes": path.stat().st_size,
        "csv_header": header(path),
        "selection_reason": reason,
        "excluded_attempt_tree": "false",
    })

for row in manifest:
    method = row["method"].strip()
    run = row["run"].strip()
    run_path = Path(row["run_path"].strip())
    key = f"{method}|{run}"

    report.append(f"RUN={key}|{run_path}")

    path_ok = run_path.is_dir()
    amf_files = []

    if path_ok and method == "B0":
        candidate = run_path / "amf-run-window.log"
        if candidate.is_file():
            amf_files = [candidate]

    elif path_ok and method in {"B1", "B2"}:
        candidate = run_path / "amf-all-run-window.log"
        if candidate.is_file():
            amf_files = [candidate]

    elif path_ok and method == "B3":
        candidate = run_path / "amf-live.log"
        if candidate.is_file():
            amf_files = [candidate]

    elif path_ok and method == "R1":
        direct = run_path / "amf-live.log"
        pod_dir = run_path / "all-pod-logs"

        if direct.is_file():
            amf_files = [direct]
        elif pod_dir.is_dir():
            amf_files = sorted(
                path for path in pod_dir.glob("amf*.log")
                if path.is_file() and path.stat().st_size > 0
            )

    resource = run_path / "resource-timeseries.csv"
    packetrusher = run_path / "packetrusher.log"
    replica = run_path / "replica-timeseries.csv"
    run_window = run_path / "run-window.txt"
    start_utc = run_path / "start-utc.txt"
    end_utc = run_path / "end-utc.txt"

    amf_ok = bool(amf_files) and all(
        path.stat().st_size > 0 for path in amf_files
    )
    resource_ok = resource.is_file() and resource.stat().st_size > 0
    packetrusher_ok = (
        packetrusher.is_file()
        and packetrusher.stat().st_size > 0
    )

    if method == "R1":
        window_ok = run_window.is_file()
        replica_ok = replica.is_file() and replica.stat().st_size > 0
    else:
        window_ok = start_utc.is_file() and end_utc.is_file()
        replica_ok = True

    for path in amf_files:
        add(
            row,
            run_path,
            "AMF",
            path,
            "TOP_LEVEL_OR_CURRENT_ALL_POD_AMF_LOG",
        )

    add(
        row,
        run_path,
        "RESOURCE",
        resource,
        "TOP_LEVEL_RESOURCE_TIMESERIES",
    )
    add(
        row,
        run_path,
        "PACKETRUSHER",
        packetrusher,
        "TOP_LEVEL_WORKLOAD_LOG",
    )

    if method == "R1":
        add(
            row,
            run_path,
            "RUN_WINDOW",
            run_window,
            "TOP_LEVEL_RUN_WINDOW",
        )
        add(
            row,
            run_path,
            "REPLICA",
            replica,
            "TOP_LEVEL_REPLICA_TIMESERIES",
        )
    else:
        add(
            row,
            run_path,
            "START_UTC",
            start_utc,
            "TOP_LEVEL_START_BOUNDARY",
        )
        add(
            row,
            run_path,
            "END_UTC",
            end_utc,
            "TOP_LEVEL_END_BOUNDARY",
        )

    report.append(
        "GATES="
        f"PATH={'PASS' if path_ok else 'FAIL'}"
        f"|AMF={'PASS' if amf_ok else 'FAIL'}"
        f"|RESOURCE={'PASS' if resource_ok else 'FAIL'}"
        f"|PACKETRUSHER={'PASS' if packetrusher_ok else 'FAIL'}"
        f"|WINDOW={'PASS' if window_ok else 'FAIL'}"
        f"|REPLICA={'PASS' if replica_ok else 'FAIL'}"
    )

    if resource.is_file():
        report.append(f"RESOURCE_HEADER={header(resource)}")

    results.append({
        "path": path_ok,
        "amf": amf_ok,
        "resource": resource_ok,
        "packetrusher": packetrusher_ok,
        "window": window_ok,
        "replica": replica_ok,
    })

fields = [
    "method",
    "method_name",
    "run",
    "source",
    "run_path",
    "evidence_type",
    "canonical_file",
    "relative_file",
    "size_bytes",
    "csv_header",
    "selection_reason",
    "excluded_attempt_tree",
]

with csv_path.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows_out)

manifest_gate = len(manifest) == 25 and len(results) == 25
path_gate = manifest_gate and all(item["path"] for item in results)
amf_gate = manifest_gate and all(item["amf"] for item in results)
resource_gate = manifest_gate and all(
    item["resource"] for item in results
)
packetrusher_gate = manifest_gate and all(
    item["packetrusher"] for item in results
)
window_gate = manifest_gate and all(
    item["window"] for item in results
)
replica_gate = manifest_gate and all(
    item["replica"] for item in results
)

final_gate = all([
    manifest_gate,
    path_gate,
    amf_gate,
    resource_gate,
    packetrusher_gate,
    window_gate,
    replica_gate,
])

report.extend([
    "",
    "===== FINAL CANONICAL EVIDENCE DECISION =====",
    f"MANIFEST_25_RUN_GATE={'PASS' if manifest_gate else 'FAIL'}",
    f"ALL_RUN_PATHS_GATE={'PASS' if path_gate else 'FAIL'}",
    f"CANONICAL_AMF_GATE={'PASS' if amf_gate else 'FAIL'}",
    f"CANONICAL_RESOURCE_GATE={'PASS' if resource_gate else 'FAIL'}",
    (
        "CANONICAL_PACKETRUSHER_GATE="
        f"{'PASS' if packetrusher_gate else 'FAIL'}"
    ),
    f"CANONICAL_WINDOW_GATE={'PASS' if window_gate else 'FAIL'}",
    f"DA_SACO_REPLICA_GATE={'PASS' if replica_gate else 'FAIL'}",
    (
        "CANONICAL_EVIDENCE_GATE="
        f"{'PASS' if final_gate else 'REVIEW'}"
    ),
    "INVALID_ATTEMPT_SUBTREES_INCLUDED=false",
    (
        "NEXT_ACTION="
        + (
            "RUN_UNIFIED_METRIC_EXTRACTION_FROM_CANONICAL_MAP"
            if final_gate
            else "REVIEW_MISSING_CANONICAL_EVIDENCE"
        )
    ),
    "OLD_VM_START_REQUIRED_NOW=false",
    "SOURCE_EXPERIMENT_FILES_MODIFIED=false",
    f"CANONICAL_ROWS={len(rows_out)}",
    f"CSV={csv_path}",
    f"REPORT={report_path}",
])

report_path.write_text("\n".join(report) + "\n")
print("\n".join(report))

sys.exit(0 if final_gate else 1)
