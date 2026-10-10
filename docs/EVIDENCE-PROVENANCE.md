# Evidence Provenance

## Authoritative Inventory

Authoritative runs and files are selected by:

- `manifests/UNIFIED-25-RUN-MANIFEST.csv`
- `manifests/UNIFIED-25-RUN-CANONICAL-EVIDENCE-MAP.csv`

## Repository Scope

This repository contains derived results, analysis scripts, documentation, manifests, and checksums.

Raw logs, credentials, packet captures, and VM images are not included.

## Superseded Evidence

Earlier DA-SACO R1 and R2 reports containing zero completions were superseded by canonical exact-window analysis.

## Latency Validation

Reconstructed latency matched the five existing Admission-only files:

- R1: 482/482
- R2: 318/318
- R3: 492/492
- R4: 501/501
- R5: 488/488

## Integrity

Source experiment files were not modified. Derived files were written separately and protected with SHA-256 checksums.
