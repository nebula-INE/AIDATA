# Fixed-fixture verification runner

The fixed-fixture runner provides repeatable execution of repository-owned test
suites without evaluating code or commands embedded in dataset records.

## List and run fixtures

```bash
python scripts/verify_fixed_fixtures.py --list
python scripts/verify_fixed_fixtures.py --fixture dataset-validator
python scripts/verify_fixed_fixtures.py \
  --fixture dataset-validator \
  --fixture eval-leakage \
  --timeout 60 \
  --report artifacts/fixed-fixture-report.json
```

Fixture IDs are mapped in `scripts/verify_fixed_fixtures.py` to fixed test-file
patterns. The CLI accepts only registered IDs; it does not accept arbitrary
module names, shell commands, paths, or test selectors. Each suite runs in a
separate subprocess with a timeout, stdin closed, and a reduced environment.
The JSON report records exit status, duration, timeout, command, and captured
output. A timeout is reported as `timeout`, never as a pass.

## Important security and quality limits

- This runner executes trusted, repository-owned tests only. Dataset-provided
  source code, `tests` strings, URLs, and commands remain untrusted and are
  never passed to this runner.
- A subprocess and timeout are useful controls, but this implementation is
  **not an OS-level sandbox**. Do not use it to execute arbitrary or unreviewed
  code. For hostile-code testing, use a separately provisioned disposable
  environment with network disabled, no secrets, resource limits, and
  filesystem isolation.
- A successful fixture run means only that the selected repository test suite
  exited successfully in that environment. It does not establish that every
  dataset answer is correct and does not automatically change
  `quality.status` from `draft` to `reviewed` or `verified`.
- Record the commit SHA, runtime, and report when using the results as evidence.
  Review fixture scope and expected behavior before relying on a passing result.

## Current scope

The initial registry covers dataset validation, duplicate auditing, train/eval
leakage checks, coverage reporting, review workflow, and response evaluation.
It is deliberately narrow: add a fixture only when its test file is part of the
repository and its scope is reviewed. Do not derive fixture mappings from
dataset content.
