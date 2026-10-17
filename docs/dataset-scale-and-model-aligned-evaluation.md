# Dataset scale and model-aligned evaluation

## Current limitation

A small seed repository is useful for schema validation, workflow testing, and early error discovery. It is not a substitute for the existing instruction corpus at roughly 100,000 examples. Adding a few hundred examples should not be presented as a material training-scale increase or as evidence of improved model capability.

All synthetic records remain `quality.status: draft` until independent human review. Passing JSON/schema validation checks structure, not whether an answer key is linguistically correct, unique, or appropriate for the target model.

## Evaluation by difficulty

Do not use a benchmark dominated by abstract lexical distinctions or multi-step tasks to judge a model with roughly 55M parameters. Near-zero accuracy on tasks outside the model's effective capability range can hide useful changes and makes score interpretation poor.

Use separate, non-interchangeable tiers:

1. **Tier A — basic control and comprehension:** short literal statements, simple arithmetic, format constraints, direct extraction, simple Python syntax, and clear positive/negative instructions. This repository adds a draft pilot at `data/eval/japanese_small_model_baseline_pilot_2026_10.jsonl`.
2. **Tier B — practical competence:** simple debugging, short multi-step procedures, small code changes, and tests with explicit expected outputs.
3. **Tier C — advanced reasoning and research:** scope ambiguity, subtle lexical semantics, multi-source evidence, version conflicts, security reviews, and complex debugging.

Report each tier separately. Do not average the tiers into a single score that obscures the capability gap. If Tier A is already near ceiling, add harder items; if a tier is near zero for every model, simplify or treat it as a capability ceiling rather than a useful discriminator.

## Scale-up plan

- **Immediate:** correct suspect answer keys; review all benchmark prompts and targets independently; label ambiguity and acceptable alternatives; keep all unreviewed records in draft.
- **Next:** build a reviewed, deduplicated core set of a few hundred to low thousands of high-value examples across error types, not merely paraphrase volume. Use real, permissioned issue/test cases where licensing and privacy allow.
- **Then:** expand in batches with measured source provenance, near-duplicate detection, task-family balance, and reviewer agreement. Keep a frozen held-out set private or access-controlled to reduce contamination.
- **Training integration:** compare candidate records against the existing ~100k instruction corpus, remove duplicates, define sampling/weighting, and run controlled ablations. Dataset size alone does not predict gain.
- **Evaluation:** freeze model checkpoint, tokenizer, prompt, decoding, runtime, and dataset revision; report per-tier accuracy, confidence intervals where sample size supports them, failure categories, and regression examples.

## Minimum evidence before claims

- Human review status and reviewer rubric are explicit.
- A benchmark has enough examples per category to support the claim being made.
- Exact model/checkpoint and inference settings are recorded.
- Results are compared to a fixed baseline on the same items.
- Any improvement claim is based on an actual controlled run, not repository growth or CI success.

## Limitations of the new pilot

The new Tier A file is synthetic and small. It is a starting point for checking whether the evaluation matches a small model's reachable skills, not a validated benchmark. Its answers must be reviewed and its items expanded before making performance claims.
