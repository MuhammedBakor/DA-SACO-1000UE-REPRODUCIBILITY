# Evaluated DA-SACO Controller Source

This directory preserves the exact local DA-SACO controller source
selected as the reconstruction reference after auditing the evaluated
Ubuntu VM.

## Why this directory exists

The DA-SACO source repository was at commit:

`7868d1d483a69ca8727e588b3182e1cd8ed074e4`

However, `parallel_action_executor.py` in the evaluated VM contained
substantial uncommitted changes relative to that commit. The active
file added behavior directly associated with the reported evaluation:

- dependency-first staged execution;
- parallel scaling within each stage;
- dependency blocking after an earlier-stage failure;
- stage-level state and action evidence;
- reopening admission only after complete stage verification;
- a 20-second workload propagation interval;
- measured workload-use verification on every added Pod; and
- classification of added capacity as verified-use or idle capacity.

The current working-tree version is therefore preserved here together
with its diff, manifest, provenance record, and SHA-256 checksums.

## Directory contents

- `source/`: exact frozen Python, shell, and YAML files;
- `SOURCE-REVISION.txt`: original commit and working-tree status;
- `SOURCE-FILE-MANIFEST.txt`: frozen source inventory;
- `PARALLEL-ACTION-EXECUTOR-WORKING-DIFF.patch`: changes relative to
  the recorded source commit;
- `FROZEN-SOURCE-SHA256SUMS.txt`: checksums generated when the local
  source package was frozen.

## Important distinction

The `source/` directory preserves the evaluated working-tree source.
It is not reconstructed solely from the recorded Git commit.

Operational logs, credentials, kubeconfig files, raw subscriber
evidence, runtime secrets, and VM images are excluded.
