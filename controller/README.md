# DA-SACO Controller Source

This directory contains the DA-SACO controller source and configuration
artifacts used by the evaluated system.

DA-SACO implements an observe-localize-decide-execute-verify-recover
control loop for registration bursts. The controller monitors the
registration dependency path, selectively scales constrained network
functions, coordinates temporary admission protection, verifies
Kubernetes readiness and measured workload use, and applies guarded
recovery to the documented baseline.

## Scope

The selective scaling scope includes:

- AMF
- AUSF
- PCF
- UDM
- UDR

NRF and MongoDB are monitored as registration-support dependencies but
are not selectively scaled in the evaluated configuration.

## Timing

- Resource sampling interval: 2 seconds
- Controller decision interval: 5 seconds

## Repository Structure

The `controller` directory contains source and configuration artifacts.
The `scripts` directory at the repository root contains the separate
analysis and evidence-extraction pipeline.

Operational logs, credentials, kubeconfig files, raw subscriber
evidence, and runtime secrets are intentionally excluded.
