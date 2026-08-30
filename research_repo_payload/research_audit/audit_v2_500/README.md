# Audit V2 — researcher-owned AI-assisted audit and independent model handoff

This directory contains the reproducible 500-item Audit V2 sample and the handoff package for independent comparison models.

## Researcher-owned annotation workflow

The primary Audit V2 annotation set is **owned by the researcher, Khagendra01**.

The annotation workflow is:

1. the researcher defines and controls the HumAID Audit V2 codebook;
2. an AI annotation assistant produces a first-pass primary label, optional secondary label, confidence, ambiguity flag, and short rationale **on the researcher's behalf**;
3. the researcher is the designated **human reviewer and final adjudicator**;
4. each row's review state is tracked explicitly in `researcher_human_review_ledger.csv`;
5. only rows marked accepted or changed by the researcher are treated as **human-reviewed final audit labels**.

The AI first pass is therefore not counted as a separate independent human annotator. See `../ANNOTATION_PROVENANCE_V2.md`.

The complete frozen first pass is:

- `researcher_ai_assisted_first_pass_FROZEN.csv`
- expected SHA256: `38390d45f7e79a274245318a49c289988231b109f8139bb5d8bc933f70512f7a`
- machine validation: `researcher_first_pass_validation.json`

This file is the AI-assisted **first pass**, not a claim that the 500 labels have already been human-reviewed.

## Sample design

- 500 unique tweets.
- 50 tweets from each of the 10 HumAID events.
- Within every event: 25 rows where HumAID and GPT-4o agree + 25 where they disagree.
- All tweets from both earlier 50-item pilots are excluded.
- Deterministic seed: `audit-v2-500-2026-08-30-v1`.
- Sampling algorithm: `audit-v2-stratified-balanced-v1`.
- The generator and source hashes are recorded in `reproduction_manifest.json`.

This deliberately disagreement-enriched sample is an **annotation audit**, not a random test-set accuracy sample.

## Human-review ledger

`researcher_human_review_ledger.csv` contains one row for every `AUDITV2_0001`–`AUDITV2_0500`.

Important fields:
- `annotation_owner=Khagendra01`
- `annotation_method=AI-assisted first pass under researcher direction`
- `human_reviewer=Khagendra01`
- `human_review_status` — initially `pending`, then updated to a reviewed state only after inspection
- `final_primary_label` — the researcher-approved label after review
- `review_action` — e.g. `accepted` or `changed`

Do not describe the full 500 as human-reviewed until the ledger confirms that status row by row.

## Pilot status

The smaller Pilot V2 was used as an AI-assisted calibration/test and its agreement characteristics were measured. The repository does **not** claim that the pilot was personally reviewed or accepted by the researcher unless separate review documentation is added.

## Independent comparison-model handoff

Claude and Grok/Gemini can be used as **independent model comparison annotators**. They are separate from the researcher-owned audit label set.

Give each independent model only:

1. `audit_v2_annotator_bundle.zip`, or equivalently:
   - `audit_v2_500_blind.csv`
   - `../HUMAID_AUDIT_V2_CODEBOOK.md`
   - `../ANNOTATOR_INSTRUCTIONS_V2.md`
2. One fresh isolated conversation/session per model.

Do **not** give a comparison model the repository URL, hidden key, HumAID labels, GPT-4o labels, Pilot V2 results, the researcher's AI-assisted first-pass labels, the human-review ledger decisions, or another model's output.

Ask the model to return CSV only with exactly:

```
annotation_id,primary_label,secondary_label,confidence,ambiguous,reason
```

Recommended filenames:
- `claude_annotations.csv`
- `grok_annotations.csv` or `gemini_annotations.csv`

## Locked key

The 500-row hidden key is intentionally **not committed to the public repository**.

GitHub Actions stores it as the private workflow artifact `audit-v2-hidden-key-locked`. Its file SHA256 is recorded in `HIDDEN_KEY_SHA256.txt` so a later download can be verified before scoring.

Do not download/open the hidden key until the researcher-owned first pass and independent comparison-model outputs have been frozen.

## Scoring

After the model outputs are frozen, download the locked key and run, for example:

```bash
python research_repo_payload/research_audit/scripts/score_audit_v2.py \
  --key audit_v2_500_hidden_key_LOCKED.csv \
  --annotator researcher_first_pass=researcher_ai_assisted_first_pass_FROZEN.csv \
  --annotator claude=claude_annotations.csv \
  --annotator grok=grok_annotations.csv \
  --outdir audit_v2_scoring
```

The scorer validates all 500 IDs and fields before producing agreement, macro-F1, Cohen's kappa, contested-case siding, ambiguity summaries, per-class metrics, and an adjudication queue.

## Paper-facing status

Before row-level researcher review is complete, the defensible wording is:

> Audit V2 used an AI-assisted first-pass annotation workflow conducted on behalf of the researcher under a predefined HumAID codebook. An initial blind pilot was used to test the first-pass procedure and measure its agreement characteristics. Final annotation responsibility, human review, and adjudication authority remained with the researcher.

After every row has actually been reviewed, it is appropriate to add:

> All final Audit V2 labels were reviewed by the researcher.

Claude, Grok, Gemini, GPT-4o, and similar outputs remain model-comparison annotations unless the researcher explicitly adopts a label during human review/adjudication.
