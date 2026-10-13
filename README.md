# AIDATA

AIDATA is the dataset and evaluation foundation for Axral AI projects, focused on reliable reasoning, software engineering, and tool-assisted problem solving.

## Goals

- Teach multi-step problem solving with explicit assumptions, checks, and calibrated uncertainty.
- Improve code generation, debugging, testing, review, and safe refactoring.
- Keep training, validation, and held-out evaluation data separate.
- Track provenance, license, language, task family, and quality status for every example.
- Prefer executable/verifiable outcomes over unsupported claims of correctness.

## Repository layout

- `schemas/`: versioned dataset record contracts.
- `data/seeds/`: small, hand-authored starter examples; not a substitute for a large curated corpus.
- `data/eval/`: held-out evaluation examples; never mix into training.
- `scripts/`: offline dataset validation, duplicate audit, and language/task coverage reporting.
- `docs/`: curation, safety, provenance, and evaluation guidance.

## Record format

Use JSONL: one UTF-8 JSON object per line. Each record should include a stable `id`, `task_type`, `prompt`, `target`, `language`, `split`, `provenance`, `license`, and `quality` fields. See `schemas/example.schema.json`.

## Data quality rules

1. Never claim synthetic examples are human-reviewed or benchmark-validated unless that review occurred.
2. Keep evaluation prompts and answers out of training data.
3. Deduplicate exact and near-duplicate content before training.
4. Respect upstream licenses, terms, privacy, and attribution requirements.
5. Do not train on secrets, credentials, private user data, or harmful code payloads.
6. For code examples, include tests or explicit expected behavior where practical.
7. Store concise solution rationales/checks, not unverifiable claims about hidden internal reasoning.

## Language understanding and reasoning

See [`docs/language-understanding-foundation.md`](docs/language-understanding-foundation.md) for the balanced multilingual language-understanding and reasoning strategy. Japanese is a priority, but the dataset is not Japanese-only: it should strengthen shared semantic skills across languages, then connect those skills to reasoning, coding, and tool use.

For Japanese-specific coverage, see [`docs/japanese-language-data.md`](docs/japanese-language-data.md) and [`docs/axral-japanese-review-and-evaluation.md`](docs/axral-japanese-review-and-evaluation.md). The contextual vocabulary and lexical-semantics expansion is in [`data/seeds/vocabulary_semantics_expansion_2026_10.jsonl`](data/seeds/vocabulary_semantics_expansion_2026_10.jsonl); it covers near-synonyms, polysemy, idioms, register, Japanese particles/scope, requirement strength, epistemic language, and multilingual technical terms. These examples remain drafts until reviewed.

## Local checks

Run the structural validator, advisory duplicate audit, and coverage report before proposing dataset changes:

```bash
python -m unittest discover -s tests -v
python scripts/validate_dataset.py data/seeds/*.jsonl
python scripts/audit_dataset.py data/seeds/*.jsonl
python scripts/report_dataset_coverage.py data/seeds/*.jsonl data/eval/*.jsonl
```

The duplicate audit is heuristic and advisory; see [`docs/duplicate-audit.md`](docs/duplicate-audit.md). Coverage and draft-review queue guidance is in [`docs/dataset-coverage-and-review.md`](docs/dataset-coverage-and-review.md). A recorded CI snapshot is available in [`docs/audit-results-2026-10-13.md`](docs/audit-results-2026-10-13.md).

## Starter status

This repository starts with a small illustrative seed set and validation scaffolding. It is not yet a production-scale training corpus. Expand it through licensed sources, executable tests, review, and documented evaluation before model training.
