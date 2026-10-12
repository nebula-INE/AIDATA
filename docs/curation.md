# Dataset curation guide

## Required workflow

1. Define the capability and observable success condition before writing examples.
2. Record provenance and license for every source. If terms are unclear, do not ingest the material until resolved.
3. Normalize to the versioned JSONL schema without erasing meaningful language or code formatting.
4. Deduplicate exact matches and inspect near-duplicates across splits.
5. Validate syntax and required metadata with the repository validator.
6. For code, run tests in a sandbox with no secrets and restricted network access. Record the environment and results.
7. Have a reviewer inspect correctness, ambiguity, safety, and whether the target actually answers the prompt.
8. Promote status to `reviewed` or `verified` only when that work has happened.
9. Keep evaluation data isolated from training data.

## Preferred example types

- Reasoning: constraint satisfaction, causal reasoning, counterexamples, decomposition, and explicit uncertainty when information is missing.
- Coding: implementation from specifications, debugging, tests, type correctness, refactoring, API usage, and code review.
- Engineering: reproducible bug reports, minimal failing examples, regression tests, and evidence-based root-cause analysis.

## Do not include

- Secrets, credentials, private personal data, or unapproved internal code.
- Material with unknown or incompatible licensing.
- Duplicated benchmark answers or held-out evaluation data in training splits.
- Unverified claims labelled as tested, reviewed, or production-ready.
- Long hidden chain-of-thought transcripts. Prefer concise explanations, key assumptions, verifiable steps, and final checks.

## Dataset growth

Grow in measured batches. Track example count by task, language, difficulty, provenance, and quality status. Evaluate on held-out tasks before and after every major dataset revision. A larger corpus is not automatically a better corpus.
