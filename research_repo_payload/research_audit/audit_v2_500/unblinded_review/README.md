# Unblinded review data

This directory intentionally exposes the Audit V2 hidden key after the researcher first pass and all three external model passes were frozen.

## Contents

- `audit_v2_500_hidden_key_LOCKED.csv` — complete source key with HumAID and GPT-4o labels.
- `researcher_review_queue_prioritized_UNBLINDED.csv` — all 500 rows prioritized for researcher review.
- `canonical_adjudication_queue_UNBLINDED.csv` — scorer-generated disagreement and adjudication evidence.
- `review_queue_summary.json` — consensus, priority, and live review counts.
- `../HUMAN_REVIEW_PROGRESS.json` — current researcher-review progress.
- `../human_review_batches/` — immutable records of explicitly approved review batches.

## Warning

This directory is public and unblinded. Do not use these files, this branch, or a conversation exposed to them for any future supposedly blind annotation pass. Use the earlier clean blind materials and a fresh isolated session if another blind experiment is needed.
