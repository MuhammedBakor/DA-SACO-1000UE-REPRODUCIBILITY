# DA-SACO 1000-UE Reproducibility Package

This private repository package contains derived results and reproducible analysis scripts for five methods: Static, AMF-HPA, Open5GLoS, Admission-only, and DA-SACO.

## Experiment Scope

- Five runs per method
- 1000 UEs per run
- 120 ms inter-UE launch interval
- 25 canonical runs

## Main Results

- DA-SACO mean registration success: 76.30%
- DA-SACO useful scale-out rate: 93.75%
- DA-SACO recovery success: 100%
- DA-SACO reduced aggregate AMF CPU P95 versus AMF-HPA and Open5GLoS
- DA-SACO recorded the highest aggregate AMF and MongoDB memory P95
- Comparable post-security latency was extracted for all 25 runs

## Latency Definition

Latency is measured from Handle InitialRegistration to Handle Registration Complete. It is not end-to-end registration latency.

## Integrity

Source experiment files were analyzed in read-only mode. Excluded and historical attempt directories are not treated as authoritative runs.
