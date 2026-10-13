# Language Understanding Foundation and Reasoning Roadmap

## Objective

Build a reliable language-understanding foundation for a reasoning-focused general AI. Japanese is an important priority, but the goal is not Japanese-only specialization. The model must understand intent, references, logical structure, constraints, uncertainty, and technical language across languages and domains, then use that understanding to solve problems.

## Capability layers

1. **Literal and compositional meaning** — negation, quantifiers, conjunction/disjunction, conditionals, comparison, time, quantities, and scope.
2. **Pragmatics and discourse** — omitted subjects/objects, coreference, ellipsis, corrections, topic shifts, indirect requests, register, and conversational implicature.
3. **Instruction state** — retain constraints across turns, apply explicit updates, preserve still-active restrictions, resolve priority conflicts, and ask focused questions when needed.
4. **Epistemic calibration** — separate observed facts, user reports, assumptions, hypotheses, inferences, and verified results; avoid unsupported certainty.
5. **Task execution understanding** — convert natural-language requirements into plans, acceptance criteria, tests, code changes, and truthful status reports.
6. **Reasoning transfer** — apply the same semantics to mathematics, algorithms, debugging, science, security, and agent/tool use rather than memorizing domain-specific wording.

## Dataset balance

Grow several complementary tracks instead of maximizing Japanese-only volume:

- General language understanding: multilingual and cross-lingual paraphrase, ambiguity, reference, negation, temporal and conditional meaning.
- Formal reasoning: multi-step deduction, constraint satisfaction, counterexamples, causal reasoning, quantitative interpretation.
- Coding and engineering: specification following, implementation, debugging, tests, code review, API and compatibility constraints.
- Tool/agent reliability: action preconditions, confirmation gates, recovery, state tracking, and honest completion reporting.
- Axral specialist data: UTAU, voicebanks, `oto.ini`, `prefix.map`, pitch, rendering, audio diagnostics, and Web/Desktop behavior.

Use Japanese naturally where it is the source language or the task requires it; use English and mixed-language records where they add coverage. Prefer semantically diverse examples over superficial paraphrase counts. Do not assume a single fixed language ratio is optimal: track per-language and per-capability performance, then adjust based on measured gaps.

## Vocabulary and lexical semantics

Vocabulary growth should teach usage, not just word-to-definition pairs. Cover:

- near-synonyms and contrastive meaning (e.g. 暫定対応 / 恒久対応; mitigate / eliminate);
- polysemy, idioms, register, pragmatic implication, and workplace colloquialisms;
- Japanese particles, negation scope, quantifiers, reference words, and grammatical relations;
- requirement strength and epistemic status (must / should / may; assumption / inference / verification);
- technical vocabulary across software, operations, APIs, performance, and reliability;
- English and mixed-language technical communication alongside Japanese.

For each entry, explain meaning in context, contrast likely confusions, and note where meanings depend on domain conventions. Keep candidates as `draft` until reviewed by a competent reviewer. Expand coverage by semantic categories and measured gaps rather than adding many shallow synonyms.

## Record design

Each example should specify, where applicable:

- The user prompt and expected answer or behavior.
- The primary capability being tested and relevant secondary tags.
- Whether the answer is unique, one of several valid answers, or underdetermined.
- Required constraints, prohibited actions, assumptions, and clarification triggers.
- Evidence needed to claim success; executable tests for code tasks when practical.
- Provenance, license, split, and review status.

For ambiguous prompts, the target should not force one interpretation unless context disambiguates it. Use a clarification target when guessing would materially change the outcome. Keep draft data marked `draft` until reviewed; structural validity is not semantic validation.

## Evaluation design

Maintain a fixed, held-out evaluation set that is never copied into training. Group templated variants together to avoid leakage. Score each capability separately:

- Semantic intent and reference resolution.
- Negation, quantifier, temporal, and conditional accuracy.
- Multi-turn constraint retention and correct instruction updates.
- Ambiguity detection and quality of clarification questions.
- Fact/hypothesis separation and calibrated uncertainty.
- Reasoning correctness and constraint coverage.
- Code execution, unit tests, edge cases, and regression behavior.
- Truthfulness of progress and verification reports.

Report sample counts and per-family results, not only one aggregate score. Track regressions by language and task family. Compare the same model, prompt, decoding settings, and evaluation version before and after changes. Dataset growth alone is not evidence that the model improved.

## Review and promotion

1. **Draft:** generated or authored; not independently reviewed.
2. **Reviewed:** a second pass checks language naturalness, answer correctness, alternate valid answers, ambiguity, constraints, provenance, license, and overlap.
3. **Verified:** executable checks pass where applicable and review evidence is recorded.

For difficult examples, use adversarial review: try to construct a reasonable counter-interpretation, identify hidden assumptions, and test whether the target overclaims. Do not mark an item verified solely because JSON/schema/duplicate checks pass.

## Immediate priorities

1. Keep CI green and fix duplicate IDs or split leakage before adding more volume.
2. Expand balanced language-understanding examples across Japanese, English, and mixed technical conversation. Include contextual vocabulary, near-synonym contrasts, polysemy, register, idioms, particles/scope, modal strength, and cross-lingual technical terms; avoid treating isolated dictionary glosses as sufficient.
3. Strengthen reasoning and coding records with verifiable expected behavior and tests.
4. Audit the held-out set for unique answer keys, alternative acceptable answers, and ambiguity.
5. Build a small repeatable evaluation report by capability and language before scaling to much larger volumes.
