# Method Configurations

## Common Workload

All five methods used the same workload:

- Planned UEs: 1000
- First SUPI: `imsi-208930000007001`
- Last SUPI: `imsi-208930000008000`
- Inter-UE launch interval: 120 ms
- Workload: registration only
- PDU-session workload: disabled
- Accepted runs per method: 5
- Total canonical runs: 25

## B0: Static

The Static baseline used a fixed AMF topology without reactive scale-out.

Required evidence:

- AMF run-window logs
- Registration results
- Resource timeline
- Restart evidence
- Canonical workload boundaries

## B1: AMF-HPA

The AMF-HPA configuration used:

- Initial AMF replicas: 1
- Minimum AMF replicas: 1
- Maximum AMF replicas: 5
- CPU target: 50%
- Scaling target: AMF only

All five accepted runs reached five Ready AMF replicas.

The four additional AMFs processed no visible SUPIs or completed
registrations in the authoritative per-AMF evidence.

Required evidence:

- HPA configuration
- HPA timeline
- First scale-out timestamp
- First time all five replicas became Ready
- Per-AMF visible SUPI counts
- Per-AMF completion counts
- Resource and restart evidence

## B2: Open5GLoS

The accepted Open5GLoS runs maintained:

- Desired AMFs: 3
- Ready AMFs: 3
- Available AMFs: 3

The topology remained 3/3/3 throughout all five accepted runs.

This method is therefore interpreted as pre-provisioned multi-AMF
capacity, not reactive scale-out during the workload.

Required evidence:

- Open5GLoS readiness
- Managed AMF list
- Topology timeline
- Open5GLoS run-window log
- Resource timeline
- Per-AMF traffic evidence when available

## B3: Admission-only

The Admission-only configuration used:

- Admission mode: CUSTOM
- Admission enabled: true
- Admission rate: 6.25 UE/s
- Offered rate: 8.333333 UE/s
- Admission-to-offered ratio: 0.75
- Burst: 5
- AMF topology: 1/1/1

All 1000 planned UEs were admitted. Most UEs experienced a short wait,
but no additional AMF capacity was created.

Required evidence:

- Admission status before and after the run
- Admission configuration response
- Admitted and waited UE counts
- Total and mean wait times
- Topology timeline
- Registration outcomes

## DA-SACO

DA-SACO used reactive multi-network-function scaling.

Observed scalable functions:

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
- Cases returning to baseline: 16

The confirmed idle case was the additional AUSF replica in R4 during the
three-minute verification window.

Required evidence for each decision:

- Target network function
- Decision timestamp
- Original and desired replica counts
- New pod name
- Ready timestamp and delay
- Traffic-use verification
- Request-event count
- Unique identifiers when derivable
- Recovery timestamp
- Stable-baseline confirmation

If DA-SACO is rebuilt for additional experiments, testing starts directly
at 1000 UEs. The 10, 100, and 500 UE progression is not repeated unless a
separate validation objective requires it.

## Canonical-Run Rule

Only runs selected in the unified manifest are authoritative.

Excluded, invalid, diagnostic, repair, and historical attempt directories
must not be interpreted as accepted experiment repetitions.
