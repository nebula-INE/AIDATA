# Axral Japanese Understanding: Review and Evaluation Workflow

## Status and honest reporting

The Japanese datasets are synthetic drafts. An assistant-generated pass is useful for triage, but it is not independent human review. Do not change `quality.status` to `reviewed` or `verified` until a named reviewer has inspected the prompt and target. Do not claim model improvement until the same fixed evaluation set has been run against comparable model versions.

## Dataset additions

- `data/seeds/japanese_multi_turn_conversations.jsonl`: 20 examples covering prior-turn references, omitted context, corrections, colloquial reports, multi-condition instructions, prohibited changes, and accurate status reports.
- `data/seeds/axral_technical_japanese.jsonl`: 20 examples covering UTAU aliases, `oto.ini`, `prefix.map`, pitch, rendering, silence, click noise, audio duration, cross-platform paths, test skips, and scope control.
- `data/eval/japanese_language_understanding_eval.jsonl`: held-out baseline set. Never copy its prompts or targets into training or tune prompts against its answer keys.

All newly added training examples are synthetic and marked `draft`. Their inclusion increases coverage; it does not itself demonstrate a model capability gain.

## Human review: per-record worksheet

For each record, reviewers should independently complete the following fields in a review log before discussing disagreements:

1. **Interpretation:** What is the user asking, including references to earlier turns?
2. **Answer cardinality:**
   - `single`: one answer is entailed by the prompt;
   - `multiple`: multiple distinct answers satisfy the prompt;
   - `context_dependent`: the answer depends on omitted context;
   - `clarification_needed`: a necessary detail is missing and guessing would change the outcome.
3. **Expected response behavior:** answer directly, list valid alternatives, state uncertainty, or ask a focused clarification question.
4. **Constraint checklist:** list every condition, exception, prohibition, scope limit, format, platform, and temporal order in the prompt; check whether the target preserves each one.
5. **Evidence calibration:** separate directly stated facts, reasonable hypotheses, and facts requiring verification. In technical examples, an error log is evidence but not automatically proof of root cause.
6. **Japanese naturalness:** assess grammar, register, conversational plausibility, and whether the target sounds like a useful response rather than a test-key fragment.
7. **Answer-key quality:** accept equivalent correct wording; flag over-specific answers, unjustified assumptions, missing alternatives, or cases where asking a question is the correct behavior.
8. **Decision:** `accept`, `revise`, or `retire`; reviewer identifier; date; short rationale.

Keep review metadata in a separate review log until the schema has a dedicated structured review object. Do not use the `tests` field to imply automated tests: for these records it is a review checklist.

## Scoring fixed evaluations

Score each response from 0 to 2 on each axis:

- **Meaning:** 0 = wrong; 1 = partly correct; 2 = correct.
- **Constraints:** 0 = material condition/prohibition omitted or reversed; 1 = minor omission; 2 = all material constraints retained.
- **Ambiguity/calibration:** 0 = unjustified certainty or harmful guess; 1 = uncertainty acknowledged but response is incomplete; 2 = ambiguity handled appropriately, including a targeted question where needed.
- **Evidence discipline:** 0 = claims unsupported facts or presents a hypothesis as proven; 1 = partly distinguishes evidence from inference; 2 = clearly separates facts, hypotheses, and verification needs.
- **Conversation/context tracking:** 0 = misses or invents prior context; 1 = partially tracks it; 2 = correctly tracks available context and admits when it is unavailable.
- **Japanese quality:** 0 = unnatural or misleading; 1 = understandable but awkward; 2 = natural and fit for context.

Maximum is 12 points per item. Mark an axis `N/A` only if it genuinely does not apply and report the denominator transparently; do not silently rescale. Keep per-item scores and failure notes, not just an average. For every run, record model/version, system and prompt template, decoding settings, date, reviewer, dataset revision/commit, and failures by category.

## Comparison protocol

1. Have reviewers inspect the held-out answer keys before using the set as a benchmark.
2. Freeze evaluation records and rubric under version control.
3. Run a baseline and save raw model responses.
4. Score the baseline before changing training data or prompts.
5. Review disagreements and identify failure categories.
6. Add training examples that address the observed failure mode without copying held-out items.
7. Re-run the exact same evaluation with the same scoring rubric and comparable inference settings.
8. Report per-category changes, regression cases, sample size, and limitations. A higher aggregate score alone can hide serious failures.

The current 20-item evaluation set is a small synthetic pilot. It is not statistically representative and is too small to support broad claims about Japanese competence. Expand it only with reviewed, non-duplicative items and keep new evaluation items held out.

## Current limitations

- The new training examples have not received independent human review.
- Answer cardinality is documented as a review requirement but is not yet a required schema field.
- No model responses have been scored by this workflow yet; therefore no measured improvement is claimed.
- Synthetic technical prompts reflect anticipated Axral workflows and should be checked against actual product behavior and logs before promotion.
