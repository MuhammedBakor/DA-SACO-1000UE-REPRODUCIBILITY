# Analysis Issue Log

## Resolved issues

- Some pasted terminal commands were damaged by HTML encoding.
- Nanosecond timestamps required normalization for Python datetime processing.
- Historical, failed, diagnostic, and excluded-attempt directories were removed from the canonical evidence set.
- Earlier DA-SACO R1 and R2 zero-completion reports were superseded by canonical exact-window extraction.
- The R2 AMF pod-role conflict was resolved using the controller `CAPACITY_USE_VERIFIED` record.
- Per-UE post-security latency was reconstructed for all 25 runs.
- Reconstruction matched all five existing Admission-only latency files.
- Failure classification was corrected to use the full planned SUPI universe rather than rejected-only SUPIs.

## Results requiring transparent discussion

- DA-SACO has a CPU-versus-memory trade-off.
- DA-SACO AMF and MongoDB memory P95 values are comparatively high.
- DA-SACO latency is higher than Static, AMF-HPA, and Open5GLoS for the reported post-security metric.
- AMF-HPA created ready AMF capacity but did not redistribute visible SUPI traffic.
- Open5GLoS used three pre-provisioned AMFs in every run.
- Admission-only admitted all planned UEs but delayed most of them and exhibited extensive security-mode timeout evidence.
