# Experiment Execution Record

## Purpose

This document records the verified configuration used during the accepted 1000-UE experiments.

Creating this document does not start PacketRusher, DA-SACO, Open5GLoS, or any Kubernetes operation.

## Canonical DA-SACO Scripts

- R1: `R1/run-r1-final.sh`
- R2: `R2/run-r2-core.sh`
- R3: `R3/run-r3-core.sh`
- R4: `R4/run-r4-core.sh`
- R5: `R5/run-r5-core.sh`

Historical, invalid, diagnostic, and `before-*` files were not treated as canonical entry points.

## Verified Workload Configuration

- PacketRusher mode: `multi-ue`
- Planned UEs: 1000
- Inter-UE registration interval: 120 ms
- Time before deregistration: 0
- PDU sessions per UE: 0
- Maximum workload duration: 300 seconds
- Timeout signal: INT
- Forced termination delay: 20 seconds

## Verified Subscriber Range

- First SUPI: `imsi-208930000007001`
- Last SUPI: `imsi-208930000008000`
- Planned subscribers: 1000
- Required preparation result: `SUBSCRIBER_RESET_GATE=PASS`

## Verified DA-SACO Configuration

- Controller loop: `parallel_controller_loop.sh`
- DA-SACO active flag: `DASACO_ACTIVE=1`
- Controller decision interval: 5 seconds
- Resource sampling interval: 2 seconds

## Verified R2 Files

- PacketRusher binary: `R2/packetrusher-dasaco`
- PacketRusher configuration: `R2/dasaco-r2.yml`

Equivalent run-specific files were used for the other accepted DA-SACO runs.

## Preserved Run Boundaries

- `RUN_START_UTC`
- `WORKLOAD_END_UTC`
- `RECOVERY_END_UTC`

Recovery monitoring continued after the PacketRusher process ended.

## Integrity Statement

This is a historical execution record. No experiment was rerun while producing this document.
