# 📄 Documentation Generation

The objective of this project is to generate missing documentation for project modules and to evaluate the consistency and relevance between the generated documentation—produced in the absence of a given module—and the actual documentation of that module. Additionally, the coherence and fluency of the generated documentation itself will be assessed.
---

## Technology Stack

- **Programming Language**：Python 3.12
- **Evaluation Framework**：[UniEval](https://github.com/yangyi02/unieval)
- **Data Processing and Runtime Environment**：
  - Standard Python third-party libraries
  - dependencies：openai, transformers (used when model-based generation or comparison is involved)

---

## Project Structure
├── evaluate/ # 评估模块：用于执行 consistency、relevance、coherence、fluency 的自动化评估
├── generate/ # 生成模块：代码摘要生成与文档生成逻辑
├── Result/ # 生成结果保存路径（中间结果、评估输出等）
├── README.md # 项目说明文档
└── requirements.txt # Python 依赖文件（如有）
