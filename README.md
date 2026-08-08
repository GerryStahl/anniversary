anniversary
===========

This project supports the 20th anniversary of the "International Journal of
Computer-Supported Collaborative Learning" (ijCSCL), covering 2006-2026.
Its goal is to analyze longitudinal journal trends by clustering summaries of
published articles.

The Anniversary Project provides utilities for:
- ingesting ijCSCL PDFs,
- extracting metadata and full text,
- identifying editorial articles,
- generating two families of summaries,
- classifying articles,
- preparing vector representations (semantic embeddings) of the summaries,
- performing clustering analysis of summary vectors.

Development is done in Visual Studio Code. Journal articles are summarized with
Claude Haiku and with local Ollama (`llama3.1:8b`), and sample trend-coding is
run with Haiku using the controlled taxonomy in `src/dimension_taxonomy.py`.

Quick start
-----------

1. Install dependencies in a virtual environment:

```bash
python -m pip install -r documentation/requirements.txt
```

2. Ingest PDFs from the default raw directories (`data/raw 2006-2015` and `data/raw 2016-2026`):

```bash
python -m src
```

To ingest from a specific directory only:

```bash
python -m src --root "data/raw 2006-2015"
```

3. Build or refresh the tabular report:

```bash
PYTHONPATH=$PWD python -m src.categorize_all_and_build_csv
```

This updates:

- `data/processed/ijcscl.pkl`
- `data/processed/ijcscl.json`
- `reports/articles.csv`

Manual metadata corrections
---------------------------

Use `data/metadata_corrections.csv` for durable hand edits to metadata fields.
This is the safest way to override `title`, `authors`, `editorial`, DOI, or basic
bibliographic fields without editing the derived JSON/CSV outputs directly.

- Edit one row per article id.
- Leave a cell blank to keep the current stored value.
- Use `__CLEAR__` to explicitly clear a field.
- Supported columns: `id`, `title`, `authors`, `editorial`, `doi`, `year`,
  `volume`, `issue`, `article_number`, `notes`.

Apply the corrections without re-ingesting PDFs:

```bash
PYTHONPATH=$PWD python -m src.apply_metadata_corrections
```

Corrections are also applied automatically whenever you run PDF ingestion or the
end-of-session refresh command, so your manual fixes persist across future re-runs.

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

Current data status:

- 357 PDFs are currently ingested across 2006-2026.
- Ingestion scans both default raw directories: `data/raw 2006-2015` and
  `data/raw 2016-2026`.
- Editorial articles are flagged and can be refined through
  `data/metadata_corrections.csv`.

`src/ingest.py` discovers PDFs, extracts full text with PyMuPDF, and infers title and author
metadata from first-page layout cues.

### Ollama summaries

These summaries run locally with `llama3.1:8b` and are slower than Haiku.

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

Claude Haiku summaries are stored in `summary_haiku` and can be regenerated at
any time.

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

Articles are currently classified with an Ollama model into:

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

### Embed Claude Haiku summaries

Use `embed_texts.py` to generate semantic vectors for `summary_haiku`:

```bash
python -c "from src.embed_texts import embed_corpus_field; print(embed_corpus_field(field='summary_haiku', embedding_field='embedding_haiku_summary', model_name='all-MiniLM-L6-v2'))"
```

### Cluster Haiku summaries

Use `cluster_vectors.py` helpers (or `run_vector_pipeline.py`) to cluster
all
`embedding_haiku_summary` vectors, with `k > 4` (for example, `k=17`).

```bash
python -c "from src.run_vector_pipeline import run_embedding_and_clustering; print(run_embedding_and_clustering(source_field='summary_haiku', embedding_field='embedding_haiku_summary', cluster_field='cluster_haiku_summary', model_name='all-MiniLM-L6-v2', k=17))"
```

### Analyze clusters for trends in the journal over the years

Regenerate `reports/cluster_haiku_summary.csv`, then compare cluster labels
with category, summary, year, and editorial flags for trend analysis.

Generate the cluster report directly from the current PKL store:

