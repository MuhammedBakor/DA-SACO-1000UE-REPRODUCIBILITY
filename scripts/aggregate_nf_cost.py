import csv
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

source_map = Path(sys.argv[1])
run_output = Path(sys.argv[2])
method_output = Path(sys.argv[3])

def cpu_m(value):
    value = str(value or "").strip().lower()

    if value.endswith("n"):
        return float(value[:-1]) / 1000000
    if value.endswith("u"):
        return float(value[:-1]) / 1000
    if value.endswith("m"):
        return float(value[:-1])

    return float(value) * 1000

def mem_mib(value):
    value = str(value or "").strip()
    match = re.fullmatch(
        r"([0-9]+(?:[.][0-9]+)?)([A-Za-z]+)?",
        value,
    )

    if not match:
        raise ValueError(value)

    amount = float(match.group(1))
    unit = (match.group(2) or "").lower()

    factors = {
        "": 1 / 1048576,
        "b": 1 / 1048576,
        "ki": 1 / 1024,
        "kib": 1 / 1024,
        "mi": 1,
        "mib": 1,
        "gi": 1024,
        "gib": 1024,
    }

    return amount * factors[unit]

def nf_name(pod):
    pod = pod.lower()

    names = [
        ("open5glos", "Open5GLoS"),
        ("mongodb", "MongoDB"),
        ("ausf", "AUSF"),
        ("amf", "AMF"),
        ("nrf", "NRF"),
        ("nssf", "NSSF"),
        ("pcf", "PCF"),
        ("smf", "SMF"),
        ("upf", "UPF"),
        ("udm", "UDM"),
        ("udr", "UDR"),
        ("webui", "WebUI"),
    ]

    for token, name in names:
        if token in pod:
            return name

    return "OTHER"

def pctl(values, probability):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower

    return (
        values[lower] * (1 - weight)
        + values[upper] * weight
    )

def stats(values):
    return {
        "samples": len(values),
        "mean": statistics.fmean(values),
        "p95": pctl(values, 0.95),
        "p99": pctl(values, 0.99),
        "peak": max(values),
    }

with source_map.open(newline="") as stream:
    evidence = [
        row for row in csv.DictReader(stream)
        if row.get("evidence_type") == "RESOURCE"
    ]

run_rows = []
failures = []

for item in evidence:
    path = Path(item["canonical_file"])
    totals = defaultdict(
        lambda: {"cpu": 0.0, "mem": 0.0, "pods": set()}
    )

    try:
        with path.open(newline="") as stream:
            reader = csv.DictReader(stream)
            time_field = (
                "timestamp_utc"
                if "timestamp_utc" in reader.fieldnames
                else "timestamp"
            )

            for row in reader:
                timestamp = row[time_field].strip()
                pod = row["pod"].strip()
                function = nf_name(pod)
                key = (timestamp, function)

                totals[key]["cpu"] += cpu_m(row["cpu"])
                totals[key]["mem"] += mem_mib(row["memory"])
                totals[key]["pods"].add(pod)

    except Exception as error:
        failures.append(
            item["method"]
            + "|"
            + item["run"]
            + "|"
            + str(error)
        )
        continue

    function_values = defaultdict(
        lambda: {"cpu": [], "mem": [], "replicas": []}
    )

    for (_, function), values in totals.items():
        function_values[function]["cpu"].append(values["cpu"])
        function_values[function]["mem"].append(values["mem"])
        function_values[function]["replicas"].append(
            len(values["pods"])
        )

    for function, values in sorted(function_values.items()):
        cpu = stats(values["cpu"])
        mem = stats(values["mem"])

        run_rows.append({
            "method": item["method"],
            "method_name": item["method_name"],
            "run": item["run"],
            "function": function,
            "timestamp_samples": cpu["samples"],
            "aggregate_cpu_mean_m": cpu["mean"],
            "aggregate_cpu_p95_m": cpu["p95"],
            "aggregate_cpu_p99_m": cpu["p99"],
            "aggregate_cpu_peak_m": cpu["peak"],
            "aggregate_memory_mean_mib": mem["mean"],
            "aggregate_memory_p95_mib": mem["p95"],
            "aggregate_memory_p99_mib": mem["p99"],
            "aggregate_memory_peak_mib": mem["peak"],
            "replicas_mean": statistics.fmean(
                values["replicas"]
            ),
            "replicas_max": max(values["replicas"]),
            "source": str(path),
        })

run_fields = list(run_rows[0])

with run_output.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=run_fields)
    writer.writeheader()
    writer.writerows(run_rows)

grouped = defaultdict(list)

for row in run_rows:
    grouped[
        (
            row["method"],
            row["method_name"],
            row["function"],
        )
    ].append(row)

method_rows = []

for key, rows in sorted(grouped.items()):
    method, method_name, function = key

    def average(field):
        return statistics.fmean(
            float(row[field]) for row in rows
        )

    method_rows.append({
        "method": method,
        "method_name": method_name,
        "function": function,
        "runs_observed": len(rows),
        "aggregate_cpu_mean_m": average(
            "aggregate_cpu_mean_m"
        ),
        "aggregate_cpu_p95_m": average(
            "aggregate_cpu_p95_m"
        ),
        "aggregate_cpu_p99_m": average(
            "aggregate_cpu_p99_m"
        ),
        "aggregate_cpu_peak_m": max(
            float(row["aggregate_cpu_peak_m"])
            for row in rows
        ),
        "aggregate_memory_mean_mib": average(
            "aggregate_memory_mean_mib"
        ),
        "aggregate_memory_p95_mib": average(
            "aggregate_memory_p95_mib"
        ),
        "aggregate_memory_p99_mib": average(
            "aggregate_memory_p99_mib"
        ),
        "aggregate_memory_peak_mib": max(
            float(row["aggregate_memory_peak_mib"])
            for row in rows
        ),
        "replicas_mean": average("replicas_mean"),
        "replicas_max": max(
            float(row["replicas_max"])
            for row in rows
        ),
    })

method_fields = list(method_rows[0])

with method_output.open("w", newline="") as stream:
    writer = csv.DictWriter(
        stream,
        fieldnames=method_fields,
    )
    writer.writeheader()
    writer.writerows(method_rows)

print("===== AGGREGATE NF COST EXTRACTION =====")
print(f"RESOURCE_FILES_ANALYZED={len(evidence)}")
print(f"RUN_FUNCTION_ROWS={len(run_rows)}")
print(f"METHOD_FUNCTION_ROWS={len(method_rows)}")
print(f"FAILURE_COUNT={len(failures)}")

for failure in failures:
    print(f"FAILURE={failure}")

gate = len(evidence) == 25 and not failures

print(
    "AGGREGATE_NF_COST_GATE="
    + ("PASS" if gate else "REVIEW")
)
print(f"RUN_RESULTS={run_output}")
print(f"METHOD_RESULTS={method_output}")
print("SOURCE_EXPERIMENT_FILES_MODIFIED=false")

raise SystemExit(0 if gate else 1)
