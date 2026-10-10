# Experiment Design

## Research objective

The experiment evaluates five control and scaling methods under a common
5G registration workload:

1. Static
2. AMF-HPA
3. Open5GLoS
4. Admission-only
5. DA-SACO

The comparison covers registration completion, post-security latency,
per-network-function resource pressure, aggregate resource cost, failure
causes, scaling usefulness, traffic distribution, and recovery.

## Workload

Each authoritative run used:

- 1000 planned UEs
- 120 ms inter-UE launch interval
- Registration-only workload
- No PDU-session workload
- Five runs per method
- 25 canonical runs in total

The planned SUPI universe for each run was:

- First SUPI: `imsi-208930000007001`
- Last SUPI: `imsi-208930000008000`
- Planned SUPIs: 1000

## Experimental methods

### B0: Static

The Static method used a fixed AMF topology without reactive scale-out.

### B1: AMF-HPA

The AMF-HPA method used:

- Initial AMF replicas: 1
- Minimum replicas: 1
- Maximum replicas: 5
- CPU target: 50%
- AMF-only horizontal scaling

All five accepted AMF-HPA runs reached five ready AMF replicas.
The four added replicas processed no visible SUPI traffic in the
authoritative per-AMF evidence.

### B2: Open5GLoS

The Open5GLoS method used a stable pre-provisioned topology:

- Desired AMFs: 3
- Ready AMFs: 3
- Available AMFs: 3

The topology remained 3/3/3 throughout all five accepted runs.
It is therefore interpreted as pre-provisioned multi-AMF capacity rather
than reactive scale-out during the workload.

### B3: Admission-only

The Admission-only method used:

- AMF topology: 1/1/1
- Admission enabled: true
- Admission rate: 6.25 UE/s
- Planned offered rate: 8.333333 UE/s
- Admission-to-offered ratio: 0.75
- Burst: 5

All 1000 planned devices were admitted. Most devices experienced a short
admission wait. No additional AMF capacity was created.

### R1: DA-SACO

DA-SACO used reactive multi-network-function scaling.

The observed scalable functions were:

- AMF
- AUSF
- PCF
- UDM
- UDR

Across five runs:

- Function-level scale-out cases: 16
- Cases reaching Ready: 16
- Cases processing measured workload: 15
- Confirmed idle cases: 1
- Useful scale-out rate: 93.75%
- Recovery to baseline: 16 of 16

The idle case was the additional AUSF replica in R4 during the
three-minute verification window.

## Canonical runs

Only runs selected by the unified manifest are authoritative.

Excluded, historical, repair, failed-gate, and diagnostic attempt
directories must not be interpreted as experiment repetitions.

The canonical run inventory is stored in:

- `manifests/UNIFIED-25-RUN-MANIFEST.csv`
- `manifests/UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv`

## Experimental-environment note

Baseline evidence originated from the previous experimental environment.

DA-SACO runs were executed in the current experimental environment except
R1, which originated from the previous environment.

This environment difference must be reported as a threat to validity and
must not be hidden when interpreting cross-method differences.