```bash
PYTHONPATH=$PWD python -m src.build_cluster_haiku_summary_csv
```

### Build analysis-ready trends dataset (editorials excluded)

Generate a trends dataset from the current PKL store with editorials excluded
by default (`editorial == "editorial"` or `article_number == 0`):

```bash
PYTHONPATH=$PWD python -m src.build_trends_dataset_csv
```

This writes `reports/trends_dataset.csv` with metadata, year/editor-era,
cluster/category values, and dimension-coding fields for:

- methodology,
- unit of analysis,
- pedagogy,
- technology,
- theory,
- AI/LLM involvement,
- evidence span and coding confidence.

Taxonomy and coding policy notes: `documentation/trend_taxonomy_v1.md`.

### Category taxonomy and prompts

This project uses two related coding layers:

1) **Legacy category label** (`category`, single letter)

- `a`: design of collaboration
- `b`: design of technology to support learning
- `c`: analysis of interaction among students
- `d`: measurement of learning
- `e`: editorial
- `f`: none of the above

2) **Trend-coding taxonomy** (dimension-specific fields in `reports/trends_dataset.csv`)

- `methodology_primary` (from `methodology` options)
- `unit_of_analysis_primary` (from `unit_of_analysis` options)
- `pedagogy_primary` (from `pedagogy` options)
- `technology_primary` (from `technology` options)
- `theory_primary` (from `theory` options)
- `ai_llm_involvement_primary` (from `ai_llm_involvement` options)

Canonical options are defined in `src/dimension_taxonomy.py` and include an `other`
fallback in every dimension.

#### Dimension options (canonical)

- `methodology`: `descriptive_statistics`, `inferential_statistics`,
  `multilevel_modeling`, `social_network_analysis`, `discourse_analysis`,
  `interaction_analysis`, `computational_linguistics_nlp`,
  `sequence_process_mining`, `learning_analytics`,
  `experimental_quasi_experimental`, `design_based_research`,
  `ethnographic_case_study`, `mixed_methods`, `content_analysis`, `other`
- `unit_of_analysis`: `individual_learner`, `dyad_small_group`,
  `classroom_cohort`, `teacher_facilitation`, `community_network`,
  `artifact_discourse_trace`, `cross_level_multilevel`, `other`
- `pedagogy`: `knowledge_building`, `collaboration_scripts`,
  `inquiry_problem_based_learning`, `argumentation`, `peer_review_feedback`,
  `teacher_orchestrated_discussion`, `self_peer_regulation`,
  `community_of_practice`, `other`
- `technology`: `asynchronous_forum`, `synchronous_chat_video`,
  `wiki_knowledge_base`, `shared_workspace_canvas`,
  `tabletop_tangible_interface`, `awareness_dashboard`,
  `collaboration_scripting_tools`, `multimodal_sensors_eye_tracking`,
  `none_minimal_technology`, `other`
- `theory`: `sociocultural`, `dialogic`, `socio_cognitive`,
  `knowledge_building_theory`, `activity_theory`, `communities_of_practice`,
  `distributed_cognition`, `information_processing`, `critical_pragmatic`,
  `other`
- `ai_llm_involvement`: `none`, `ai_supported_non_llm`,
  `llm_supported_writing`, `llm_supported_feedback`,
  `llm_supported_assessment`, `llm_supported_orchestration`,
  `llm_supported_analytics`, `llm_as_learning_partner`, `other`

#### Prompt templates used in code

**Summarization system prompt** (`src/summarize.py`):

```text
You are an expert in computer-supported collaborative learning.
Write a concise 50-60 word summary of the article's central claim or finding.
Focus on the main research question, method type, and conclusion.
Do not mention that you are summarizing.
Return only the summary text.
```

**Summarization user prompt template** (`src/summarize.py`):

```text
Title: {title}
Authors: {authors}
Year: {year}
Volume: {volume}
Issue: {issue}
Article ID: {id}

Article text:
{fulltext}
```

**Trend-coding system prompt** (`src/_run_haiku_and_coding_sample.py`):

