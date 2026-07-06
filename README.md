anniversary
===========

Utilities for ingesting ijCSCL PDFs, extracting metadata and full text, generating two
families of summaries, classifying articles, and preparing vector representations for later
clustering analysis.

Quick start
-----------

1. Install dependencies in a virtual environment:

```bash
python -m pip install -r documentation/requirements.txt
```

2. Ingest PDFs from `data/raw`:

```bash
python -m src --root data/raw
```

3. Build or refresh the tabular report:

```bash
PYTHONPATH=$PWD python -m src.categorize_all_and_build_csv
```

This updates:

- `data/processed/ijcscl.pkl`
- `data/processed/ijcscl.json`
- `reports/articles.csv`

Data model
----------

The `Article` model in `src/models.py` now uses canonical field names:

- `fulltext`: extracted PDF text
- `summary_ollama`: local Ollama summary
- `summary_haiku`: Claude Haiku summary
- `embedding_fulltext`: vector for full text
- `embedding_ollama_summary`: vector for the Ollama summary
- `embedding_haiku_summary`: vector for the Claude summary
- `cluster_fulltext`: cluster label for full text vectors
- `cluster_ollama_summary`: cluster label for Ollama summary vectors
- `cluster_haiku_summary`: cluster label for Claude summary vectors

Compatibility accessors for older names (`text`, `ollama_summary`, `claude_summary`) are still
available so legacy scripts continue to run, but new code should use the canonical names.

Workflow
--------

### Ingestion

`src/ingest.py` discovers PDFs, extracts full text with PyMuPDF, and infers title and author
metadata from first-page layout cues.

### Ollama summaries

Generate or refresh one summary:

```bash
python -c "from src.summarize import summarize_one; print(summarize_one('ijCSCL_4_1_2', model='llama3.1:8b'))"
```

Generate for all articles:

```bash
python -c "from src.summarize import summarize_store; summarize_store(model='llama3.1:8b')"
```

These populate `summary_ollama`.

### Claude Haiku summaries

Generate Claude summaries and persist them back to the store:

```bash
PYTHONPATH=$PWD python -m src.summarize_Claude --model claude-haiku-4-5
```

These populate `summary_haiku`.

### Summary comparison

Compare Ollama and Claude summaries for a subset of articles:

```bash
PYTHONPATH=$PWD python -m src.compare_summaries --limit 5
```

This writes `reports/summary_comparison.csv` with both summaries and a diff score.

### Categorization

Articles are classified into:

- `a`: design of collaboration
- `b`: design of technology to support learning
- `c`: analysis of interaction among students
- `d`: measurement of learning
- `e`: editorial
- `f`: none of the above

Run:

```bash
PYTHONPATH=$PWD python -m src.categorize_all_and_build_csv
```

This updates `category` and refreshes `reports/articles.csv`.

Vector pipeline
---------------

Three modules support embedding and clustering preparation:

- `src/embed_texts.py`: builds corpora from canonical fields and stores embeddings
- `src/cluster_vectors.py`: loads vectors, scores candidate `k`, and clusters matrices
- `src/run_vector_pipeline.py`: orchestrates embedding + clustering for one source field

Supported source fields are typically:

- `fulltext`
- `summary_ollama`
- `summary_haiku`

Typical target fields are:

- `embedding_fulltext`, `cluster_fulltext`
- `embedding_ollama_summary`, `cluster_ollama_summary`
- `embedding_haiku_summary`, `cluster_haiku_summary`

Example:

```bash
python -c "from src.run_vector_pipeline import run_embedding_and_clustering; print(run_embedding_and_clustering(source_field='summary_ollama', embedding_field='embedding_ollama_summary', cluster_field='cluster_ollama_summary', model_name='all-MiniLM-L6-v2', k=6))"
```

Files of interest
-----------------

- `src/models.py`: canonical article schema
- `src/store.py`: PKL/JSON persistence and migration logic
- `src/ingest.py`: PDF ingestion and metadata extraction
- `src/llm.py`: Ollama wrapper
- `src/summarize.py`: Ollama summarization pipeline
- `src/summarize_Claude.py`: Claude summary generation script
- `src/categorize.py`: article categorization pipeline
- `src/categorize_all_and_build_csv.py`: report builder for `reports/articles.csv`
- `src/compare_summaries.py`: Ollama vs Claude comparison report
- `src/generate_categories_and_chart.py`: volume/category spreadsheet and chart
- `src/regenerate_reports.py`: re-ingest raw PDFs and rebuild the store
- `src/embed_texts.py`: embedding helpers
- `src/cluster_vectors.py`: vector loading and clustering helpers
- `src/run_vector_pipeline.py`: end-to-end vector pipeline

Reports and outputs
-------------------

- `data/processed/ijcscl.pkl`: canonical pickle store (full vectors)
- `data/processed/ijcscl.json`: JSON mirror without `fulltext` or embedding vectors
- `reports/articles.csv`: metadata, categories, and both summary columns
- `reports/cluster_haiku_summary.csv`: cluster labels, editorial flags, and metadata for all articles
- `reports/summary_comparison.csv`: side-by-side Ollama/Claude comparison
- `reports/categories.csv`: volume/category extract
- `reports/volume_category_counts.png`: category counts by volume plot

Notes
-----

- Summarization and categorization with Ollama require a running local server and an installed model.
- Claude summarization requires `ANTHROPIC_API_KEY`.
- Existing stored data is migrated on load from legacy keys like `text`, `summary`,
  `ollama_summary`, and `claude_summary`.
- The embedding dependencies are larger than the base ingestion stack; install them only once and
  reuse the same environment for vector work.

Development
-----------

Lint the code with:

```bash
python -m flake8 src/ --max-line-length=120
```
