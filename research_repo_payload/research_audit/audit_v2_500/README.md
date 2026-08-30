# Audit V2 — 500-item blind model-annotation package

This directory is the public, reproducible handoff for independent **model annotators** such as Claude and Grok/Gemini.

## Sample design

- 500 unique tweets.
- 50 tweets from each of the 10 HumAID events.
- Within every event: 25 rows where HumAID and GPT-4o agree + 25 where they disagree.
- All tweets from both earlier 50-item pilots are excluded.
- Deterministic seed: `audit-v2-500-2026-08-30-v1`.
- Sampling algorithm: `audit-v2-stratified-balanced-v1`.
- The generator and source hashes are recorded in `reproduction_manifest.json`.

This deliberately disagreement-enriched sample is an **annotation audit**, not a random test-set accuracy sample.

## Give each independent model only

1. `audit_v2_annotator_bundle.zip`, or equivalently:
   - `audit_v2_500_blind.csv`
   - `../HUMAID_AUDIT_V2_CODEBOOK.md`
   - `../ANNOTATOR_INSTRUCTIONS_V2.md`
2. One fresh isolated conversation/session per annotator.

Do **not** give an annotator the repository URL, hidden key, HumAID labels, GPT-4o labels, the Pilot V2 results, ChatGPT's pilot answers, or another annotator's output.

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

Do not download/open the hidden key until the independent annotation outputs have been frozen.

## Scoring

After both model outputs are frozen, download the locked key and run:

```bash
python research_repo_payload/research_audit/scripts/score_audit_v2.py \
  --key audit_v2_500_hidden_key_LOCKED.csv \
  --annotator claude=claude_annotations.csv \
  --annotator grok=grok_annotations.csv \
  --outdir audit_v2_scoring
```

The scorer validates all 500 IDs and fields before producing agreement, macro-F1, Cohen's kappa, contested-case siding, ambiguity summaries, per-class metrics, and an adjudication queue.

## Scientific wording

Claude, Grok, Gemini, ChatGPT, and GPT-4o outputs are **model annotations**. They are useful as independent model judgments and for selecting cases for adjudication, but they are not independent human ground truth. For a paper claiming corrected/adjudicated ground truth, use human review/adjudication for the final disputed cases or full audit.
