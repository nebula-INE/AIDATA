# Evaluation Plan

## Purpose

Measure whether a model can solve unseen tasks reliably, not whether it can reproduce seed examples. Dataset growth alone is not evidence of model improvement.

## Required benchmark families

- Multi-step reasoning: constraints, counterexamples, contradictory requirements, uncertainty, causal inference.
- Coding: implementation from specifications, algorithms, types, edge cases, complexity.
- Debugging: root-cause hypotheses, minimal reproductions, concurrency, resource lifetime, error handling.
- Testing: boundary cases, regression tests, failure injection, idempotency.
- Engineering judgment: trade-offs, performance measurement, security, API contracts.

## Split policy

1. Keep training records under `data/seeds/` with `split=train`.
2. Store validation and held-out evaluation records separately. Do not copy held-out prompts or target answers into training files.
3. Restrict changes to held-out examples to reviewed benchmark-maintenance changes, and record why each change was needed.
4. Avoid near-duplicates across splits. Check for shared wording, solution templates, and algorithm variants that make evaluation too easy.
5. If examples are generated from a template, group related instances and place the whole group in one split.

## Scoring

Use task-appropriate checks:
- Code: compile/type-check, unit tests, edge cases, and timeouts.
- Reasoning: a rubric for constraint coverage, assumptions, counterexamples, and justified conclusions.
- Debugging: whether the proposed cause is supported by evidence, whether a falsifiable test is suggested, and whether the fix addresses the cause.
- Safety and reliability: no secrets, destructive commands without safeguards, or unsupported certainty.

Report pass rate, per-family scores, sample counts, confidence intervals where practical, and common failure categories. Compare against a baseline model and a baseline prompt.

## Promotion gates

- `draft`: authored but not independently reviewed.
- `reviewed`: a reviewer checked correctness, clarity, provenance, license, and ambiguity.
- `verified`: executable checks passed where applicable and the review evidence is recorded.

Never promote a record just because it parses as JSON. Do not claim model improvement until a reproducible training run improves held-out results without unacceptable regressions.