```text
You are an expert in computer-supported collaborative learning (CSCL) and systematic literature review.
Return a compact JSON object with exactly these keys and controlled values:

  methodology_primary — choose ONE of: [from src/dimension_taxonomy.py]
  unit_of_analysis_primary — choose ONE of: [from src/dimension_taxonomy.py]
  pedagogy_primary — choose ONE of: [from src/dimension_taxonomy.py]
  technology_primary — choose ONE of: [from src/dimension_taxonomy.py]
  theory_primary — choose ONE of: [from src/dimension_taxonomy.py]
  ai_llm_involvement_primary — choose ONE of: [from src/dimension_taxonomy.py]
  evidence_span: short phrase indicating which sections support the coding, e.g. "methods+findings"
  coding_confidence: a decimal between 0.0 and 1.0
  coding_notes: one or two sentences noting rationale or uncertainty

Rules:
- You MUST choose values from the listed options for each *_primary field. Do not invent labels.
- If no option fits well, choose "other" and explain in coding_notes.
- Return only valid JSON. No markdown fences, no extra text outside the JSON object.
```

**Trend-coding user prompt template** (`src/_run_haiku_and_coding_sample.py`):

```text
Title: {title}
Authors: {authors}
Year: {year}
Volume: {volume}
Issue: {issue}
Article ID: {id}

Article excerpt:
{fulltext[:12000]}
```

### End-of-session refresh (reports + GitHub)

Use one command to clean temporary helper scripts, regenerate report CSVs from
the current PKL store (including `reports/trends_dataset.csv`), and optionally
commit/push to GitHub:

```bash
PYTHONPATH=$PWD python -m src.refresh_reports --commit --push
```

Useful variants:

```bash
# Refresh reports only (no git changes)
PYTHONPATH=$PWD python -m src.refresh_reports

# Refresh + commit, but do not push
PYTHONPATH=$PWD python -m src.refresh_reports --commit --message "Refresh reports"
```


Vector pipeline
---------------

Three modules support embedding and clustering workflows:

- `src/embed_texts.py`: builds corpora from canonical fields and stores embeddings
- `src/cluster_vectors.py`: loads vectors, scores candidate `k`, and clusters matrices
- `src/run_vector_pipeline.py`: orchestrates embedding + clustering for one source field

Typical source fields include:

- `fulltext`
- `summary_ollama`
- `summary_haiku`

Typical target fields include:

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
- `src/build_articles_csv.py`: builds `reports/articles.csv` from the PKL store
- `src/build_cluster_haiku_summary_csv.py`: builds `reports/cluster_haiku_summary.csv` from the PKL store
- `src/build_trends_dataset_csv.py`: builds `reports/trends_dataset.csv` with editorials excluded by default
- `src/dimension_taxonomy.py`: v1 controlled taxonomy options for dimension coding
- `src/refresh_reports.py`: end-of-session report refresh, cleanup, and optional git commit/push
- `src/embed_texts.py`: embedding helpers
- `src/cluster_vectors.py`: vector loading and clustering helpers
- `src/run_vector_pipeline.py`: end-to-end vector pipeline

Reports and outputs
-------------------

- `data/processed/ijcscl.pkl`: canonical pickle store (full vectors)
- `data/processed/ijcscl.json`: JSON mirror without `fulltext` or embedding vectors
- `reports/articles.csv`: metadata, categories, and both summary columns
- `reports/cluster_haiku_summary.csv`: cluster labels, editorial flags, and metadata for all articles
- `reports/trends_dataset.csv`: analysis-ready trends table with dimension-coding fields (editorials excluded)
- `reports/summary_comparison.csv`: side-by-side Ollama vs. Claude comparison
- `reports/categories.csv`: volume/category extract
- `reports/volume_category_counts.png`: category counts by volume plot

Notes
-----

- Summarization and categorization with Ollama require a running local server and an installed model.
- Claude summarization and Haiku-based trend-coding require `ANTHROPIC_API_KEY`.
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
