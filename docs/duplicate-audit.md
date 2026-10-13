# Dataset duplicate audit

The advisory duplicate audit is run in CI against `data/seeds/*.jsonl`.

## Run locally

```bash
python scripts/audit_dataset.py data/seeds/*.jsonl
```

The script:
- normalizes case, punctuation, and whitespace to detect exact prompt duplicates;
- reports near-duplicate candidates using token-set Jaccard similarity (default threshold: `0.82`);
- skips near-match scoring for prompts with fewer than five unique tokens, where scores are unstable;
- never executes content from the dataset;
- exits successfully by default because similarity matches require human judgment.

To make exact normalized duplicates fail a local check, use `--fail-on-exact`. Do not enable that as a required CI gate until existing candidates, if any, have been reviewed.

## Interpretation and limitations

A zero-match report is not proof of semantic diversity or correctness. The current heuristic can miss paraphrases and can flag distinct tasks that share vocabulary. Review any reported candidates manually, including the task target and expected behavior. This check only analyzes prompts; it does not validate answer correctness, licensing, leakage, or training outcomes.
