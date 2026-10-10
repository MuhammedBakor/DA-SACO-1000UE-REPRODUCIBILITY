# Known Issues and Exclusions

## Excluded Attempts

Invalid, failed-gate, diagnostic, historical, repair, and explicitly excluded directories are not authoritative runs.

## Environment Difference

DA-SACO R2-R5 used the current environment. DA-SACO R1 and baseline evidence originated from the previous environment.

## DA-SACO Limitations

- Highest aggregate AMF memory P95
- Highest MongoDB memory P95
- Higher reported latency than Static, AMF-HPA, and Open5GLoS
- One idle additional AUSF replica in R4

## Evidence Limitations

- Five independent runs per method
- Non-significance does not prove equivalence
- Some Static and AMF-HPA latency runs had less than 100% coverage
- Unclassified failures are evidence gaps, not confirmed causes
- Latency excludes authentication and Security Mode before the start event

## Analysis Corrections

Pasted-command corruption, nanosecond timestamp parsing, excluded-directory selection, R2 pod-role assignment, and full-SUPI failure classification were corrected and subsequently validated.

## Upload Preparation

A VM network issue occurred after analysis and local commit creation. It did not modify experiment evidence or derived results.
