# Environment and Dependencies

## Main platform components

The experimental system used the following component categories:

- Ubuntu virtual machine
- Kubernetes
- free5GC
- PacketRusher
- Open5GLoS
- MongoDB
- Python 3
- Bash
- Git

The repository contains derived results and analysis scripts. Raw
experiment logs, packet captures, credentials, and VM images are not
included.

## 5G network functions observed

The analysis detected the following components:

- AMF
- AUSF
- NRF
- NSSF
- PCF
- SMF
- UDM
- UDR
- UPF when present
- MongoDB
- WebUI
- Open5GLoS

## Python requirements

The analysis scripts use Python standard-library modules including:

- csv
- collections
- datetime
- math
- pathlib
- re
- statistics

The statistical comparison additionally requires SciPy.

## Units

- CPU: millicores
- Memory: MiB
- Latency: milliseconds
- Percentiles: Hyndman and Fan Type 7

## Clock and timestamps

Canonical AMF evidence uses UTC timestamps.

Nanosecond timestamps are normalized to microsecond precision when parsed
with Python datetime. This normalization does not alter the original
evidence files.

## Environment capture required for a fresh rerun

Before starting a new experiment series, record:

- Ubuntu version
- Kernel version
- Kubernetes version
- kubectl version
- Container runtime version
- free5GC image tags
- PacketRusher version or commit
- Open5GLoS version or commit
- DA-SACO version or commit
- Helm release values
- CPU and memory limits and requests
- VM vCPU count
- VM memory
- Storage type and capacity
- Network-adapter mode
- Time synchronization status
- Python version
- SciPy version

The current derived package does not claim exact values for items that
were not preserved in the canonical evidence.
