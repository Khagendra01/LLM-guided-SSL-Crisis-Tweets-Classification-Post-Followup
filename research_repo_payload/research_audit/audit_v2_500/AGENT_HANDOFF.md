# Audit V2 complete agent handoff

Canonical branch: `audit-v2-scoring-results`

This branch is intentionally **UNBLINDED** for researcher adjudication and review. Do not use it for future blind annotation experiments.

## Start here

- Blind sample: `audit_v2_500_blind.csv`
- Researcher AI-assisted first pass: `researcher_ai_assisted_first_pass_FROZEN.csv`
- External model outputs: `external_model_annotations/`
- Aggregate scoring: `scoring/`
- Full hidden key and review queues: `unblinded_review/`
- Main review file: `unblinded_review/researcher_review_queue_prioritized_UNBLINDED.csv`
- Canonical adjudication queue: `unblinded_review/canonical_adjudication_queue_UNBLINDED.csv`
- Human-review ledger: `researcher_human_review_ledger.csv`
- Codebook: `../HUMAID_AUDIT_V2_CODEBOOK.md`
- Annotation provenance: `../ANNOTATION_PROVENANCE_V2.md`
- Generator: `../scripts/generate_audit_v2.py`
- Scorer: `../scripts/score_audit_v2.py`
- Artifact manifest: `COMPLETE_HANDOFF_MANIFEST.sha256`

## Review order

1. P1: 101 unanimous four-model decisions that differ from HumAID.
2. P2: 78 three-of-four model decisions that differ from HumAID.
3. P3: 90 split or tied model decisions.
4. P4: 231 strong-consensus decisions matching HumAID.

## Critical status

- The researcher first pass, Claude, Gemini, and Grok outputs were frozen before unblinding.
- The hidden HumAID/GPT-4o key is now public on this branch.
- All 500 human-review ledger rows remain `pending`.
- Model consensus is review evidence, not human ground truth.
- Do not describe any row as human-reviewed until the researcher records an explicit acceptance or change.
- Audit V2 is disagreement-enriched: each event has 25 HumAID/GPT-4o agreements and 25 disagreements. Reported agreement rates are audit statistics, not ordinary test accuracy.
