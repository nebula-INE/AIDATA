# Japanese Language Understanding Data

## Scope

AIDATA includes Japanese examples for meaning preservation, context dependence, omitted subjects and objects, particles, negation scope, politeness and register, indirect requests, quantifiers, temporal ordering, ambiguity, paraphrase fidelity, technical communication, and instruction constraints.

The dataset is synthetic and is intended as a curation and evaluation starting point. A record marked `draft` is **not** a human-verified answer key. Dataset size alone does not establish language understanding or model quality.

## Files and split policy

- `data/seeds/japanese_language_understanding.jsonl`: initial 36 Japanese examples, train split.
- `data/seeds/japanese_language_understanding_expansion.jsonl`: additional 40 Japanese examples, train split.
- `data/eval/japanese_language_understanding_eval.jsonl`: 20 held-out examples, eval split.

Do not train on `data/eval/` or use its answer targets for prompt tuning. The CI validator checks both seed and evaluation JSONL files for schema consistency; duplicate auditing currently runs on seeds.

## Review rubric

Before promoting a record from `draft`:

1. **Interpretation:** the target answers the prompt that was actually asked.
2. **Faithfulness:** no condition, negation, quantity, exception, time order, or contrast is dropped or reversed.
3. **Calibration:** ambiguity and missing context are acknowledged; plausible guesses are not presented as facts.
4. **Japanese naturalness:** wording is idiomatic for the intended register and audience.
5. **Answer boundaries:** quoted claims, reported speech, and uncertain statements are not upgraded into verified facts.
6. **Uniqueness:** the item tests a meaningful capability not already covered by a near-duplicate.
7. **Independent review:** a reviewer checks the prompt and target; automated structural validation alone is insufficient.

## Evaluation protocol

For each model version, run the same held-out prompts and record:

- exact/semantic correctness (human rubric);
- constraint preservation;
- ambiguity handling and calibrated uncertainty;
- unsupported inference rate;
- instruction-following and format compliance;
- results by category, not only an overall average.

Keep the model version, prompt template, decoding settings, evaluation date, reviewer, and per-item scores. Compare against a fixed baseline before claiming an improvement. Review the answer keys before treating the current synthetic evaluation set as a benchmark.

## Known limitations

- These examples are synthetic and may contain author bias or incomplete coverage.
- The current held-out set is small and not statistically representative.
- The `tests` field contains review criteria, not executable unit tests.
- Japanese language understanding also needs natural conversation data, dialect/register variation, long-context references, speech/transcription noise, and real task examples with appropriate permissions.
- No claim about trained-model performance should be made from record counts or schema validation alone.
