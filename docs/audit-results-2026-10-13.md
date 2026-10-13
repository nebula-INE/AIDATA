# AIDATA automated audit snapshot — 2026-10-13

## Latest verified run

The GitHub Actions workflow validated commit `59e0e934f95b3c7a1a7acdbfeb6e20848ac087b4`, including the language-understanding foundation additions.

- JSONL records validated: **417**
- Exact normalized prompt duplicates: **0**
- Near-duplicate candidates at the default 0.82 threshold: **0**
- Validator unit tests: **passed**
- Dataset validation: **passed**
- GitHub Actions workflow: **passed**

Workflow run: https://github.com/nebula-INE/AIDATA/actions/runs/38392650490

## Recent issue and resolution

The initial Japanese instruction expansion used IDs that overlapped with an existing file. The validator caught the 40 duplicate IDs, the IDs were changed to the distinct `language.ja.instruction_understanding.*` namespace, and the follow-up validation passed in run [38392522311](https://github.com/nebula-INE/AIDATA/actions/runs/38392522311). The failed initial run remains part of the audit history: [38391894783](https://github.com/nebula-INE/AIDATA/actions/runs/38391894783).

## What this does not establish

This is a structural and heuristic audit, not a human quality review. It does not establish that all targets are semantically correct, that illustrative `tests` strings are executable, that examples improve a model, or that the corpus is ready for training. Synthetic examples remain `draft` until reviewed. Duplicate-audit results are heuristic and cannot guarantee semantic diversity or the absence of train/evaluation leakage.
