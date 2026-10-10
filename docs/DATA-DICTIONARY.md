# Data Dictionary

## Experiment identifiers

- `method`: experimental method identifier.
- `method_name`: human-readable method name.
- `run`: run identifier.
- `target_ues`: planned UE count, equal to 1000 per run.

## Registration outcomes

- `registration_complete_unique_supis`: unique planned SUPIs with `Handle Registration Complete`.
- `registration_reject_unique_supis`: unique SUPIs with an explicit registration-reject event.
- `not_completed_against_target`: planned UEs without a canonical completion event.
- `success_rate_percent`: completed planned SUPIs divided by 1000.

## Resource metrics

- CPU unit: millicores.
- Memory unit: MiB.
- `NF-PRESSURE` files describe per-pod resource observations.
- `AGGREGATE-NF-COST` files sum all pods of the function at each timestamp.
- P95 and P99 use Hyndman and Fan Type 7.

## Latency

- Start event: `Handle InitialRegistration`.
- End event: `Handle Registration Complete`.
- Unit: milliseconds.
- Metric name: post-security registration-completion latency.
- The metric is not end-to-end registration latency.
- Authentication and security-mode processing before the start event are excluded.

## Failure classification

Each non-completed planned SUPI is assigned to at most one category using the documented classification priority. Unclassified cases indicate that no attributable SUPI-bearing cause was found in the canonical AMF evidence.

## Path notation

`<LOCAL_HOME>` represents the local user home directory containing the original experiment evidence. Raw evidence is not included in this repository.
