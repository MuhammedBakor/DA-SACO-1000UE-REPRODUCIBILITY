# Current Environment Specifications

## Scope

This document records the current experimental environment.

DA-SACO R2-R5 were executed in this environment.

DA-SACO R1 and the baseline-method evidence originated from the previous
environment. Their exact environment values must be documented separately
from preserved evidence and must not be assumed to match this snapshot.

## Ubuntu Virtual Machine

| Property | Value |
|---|---|
| Operating system | Ubuntu 22.04.5 LTS |
| Kernel | 6.8.0-136-generic |
| Architecture | x86_64 |
| Hypervisor | VMware |
| Virtualization type | Full virtualization |
| Virtual CPUs | 6 |
| Host CPU model | AMD Ryzen 7 8845HS with Radeon 780M Graphics |
| VM memory | 10 GiB |
| Swap | 2 GiB |
| Virtual disk | 100 GiB |
| Root filesystem | 99.5 GiB ext4 |
| EFI partition | 513 MiB vfat |

The VM is currently stored on an external drive. This storage location
must be recorded when reproducing the environment because storage and
connection behavior may affect operational reliability.

## Development Tools

| Component | Version |
|---|---|
| Python | 3.10.12 |
| Git | 2.34.1 |
| Go | 1.24.1 |
| Helm | 3.21.3 |
| kubectl client | 1.36.0 |
| Kustomize | 5.8.1 |
| Docker command | 29.7.2 |
| Host containerd command | 2.3.3 |
| SciPy inside the VM | Not available during documentation capture |
| crictl | Not available |

The final statistical values are preserved as derived results. A fresh
reproduction of the statistical workflow requires SciPy.

## Kubernetes Cluster

| Property | Value |
|---|---|
| Kubernetes server | 1.36.1 |
| Control-plane node | dasaco-control-plane |
| Kubelet | 1.36.1 |
| Node operating system | Debian GNU/Linux 13 (trixie) |
| Node architecture | amd64 |
| Node CPU capacity | 6 |
| Node memory capacity | 10711516 Ki |
| Node container runtime | containerd 2.3.1 |

The Kubernetes node environment is distinct from the Ubuntu VM operating
system because the Kubernetes node runs inside the containerized cluster.

## Main Workload Images

| Component | Container image |
|---|---|
| AMF | free5gc/amf:v4.2.3 |
| AUSF | free5gc/ausf:v4.2.3 |
| CHF | free5gc/chf:v4.2.3 |
| NEF | free5gc/nef:v4.2.3 |
| NRF | free5gc/nrf:v4.2.3 |
| NSSF | free5gc/nssf:v4.2.3 |
| PCF | free5gc/pcf:v4.2.3 |
| SMF | free5gc/smf:v4.2.3 |
| UDM | free5gc/udm:v4.2.3 |
| UDR | free5gc/udr:v4.2.3 |
| WebUI | free5gc/webui:v4.2.3 |
| MongoDB | docker.io/bitnamilegacy/mongodb:7.0.9-debian-12-r4 |
| DBPython | towards5gs/free5gc-dbpython:latest |
| Open5GLoS | open5glos:dasaco-gnb-runtime |

The use of `latest` for DBPython should be replaced by a fixed image tag
or immutable image digest in a fresh reproduction.

## Network-Function Resource Configuration

| Component | CPU request | Memory request | CPU limit | Memory limit |
|---|---:|---:|---:|---:|
| AMF | 100m | 128Mi | 500m | 512Mi |
| AUSF | 100m | 128Mi | 200m | 256Mi |
| CHF | 100m | 128Mi | 200m | 256Mi |
| NEF | 100m | 128Mi | 200m | 256Mi |
| NRF | 100m | 128Mi | 200m | 256Mi |
| NSSF | 100m | 128Mi | 200m | 256Mi |
| PCF | 100m | 128Mi | 200m | 256Mi |
| SMF | 100m | 128Mi | 200m | 256Mi |
| UDM | 100m | 128Mi | 200m | 256Mi |
| UDR | 100m | 128Mi | 200m | 256Mi |
| WebUI | 100m | 128Mi | 200m | 256Mi |
| MongoDB | 500m | 512Mi | 750m | 768Mi |
| Open5GLoS | 100m | 128Mi | 500m | 512Mi |
| DBPython | 100m | 128Mi | 100m | 128Mi |

## Stable Baseline Topology

The current stable baseline contains one replica of each main free5GC
control-plane function:

- AMF: 1
- AUSF: 1
- CHF: 1
- NEF: 1
- NRF: 1
- NSSF: 1
- PCF: 1
- SMF: 1
- UDM: 1
- UDR: 1
- WebUI: 1
- MongoDB: 1
- Open5GLoS: 1
- DBPython: 1

UPF and UERANSIM deployments were configured with zero replicas during
the environment inventory capture.

## Reproducibility Notes

- Record immutable image digests before a new experiment series.
- Preserve Helm values and Kubernetes manifests.
- Record PacketRusher, Open5GLoS, and DA-SACO commit hashes.
- Confirm all resource requests and limits before each method.
- Confirm the stable baseline before each run.
- Store UTC run boundaries with every run.
- Do not assume the previous environment used identical versions or
  resource configurations.
