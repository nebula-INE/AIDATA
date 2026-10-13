# Dataset Coverage and Review Workflow

## Generate a coverage report

The report is a composition dashboard, not a score of model intelligence. It reports counts by language, split, task type, quality status, and tags; identifies duplicate IDs and ID overlap between training/validation and eval; and emits a queue of draft records for review.

```bash
python scripts/report_dataset_coverage.py data/seeds/*.jsonl data/eval/*.jsonl
python scripts/report_dataset_coverage.py --json coverage-report.json data/seeds/*.jsonl data/eval/*.jsonl
```

Inspect imbalances by language and task family. Do not infer that a larger count means better coverage: check diversity of prompts, ambiguity classes, answer cardinality, difficulty, and whether examples test meaning in context rather than memorized glosses.

## Review queue and promotion

All newly generated records remain `draft`. Use the report's `draft_review_queue` as a starting index, then record independent decisions in a separate review log. For each item review:

1. Correct interpretation and factual/technical accuracy.
2. Natural phrasing in the stated language and intended register.
3. Whether one answer is required, multiple answers are acceptable, or clarification is needed.
4. Preservation of negation, quantifiers, conditions, exception clauses, temporal order, and modal strength.
5. Counterexamples and plausible alternate interpretations.
6. Duplicate or near-duplicate coverage compared with existing items.
7. Source/license and privacy constraints.

Only set `reviewed` after a named human review and set `verified` only when the claimed verification evidence exists. The dataset report does not promote records, and structural CI does not establish semantic correctness.

## Train/eval leakage

Use `eval` for held-out examples only. Keep its target answers and close paraphrases out of training and prompt tuning. The coverage tool reports exact ID overlap; it does not detect semantic leakage or near-duplicate meaning. Run the duplicate audit and inspect candidates manually before accepting a split as clean.

## Vocabulary growth strategy

Expand vocabulary in contextual families: near-synonyms, polysemy, particles and scope, discourse markers, time/aspect, quantifiers, causality, pragmatic strength, epistemic confidence, register, and technical terminology. Prefer contrastive examples with realistic consequences and counterexamples. Include English and mixed-language material for transfer, while measuring Japanese performance separately. Synthetic records stay drafts until reviewed.
