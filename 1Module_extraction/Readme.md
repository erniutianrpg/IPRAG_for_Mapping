# Documented Module Extraction

This module is responsible for extracting documented architectural modules from existing, potentially incomplete architectural documentation. It serves as the initial stage in the end-to-end framework for updating outdated architectural artifacts.

## Structure

This folder contains the following:

- **extract.py**: Scripts for invoking LLMs to extract module information from input documentation.
- evaluation.py: Scripts for evaluating extracted module information.

he output of extracted modules for each individual project is organized under the dataset/ directory, following the structure:
dataset/<project_name>/Extracted_Module
