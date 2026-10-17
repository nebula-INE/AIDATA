# Reproducible Evaluation Run Records

This protocol records enough information to reproduce and audit an AIDATA evaluation. It complements the [fixed evaluation workflow](fixed-evaluation-workflow.md); it does not claim that the current draft pilot is a validated benchmark.

## What must be frozen

For each comparison, retain or identify:

- **Evaluation data:** exact path, Git commit, and SHA-256 of each JSONL file used.
- **Rubric:** exact rubric document/version and SHA-256 if stored as a file.
- **Predictions:** immutable raw output file for each model/run, with SHA-256; never overwrite a prior run.
- **Model and inference settings:** provider/model ID, checkpoint or API version when available, system/prompt template version, decoding settings, tool/retrieval configuration, and run timestamp with timezone.
- **Scoring:** worksheet hash, reviewer IDs or pseudonyms, rubric version, score changes/adjudication notes, and the commit of the summarizer.
- **Execution context:** Python version, dependency lockfile or environment specification, command line, exit status, and report hash.

If a field is unavailable (for example, a hosted model's hidden checkpoint), write `unknown` rather than inventing a value. Do not put API keys, access tokens, private reviewer details, or other secrets in the manifest.

## Hash files

Run from the repository root. These commands print SHA-256 digests without changing the source files.

**macOS / Linux**
```bash
shasum -a 256 data/eval/japanese_language_understanding_eval.jsonl predictions.jsonl review-scored.csv report.md
```

**Windows PowerShell**
```powershell
Get-FileHash data/eval/japanese_language_understanding_eval.jsonl,predictions.jsonl,review-scored.csv,report.md -Algorithm SHA256
```

Record the Git commit separately; a hash identifies exact bytes, while a commit identifies repository history. For multiple evaluation files, record each file individually.

## Run-record template

Copy this template to a new file per run (for example, `reports/run-record-2026-10-17.json`) and fill it in. Keep records append-only; do not reuse a record for a changed dataset, prompt, model, or scoring pass.

```json
{
  "record_schema_version": 1,
  "run_id": "replace-with-unique-id",
  "created_at": "2026-10-17T00:00:00+09:00",
  "repository": "nebula-INE/AIDATA",
  "evaluation": {
    "files": [
      {
        "path": "data/eval/japanese_language_understanding_eval.jsonl",
        "git_commit": "full-commit-sha",
        "sha256": "sha256-of-exact-file-bytes"
      }
    ],
    "split": "eval",
    "human_review_status": "draft"
  },
  "rubric": {
    "version": "replace-with-version-or-commit",
    "sha256": "sha256-if-file-based"
  },
  "model_run": {
    "provider": "replace-or-unknown",
    "model": "replace-with-exact-model-id",
    "model_version": "replace-or-unknown",
    "prompt_template_version": "replace-with-version",
    "decoding_settings": {},
    "tool_and_retrieval_config": "replace-or-none",
    "started_at": "replace-with-ISO-8601-timezone",
    "completed_at": "replace-with-ISO-8601-timezone"
  },
  "artifacts": {
    "raw_predictions_path": "predictions.jsonl",
    "raw_predictions_sha256": "sha256-of-exact-file-bytes",
    "review_worksheet_path": "review-scored.csv",
    "review_worksheet_sha256": "sha256-of-exact-file-bytes",
    "report_path": "report.md",
    "report_sha256": "sha256-of-exact-file-bytes"
  },
  "scoring": {
    "reviewer_ids_or_pseudonyms": [],
    "independent_reviewers": 2,
    "adjudication_status": "pending",
    "unresolved_disagreements": 0
  },
  "execution": {
    "python_version": "replace-with-version",
    "dependency_lockfile": "path-or-none",
    "command": "python scripts/evaluate_responses.py summarize review-scored.csv --output report.md",
    "exit_status": 0,
    "summarizer_commit": "full-commit-sha"
  },
  "limitations": [
    "State unavailable model metadata.",
    "State draft answer-key or small-sample limitations."
  ]
}
```

The values above are placeholders, not a record of a real experiment. Never report a successful run until the command has actually been executed and its exit status checked.

## Recommended sequence

1. Confirm the evaluation set and answer keys have been reviewed. Current synthetic pilot items marked `draft` are not benchmark-grade until reviewed.
2. Save raw predictions as a new immutable file; check that IDs match the frozen evaluation set.
3. Hash the evaluation files, prompt/config artifacts, and raw predictions.
4. Prepare the scoring worksheet with `scripts/evaluate_responses.py prepare ...`; use the optional blind-review workflow when feasible.
5. Have reviewers score independently, preserve the original score sheets, and document adjudication instead of silently replacing disagreements.
6. Summarize only after validation succeeds. Hash the completed worksheet and report, then complete the run record.
7. For comparisons, verify the evaluation file hashes and rubric version match. If they differ, label the results as different-set comparisons rather than directly comparable runs.

## Interpretation guardrails

- A matching hash establishes byte identity, not correctness, representativeness, or freedom from training contamination.
- A successful validator or report command establishes structural validity, not semantic correctness.
- Draft synthetic answer keys must not be treated as authoritative until independent human review.
- Small pilots support debugging and exploratory comparison, not broad claims about model capability or statistical significance.
- Store blind-review identity manifests separately with restricted access; never include them in a public run record.
- Do not include secrets or private user data in prediction artifacts or manifests.
