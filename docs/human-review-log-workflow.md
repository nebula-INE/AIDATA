# Human Review Log Workflow

## Export a review queue

Create a CSV worksheet from training/validation JSONL. The worksheet includes the prompt and target plus blank fields for reviewer, date, decision, interpretation, answer cardinality, expected behavior, constraints, evidence calibration, language quality, and rationale.

```bash
python scripts/review_dataset.py export data/seeds/*.jsonl --output reviews/training-review.csv
```

Keep this file in a review branch or an access-controlled location while it contains evaluation material or private notes. For held-out evaluation answer keys, do not export them into a training review queue or commit completed answer-key notes to public training paths.

## Record the review

For every reviewed row, fill in:

- `reviewer`: stable reviewer ID or name.
- `review_date`: ISO date `YYYY-MM-DD`.
- `decision`: `accept`, `revise`, or `retire`.
- `answer_cardinality`: `single`, `multiple`, `context_dependent`, or `clarification_needed`.
- `expected_behavior`: `answer`, `list_alternatives`, `state_uncertainty`, or `ask_clarification`.
- `interpretation`, `constraint_checklist`, `evidence_calibration`, `language_quality`, and `rationale`: short evidence of what was checked and why the decision was made.

Accept equivalent correct wording. Mark ambiguous prompts as context-dependent or clarification-needed rather than forcing a single answer. Check negation, quantifiers, exceptions, scope, temporal order, technical accuracy, and register. For coding items, run the relevant tests separately and record the command/environment/results in the rationale or linked review artifact.

## Validate the completed log

```bash
python scripts/review_dataset.py validate reviews/training-review.csv --output reviews/review-summary.md
```

Validation checks required fields, decision/cardinality/behavior vocabularies, date format, and duplicate IDs. It does not establish that the reviewer is correct or independent.

## Dataset promotion

The tool deliberately does not edit dataset files or change `quality.status`. After review, use a separate reviewed change to update accepted records with the reviewer and evidence in metadata; keep `revise` records as `draft`, and do not silently delete `retire` decisions. Resolve reviewer disagreements before promotion. Use `verified` only after any applicable executable checks also pass.
