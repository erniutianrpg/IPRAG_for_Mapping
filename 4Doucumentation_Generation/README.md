# 📄 Documentation Generation

本项目旨在生成缺失的代码文档，并评估生成文档与实际文档之间的一致性（consistency）、相关性（relevance），以及生成文档本身的连贯性（coherence）与流畅性（fluency）。

---

## 🧰 技术栈（Technology Stack）

- **编程语言**：Python 3.12
- **评估框架**：[UniEval](https://github.com/yangyi02/unieval)
- **数据处理与运行环境**：
  - 标准 Python 第三方库（如 `os`, `json`, `argparse` 等）
  - 可选依赖：transformers、datasets（如涉及模型生成或对比）

---

## 📁 项目结构（Project Structure）
├── evaluate/ # 评估模块：用于执行 consistency、relevance、coherence、fluency 的自动化评估
├── generate/ # 生成模块：代码摘要生成与文档生成逻辑
├── Result/ # 生成结果保存路径（中间结果、评估输出等）
├── README.md # 项目说明文档
└── requirements.txt # Python 依赖文件（如有）
