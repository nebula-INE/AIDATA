# Record-level content-quality audit

Run the advisory record-level audit across all training seeds before considering a batch for promotion:

```bash
python scripts/audit_record_quality.py data/seeds/*.jsonl
python scripts/audit_record_quality.py --json data/seeds/*.jsonl > record-quality-audit.json
```

The report flags duplicate IDs, normalized exact duplicate prompts, missing targets, missing checks, generic placeholder checks, literal `\\n` sequences in prompts, and records marked reviewed without a reviewer field. Findings are review signals, not automatic judgments that a record is wrong.

Use `--fail-on duplicate_id` or repeat `--fail-on` with selected finding kinds when a specific class has been triaged and is ready to become a gate. By default the command is advisory and exits successfully, so the existing draft corpus can be measured before adopting stricter CI policy.

This script reads JSON only and never executes dataset-provided code. A populated `tests` field is not proof of executable verification; generic checks are deliberately surfaced. Synthetic records must remain `draft` until a human reviewer records the evidence and disposition. This audit does not establish factual correctness, license compliance, absence of semantic duplicates, or model improvement.
