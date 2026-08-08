# Trend Taxonomy v1 (Interpretability-First)

This taxonomy supports coding ijCSCL articles for longitudinal trend analysis.

## Principles

1. Code from methods/findings evidence, not only introduction claims.
2. Prefer transparent labels and auditable decisions.
3. Allow one primary label plus optional secondary labels per dimension.
4. Exclude editorials from trend evidence by default.

## Dimensions

- Methodology
- Unit of analysis
- Pedagogy
- Technology
- Theory
- AI/LLM involvement

The current controlled options are defined in [src/dimension_taxonomy.py](../src/dimension_taxonomy.py).

`AI/LLM involvement` is intentionally kept as a single dimension for now and can
be differentiated later if multiple articles begin to address recurring subtypes.

`Equity` is not yet a formal dimension, but may become one if a substantial set
of papers addresses recurring issues such as access, language, fairness, or
participation disparities.

## Coding metadata fields

- `evidence_span`: short note describing evidence region(s), e.g. `methods+findings`.
- `coding_confidence`: numeric confidence in `[0,1]`.
- `extends_methodology|pedagogy|technology|theory`: whether findings extend that dimension.
- `coding_notes`: optional rationale notes.

## Iterative growth policy

When a paper does not fit existing options:

1. Use closest option as primary.
2. Record mismatch in `coding_notes`.
3. Propose candidate new label with examples.
4. Add new label only after at least 3 papers warrant the same concept.

This preserves comparability over time while allowing taxonomy evolution.
