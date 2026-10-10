# Reproduction Guide

## Scope

This guide describes the requirements for reproducing the unified 1000-UE experiment. It does not execute the experiment.

## Reference Software

- DA-SACO repository commit: `7868d1d483a69ca8727e588b3182e1cd8ed074e4`
- PacketRusher commit: `194ae987ee2bacfae2cf57d435b475e54076679e`
- free5GC Helm commit: `6f67ec11512e8c6b4eb6b3237f46e71fec5bdda2`
- Open5GLoS commit: `55994ae45ac66e00722460fad4902a481dac6f68`
- free5GC images: version `v4.2.3`

## Environment

Use the specifications documented in:

- `docs/CURRENT-ENVIRONMENT-SPECIFICATIONS.md`
- `docs/ENVIRONMENT-AND-DEPENDENCIES.md`

Record all software versions, image digests, VM resources, Kubernetes versions, and resource limits before a new experiment series.

## Subscriber Preparation

Prepare exactly 1000 subscribers:

- First SUPI: `imsi-208930000007001`
- Last SUPI: `imsi-208930000008000`
- Planned subscribers: 1000

Before every accepted run, verify that all planned subscriber records exist and that no planned SUPI is missing.

The preparation gate must report:

`SUBSCRIBER_RESET_GATE=PASS`

Authentication values must be consistent between PacketRusher and free5GC. Secrets and subscriber credentials are not published in this derived-results repository.

## Common Workload

- PacketRusher mode: `multi-ue`
- Number of UEs: 1000
- Inter-UE registration interval: 120 ms
- Time before deregistration: 0
- PDU sessions per UE: 0
- Maximum workload duration: 300 seconds

## Per-Method Preparation

Use `docs/METHOD-CONFIGURATIONS.md` to configure Static, AMF-HPA, Open5GLoS, Admission-only, or DA-SACO.

Start each accepted run from its documented baseline topology. Do not reuse resource or log files from an earlier run.

## Evidence Collection

Start evidence collection before the workload and preserve:

- UTC run boundaries
- AMF logs from every replica
- PacketRusher output
- CPU and memory timeline
- Replica or topology timeline
- Controller decisions
- Kubernetes events and restart counts
- Scale-out, readiness, traffic-use, scale-in, and recovery evidence

Continue evidence collection after PacketRusher exits until recovery is complete.

## Acceptance Rules

Accept a run only when the subscriber gate passes, workload boundaries exist, required evidence is readable, and the intended method remains valid.

Preserve excluded attempts with an explicit reason. Do not silently delete or replace them.

## Required Repetitions

- Five accepted runs per method
- Five methods
- Twenty-five canonical runs

If DA-SACO is rebuilt, begin validation directly with 1000 UEs unless a separate objective requires lower loads.

## Analysis

After completing the runs, follow `docs/ANALYSIS-PIPELINE.md`.

Raw experiment evidence must remain read-only. Write all derived outputs to a separate analysis directory.
