# REMAP: Retrieval-Augmented and Expert-Guided Mapping

This repository contains the implementation, dataset, experimental outputs, and supplementary experiments for REMAP, an end-to-end framework for updating incomplete architectural documentation through code-to-architecture mapping.

## Overview

Software architecture documentation is often incomplete or outdated, which makes maintenance, comprehension, and evolution tasks more difficult. REMAP addresses this problem by constructing mappings between source-code files and architectural modules when the available architecture documentation is incomplete.

The framework has three main stages:

1. **Documented Module Extraction**
   Extract documented architectural modules from existing architecture documentation using large language models.
2. **Code-to-Architecture Mapping Generation**
   Generate mappings between source-code files and documented or undocumented architectural modules using retrieval-based, LLM-based, and IP-RAG-based methods.
3. **Mapping Fusion**
   Fuse outputs from multiple mapping methods with a Mixture-of-Experts model to improve final mapping quality.

## Repository Structure

```text
.
|-- 1Module_extraction/              # Stage 1: LLM-based documented module extraction.
|-- 2Mapping_generation/             # Stage 2: mapping generation methods and outputs.
|-- 3Mapping_Fusion/                 # Stage 3: MoE-based mapping fusion.
|-- dataset/                         # Main benchmark data and ground-truth labels.
|-- supplementary_experiments/        # Additional experiments, datasets, baselines, and evaluations.
|-- Readme.md                        # Repository overview.
`-- Supplementary Material.pdf        # Extended experimental and methodological details.
```

## Main Components

### `1Module_extraction/`

Contains scripts and LLM responses for extracting documented architectural modules from architecture documentation. The evaluation script reports precision, recall, and F1 score for module extraction results.

### `2Mapping_generation/`

Contains code-to-architecture mapping methods, including retrieval-based, LLM-based, and IP-RAG-based approaches. Each method produces standardized mapping outputs that can be used by downstream fusion and documentation-update steps.

### `3Mapping_Fusion/`

Contains the Mixture-of-Experts fusion implementation, processed mapping inputs, prediction outputs, and pretrained model weights for the evaluated systems.

### `dataset/`

Contains the main benchmark data used by the framework, including project data and labels required by the extraction, mapping, and fusion stages.

### `supplementary_experiments/`

Contains additional experiments used for extended evaluation, including baseline comparisons, extra datasets, mapping-generation evaluations, prompt evaluations, summary-generation experiments, and related analysis artifacts. See [`supplementary_experiments/README.md`](supplementary_experiments/README.md) for details.

## Usage

Each major stage includes its own README or scripts. A typical workflow is:

1. Run module extraction in `1Module_extraction/`.
2. Run mapping generation in `2Mapping_generation/`.
3. Run mapping fusion in `3Mapping_Fusion/`.
4. Use the supplementary experiments under `supplementary_experiments/` for extended evaluation and comparison.

Please refer to the README files inside each directory for component-specific commands and expected outputs.

## Notes

- Shell scripts and PowerShell scripts are excluded from version control in this repository.
- Large generated result directories that are not required for source inspection are ignored.
- Some third-party benchmark artifacts that require unavailable Git LFS objects are excluded from the uploaded supplementary package.
