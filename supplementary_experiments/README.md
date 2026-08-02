# Supplementary Experiments

This directory contains the supplementary experiment package for REMAP. It is organized as a single top-level folder so that the additional baselines, datasets, evaluation scripts, and experiment outputs can be inspected separately from the main framework implementation.

## Directory Structure

```text
supplementary_experiments/
|-- baseline-InMap/      # Baseline implementations and baseline comparison artifacts.
|-- dataset/             # Additional datasets and project snapshots used in supplementary experiments.
|-- evaluation/          # Evaluation scripts for mapping quality, prompt quality, and generated summaries.
`-- experiment/          # Supplementary experiment scripts, settings, generated summaries, and outputs.
```

## Contents

### `baseline-InMap/`

Contains baseline materials used to compare REMAP with InMap-style mapping approaches across Java, Python, C, and C++ projects. The directory includes baseline scripts, intermediate mapping artifacts, and result files used by the supplementary evaluation.

### `dataset/`

Contains additional project data used by the supplementary experiments. The dataset is separated from the main benchmark directory to keep the supplementary package self-contained.

### `evaluation/`

Contains evaluation utilities and outputs for the supplementary study, including:

- `DMquality-eva/`: evaluation of documented-module quality.
- `Mapping_generation/`: evaluation scripts and artifacts for mapping-generation quality.
- `prompt-eva/`: prompt-level evaluation materials.
- `summary-eva/`: evaluation materials for generated architecture summaries.

The generated `result/` directory is intentionally ignored and is not part of the uploaded package.

### `experiment/`

Contains supplementary experiment code and generated artifacts, including:

- language-specific experiment folders for Java, Python, C, and C++;
- `summary-gen/` for architecture-summary generation experiments;
- `result/` for retained experiment outputs.

The local `project/` directory is intentionally ignored because it contains project workspaces that are not required for the uploaded supplementary package.

## Version-Control Notes

The following files and directories are intentionally excluded from the uploaded repository:

- PowerShell scripts: `*.ps1`
- shell scripts: `*.sh`
- `supplementary_experiments/evaluation/result/`
- `supplementary_experiments/experiment/project/`
- unavailable third-party Git LFS artifacts under `dataset/project/py/lerobot/lerobot/tests/artifacts/`

Paths in uploaded code are prepared to use relative paths where the supplementary package needs to be portable.
