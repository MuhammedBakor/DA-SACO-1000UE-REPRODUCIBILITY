# Results Guide

## Mean Registration Completion

- Static: 50.22%
- AMF-HPA: 56.58%
- Open5GLoS: 85.58%
- Admission-only: 45.62%
- DA-SACO: 76.30%

DA-SACO significantly outperformed Admission-only after Holm correction.

## Mean Post-Security Latency

- Open5GLoS: 3528.882 ms
- Static: 3950.100 ms
- AMF-HPA: 5576.659 ms
- DA-SACO: 7904.273 ms
- Admission-only: 10011.661 ms

## DA-SACO Scaling

- Scale-out cases: 16
- Cases reaching Ready: 16
- Cases processing traffic: 15
- Useful scale-out rate: 93.75%
- Recovery success: 100%
- Confirmed idle case: R4 AUSF

## CPU and Memory Trade-off

DA-SACO reduced aggregate AMF CPU P95 by 27.13% relative to AMF-HPA and 25.00% relative to Open5GLoS.

DA-SACO recorded the highest aggregate AMF memory P95 at 593.80 MiB and the highest MongoDB memory P95 at 480.80 MiB.

The CPU improvement and memory cost must both be reported.

## Interpretation

No method dominated every metric. Open5GLoS used three pre-provisioned AMFs. AMF-HPA created additional Ready AMFs without visible SUPI redistribution. DA-SACO achieved useful multi-NF scaling but incurred latency and memory trade-offs.
