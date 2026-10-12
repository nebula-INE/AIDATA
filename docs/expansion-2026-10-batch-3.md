# AIDATA expansion batch 3 (2026-10)

This batch adds 27 synthetic seed records across three JSONL files:

- `data/seeds/python_practical.jsonl` — practical Python utilities, filesystem safety, parsing, concurrency, and collection algorithms.
- `data/seeds/testing_and_quality.jsonl` — property-based testing, deterministic concurrency tests, regression design, exception safety, and secure subprocess use.
- `data/seeds/cross_platform_audio.jsonl` — audio-buffer latency, resampling, RMS/normalization, clipping diagnostics, render-silence regression checks, voicebank alias scope, and desktop/web parity.

## Curation status

All examples are marked `train`, `synthetic`, `CC0-1.0`, and `draft`. The `tests` field contains a mix of assertion-like checks and test-design notes; it is **not yet a uniform executable test format**, and these checks have not been run automatically. Do not mark examples `verified` until answers are independently reviewed and executable checks are actually run where applicable.

## Next quality gates

1. Normalize executable tests into a defined harness (for example, Python pytest modules with explicit imports and fixtures).
2. Run the repository validator across every JSONL file and validate against the JSON Schema, including additional-property checks.
3. Add near-duplicate detection and review answer correctness, edge cases, security, and cross-platform assumptions.
4. Keep held-out evaluation examples outside all training JSONL files; this batch intentionally adds no eval data.

This is a synthetic seed expansion, not evidence of model training or improved model performance.
