## Code-to-Architecture Mapping Methods

To address the challenge of establishing precise mappings between source code files and architectural modules, we implemented and evaluated four complementary approaches under the second stage of our framework:

- **BM25-based Retrieval**: A lexical retrieval baseline leveraging BM25 to compute textual similarity between module descriptions and source code comments or identifiers.
- **LLM-based Scoring**: This approach uses a large language model (LLM) to score the semantic relevance between each source file and module description.
- **LLM-based Assignment**: Based on the scoring results, this method assigns each file to the most likely module using thresholding or ranking strategies.
- **IP-RAG-based Assignment**: A retrieval-augmented generation method that employs in-context examples and LLM reasoning to infer the most suitable architectural module for each file.

### Directory Structure

The implementation scripts and outputs of each method are organized under the following folders:

```
BM25/          → BM25-based retrieval method  
LLM-S/         → LLM-based Scoring method (semantic similarity)  
LLM-A/         → LLM-based Assignment method  
IP-RAG-A/      → IP-RAG-based Assignment method  
```

### Script Execution

Each method is executed independently using a script named `run_projects.sh` located in its corresponding directory. The typical usage is as follows:

```bash
cd BM25/
bash run_projects.sh
```

Each script will automatically perform the mapping process for that method and generate the corresponding output JSON file in the same directory.

### Output Format

Each method produces its mapping results in a standardized JSON file named `{method}_mapping.json`. For example:

- `BM25_mapping.json`
- `LLM-S_mapping.json`
- `LLM-A_mapping.json`
- `IP-RAG-A_mapping.json`

These files are located in the deepest-level subdirectory of each method's folder, where the final outputs are generated. These files record the predicted mappings between source code files and architectural modules and serve as input to the downstream fusion and documentation generation steps.