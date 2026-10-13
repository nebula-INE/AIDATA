# Held-out evaluation data

Keep evaluation prompts and target answers out of all training files. Add examples here only after documenting their source, license, intended capability, and review process. Prefer tasks with objectively checkable outcomes: unit tests, compiler diagnostics, exact-answer problems, dependency constraints, and bug reproduction cases.

Do not report a model as improved from this starter set alone. Track dataset version, model/checkpoint, decoding settings, pass rate, failure categories, and confidence intervals where sample size permits. Keep a private or access-controlled test subset for contamination-resistant checks.

A small synthetic Japanese pilot currently exists at `japanese_language_understanding_eval.jsonl`. Its answer keys remain drafts and must be independently reviewed before benchmark claims. See [`docs/fixed-evaluation-workflow.md`](../../docs/fixed-evaluation-workflow.md) for the scoring worksheet and report process. The pilot is not statistically representative and should not be used to claim broad model improvement.
