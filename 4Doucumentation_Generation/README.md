# 📄 Documentation Generation

The objective of this project is to generate missing documentation for project modules and to evaluate the consistency and relevance between the generated documentation—produced in the absence of a given module—and the actual documentation of that module. Additionally, the coherence and fluency of the generated documentation itself will be assessed.
---

## Technology Stack

- **Programming Language**：Python 3.12
- **Evaluation Framework**：[UniEval]([https://github.com/yangyi02/unieval](https://github.com/maszhongming/UniEval))
- **Data Processing and Runtime Environment**：
  - Standard Python third-party libraries
  - dependencies：openai, transformers (used when model-based generation or comparison is involved)

---

## Project Structure
├── evaluate/           # Evaluation module: performs automated assessment of consistency, relevance, coherence, and fluency  
├── generate/           # Generation module: handles code summarization and documentation generation logic  
├── Result/             # Output directory: stores generated results, including intermediate outputs and evaluation reports  
├── README.md           # Documentation  




