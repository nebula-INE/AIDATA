# Japanese Coding Evaluation Review Protocol

Status: draft protocol for the held-out pilot; not a benchmark report.

## Scope

The pilot at `data/eval/japanese_coding_evaluation_pilot_2026_10.jsonl` contains synthetic Japanese coding/debugging scenarios. Its `target` values are proposed answer keys, not independently verified gold answers. Do not publish a model score or claim improvement until the answer keys and scoring criteria have been reviewed by a human.

This pilot is not an evaluation set for the Axral Vocal AI pitch-expression regressor. That repository currently describes a metadata-only singing-pitch model; it does not provide a Japanese coding-question answering interface. Use this pilot only with a model that can receive each prompt and return a textual response.

## Phase 1 — Review and freeze the evaluation set

For every record:

1. Have a reviewer with relevant software-engineering knowledge check the target for technical correctness, security, completeness, and appropriate uncertainty.
2. Check Japanese phrasing for clarity and ensure the prompt contains enough information to justify the target.
3. Check every item-specific criterion in `tests`; revise vague, overlapping, or unobservable criteria.
4. Mark the item as reviewed only after recording reviewer, date, decision, and rationale in a separate review log. Do not silently overwrite the original draft.
5. Resolve disputed answers with a second reviewer. If multiple approaches are valid, score required properties rather than exact wording.
6. Freeze a version/hash of the reviewed evaluation file before running a baseline.

Do not copy evaluation prompts, targets, or close paraphrases into training data. If a failure reveals a gap, create a distinct training example that teaches the underlying skill.

## Phase 2 — Run a reproducible baseline

For each frozen prompt, save the raw model response and record:

- model name and exact version/checkpoint;
- inference endpoint or command and relevant configuration;
- date, environment, decoding parameters, and any system/developer instructions;
- evaluation file version/hash and item ID;
- response text, errors, timeout status, and latency;
- reviewer scores and brief evidence for each score.

Run each prompt independently with the same settings. Do not use evaluation answers as context for the model. Do not tune prompts or model settings against this held-out set and then report the resulting score as an untouched baseline.

If the model cannot answer text prompts, record the run as **blocked / unsupported interface** rather than scoring an unrelated model.

## Phase 3 — Score with an explicit rubric

Score each criterion in `tests` independently:

- **2 — Meets:** clearly satisfies the criterion with technically sound reasoning.
- **1 — Partial:** relevant but incomplete, vague, or missing an important qualification.
- **0 — Misses:** absent, incorrect, unsafe, or contradicts the criterion.
- **N/A — Not applicable:** only when a reviewer documents why the criterion cannot reasonably be assessed from the response.

Also record critical safety/accuracy failures separately (for example, recommending an unsafe path-handling fix or asserting an unverified external guarantee). A high average must not hide a critical failure.

Report at minimum:

- number of reviewed items and number actually scored;
- mean criterion score and score distribution;
- per-domain results (security, debugging, testing, data integrity, time semantics, and so on);
- critical failure count and examples;
- abstentions, errors, and timeouts;
- reviewer agreement or adjudication notes;
- limitations and confidence caveats.

Do not treat draft items or unreviewed targets as authoritative ground truth.

## Phase 4 — Improve without test leakage

Group observed errors into skill categories. Add new training examples that teach the general skill using different scenarios and wording. Keep the evaluation set frozen for comparisons. Use a separate validation set for iteration, and only run a new held-out evaluation when a new reviewed set or predeclared evaluation cycle is ready.

## Result status vocabulary

- `blocked`: no compatible model/interface or prerequisites missing.
- `data_review_pending`: one or more answer keys or criteria are unreviewed.
- `baseline_complete`: frozen reviewed set was run and responses and configuration were saved.
- `scored`: rubric scoring was completed with documented review.
- `comparison_complete`: comparable runs were scored under the same protocol.

A passing JSONL/CI validation verifies structure and tooling only; it does not verify answer-key quality or model capability.
