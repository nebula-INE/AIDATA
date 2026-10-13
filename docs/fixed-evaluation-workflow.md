# Fixed Evaluation and Model Comparison

## Purpose

This workflow compares saved model responses on the same frozen evaluation set. It prepares a human-scoring worksheet and summarizes scores by model, language, task type, tag, and rubric axis. It does not call a model API and does not automatically determine semantic correctness.

## 1. Freeze the evaluation set

Use a reviewed, version-controlled set under `data/eval/`. Keep its prompts and targets out of training, prompt tuning, and retrieval. The current Japanese pilot includes synthetic draft answer keys; review those keys before using results as a benchmark. It is a small pilot, not a statistically representative Japanese-language test.

Record the commit SHA of the evaluation data and rubric. Never add evaluation items to training files. The current dataset validator catches duplicate IDs, while the coverage report catches exact train/validation/eval ID overlap; neither proves semantic non-contamination.

## 2. Save predictions

Export one JSON object per line from each model run. Required fields: `id`, `prediction`, `model`. Recommended metadata: `model_version`, `prompt_template_version`, `decoding_settings`, and `run_date`.

Example:

```json
{"id":"language.ja.eval.001","prediction":"回答本文","model":"axral-baseline","model_version":"checkpoint-or-api-version","prompt_template_version":"system-prompt-v1","decoding_settings":{"temperature":0},"run_date":"2026-10-13"}
```

The evaluation harness joins predictions by ID and creates a CSV review worksheet. Missing predictions remain visible and are not silently counted as correct.

```bash
python scripts/evaluate_responses.py prepare \
  data/eval/japanese_language_understanding_eval.jsonl \
  predictions.jsonl --output review.csv
```

Reviewers should see the prompt and model output before consulting the reference answer where practical, then compare against the reviewed answer key. Keep raw model outputs immutable; score copies in the worksheet.

## 3. Human scoring rubric

Score each applicable axis from 0 to 2:

- `meaning`: 0 wrong; 1 partly correct; 2 correct.
- `constraints`: 0 material constraint omitted/reversed; 1 minor omission; 2 all material constraints preserved.
- `ambiguity_calibration`: 0 unjustified certainty/guess; 1 partial calibration; 2 handles ambiguity and asks a targeted question when needed.
- `evidence_discipline`: 0 unsupported claims; 1 partly separates evidence and inference; 2 clearly distinguishes facts, hypotheses, and verification needs.
- `context_tracking`: 0 misses/invents context; 1 partial; 2 tracks context accurately and admits missing context.
- `language_quality`: 0 unnatural/misleading; 1 understandable but awkward; 2 natural and appropriate.

Use `N/A` only when an axis genuinely does not apply. Leave a score blank while unreviewed. Add reviewer identity and short notes for every 0 or 1. Prefer two independent reviewers for high-impact comparisons and adjudicate disagreements.

## 4. Summarize and compare

After completing the CSV scores:

```bash
python scripts/evaluate_responses.py summarize review.csv --output report.md
```

To compare models, combine rows from separate runs into one scoring CSV while preserving a row per (model, item) and including run metadata columns. The report includes per-model, per-language, per-task, per-tag, and per-axis results. Review per-item regressions and category shifts; do not rely only on the overall mean.

## 5. Reporting rules

Report item count, number of scored ratings, denominator, model/checkpoint, prompt template, decoding settings, evaluation commit, rubric version, reviewer, and unresolved disagreements. Avoid claiming a statistically significant gain from a small pilot. For larger evaluations, add confidence intervals and repeated runs where appropriate.

## Current limitations

- The harness requires saved model outputs; it does not itself access an inference endpoint or train a model.
- Scoring is human-led, not an automatic LLM-as-judge score.
- The current Japanese pilot's answer keys remain draft until independently reviewed.
- Exact ID overlap checks do not detect paraphrase or semantic leakage.
