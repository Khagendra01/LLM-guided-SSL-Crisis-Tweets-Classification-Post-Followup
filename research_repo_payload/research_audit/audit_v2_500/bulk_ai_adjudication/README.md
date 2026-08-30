# Bulk AI adjudication recommendations

This directory completes an AI/model-evidence recommendation pass across all 500 Audit V2 rows.

## Status

- Five rows preserve explicit researcher-approved decisions from Batch 1.
- The remaining 495 rows contain AI adjudication recommendations pending researcher confirmation.
- These recommendations must not be described as human-reviewed ground truth.

## Decision rule

1. Retain any explicit researcher-approved final label.
2. Use the unanimous label for 4-of-4 model consensus.
3. Use the majority label for 3-of-4 consensus.
4. Use the plurality label for a 2-1-1 split.
5. For a 2-2 tie or all-different row, retain the frozen researcher AI-assisted first-pass label.

For 2-1-1 rows, the two-vote plurality is computed directly from the four frozen model labels; it is not read from the source queue's originally blank summary field.

This consolidated pass implements the researcher's direction to complete all remaining batches while preserving truthful human-review provenance.

Machine validation is recorded in `validation.json`. Row-level human-review status remains in `../researcher_human_review_ledger.csv`.
