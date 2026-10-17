<img width="4032" height="313" alt="image" src="https://github.com/user-attachments/assets/842d5c6f-38d0-432f-bb3e-7343c0b53ebc" /><img width="4032" height="313" alt="image" src="https://github.com/user-attachments/assets/d677b742-9989-4f5e-8823-7817511822ca" /><img width="4032" height="313" alt="image" src="https://github.com/user-attachments/assets/5ff7a2ae-e777-4f01-b6f6-9134d999090f" /># DA-SACO 1000-UE Reproducibility Package

This public reproducibility package contains derived results, experiment manifests, documentation, and reproducible analysis scripts for five methods: Static, AMF-HPA, Open5GLoS, Admission-only, and DA-SACO.

## Experiment Scope

- Five runs per method
- 1000 UEs per run
- 120 ms inter-UE launch interval
- 25 accepted runs

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

## Reproduction Documentation

Read the documentation in this order:

1. `docs/EXPERIMENT-DESIGN.md`
2. `docs/CURRENT-ENVIRONMENT-SPECIFICATIONS.md`
3. `docs/ENVIRONMENT-AND-DEPENDENCIES.md`
4. `docs/METHOD-CONFIGURATIONS.md`
5. `docs/EXPERIMENT-EXECUTION-RECORD.md`
6. `docs/REPRODUCTION-GUIDE.md`
7. `docs/ANALYSIS-PIPELINE.md`
8. `docs/RESULTS-GUIDE.md`
9. `docs/EVIDENCE-PROVENANCE.md`
10. `docs/KNOWN-ISSUES-AND-EXCLUSIONS.md`

## Reference Software Revisions

- DA-SACO repository commit: `7868d1d483a69ca8727e588b3182e1cd8ed074e4`
- PacketRusher commit: `194ae987ee2bacfae2cf57d435b475e54076679e`
- free5GC Helm commit: `6f67ec11512e8c6b4eb6b3237f46e71fec5bdda2`
- Open5GLoS commit: `55994ae45ac66e00722460fad4902a481dac6f68`
- free5GC network-function images: `v4.2.3`

## Related Earlier Repositories

- DA-SACO earlier research package:
  `https://github.com/MuhammedBakor/dasaco-research.git`
- Earlier Open5GLoS and DA-SACO package:
  `https://github.com/MuhammedBakor/open5glos-dasaco.git`

The earlier repositories preserve continuity with the previous 100-UE
work. This repository documents the unified 25-run, 1000-UE evaluation.

## Important Interpretation Notes

- DA-SACO achieved a 93.75% useful scale-out rate.
- All DA-SACO scaled functions recovered to baseline.
- DA-SACO reduced aggregate AMF CPU P95 relative to AMF-HPA and Open5GLoS.
- DA-SACO recorded the highest aggregate AMF memory P95.
- DA-SACO also recorded the highest MongoDB memory P95.
- The reported latency is post-security registration-completion latency,
  not end-to-end registration latency.

## DA-SACO Controller Source

The evaluated DA-SACO controller source and configuration artifacts are
included in the [`controller`](controller) directory. Analysis and
evidence-extraction programs remain separately available in
[`scripts`](scripts).

The controller package excludes credentials, kubeconfig files,
operational logs, raw subscriber evidence, runtime secrets, and
environment-specific private material.
