# Research Audit Follow-up

This directory contains follow-up audit and reproduction artifacts generated from the public crisis-classification repository.

## Provenance

- `pilot_50/` contains the blind 50-post human annotation pilot and its hidden key.
- `model_audit_500/humaid_500_model_annotations.csv` contains assistant/model audit labels. These are **not human ground truth** and are **not Professor Li-approved annotations**.
- `reproduction/` contains GPT-4o evaluation summaries and canonical LG-CoTrain aggregate results reconstructed from committed repository outputs.
- `work_in_progress/humaid_500_source_with_hidden_labels_PARTIAL_350.csv` is intentionally marked partial. It contains only the first 350 of 500 deterministic audit-key rows and must not be treated as a complete 500-row source key.

## Audit design

The expanded assistant audit sample was designed for 50 posts per event, with 25 HumAID/GPT-4o agreements and 25 disagreements per event. Final scoring and sensitivity analysis should exclude any overlap with the earlier 50-post pilot when reporting a stricter blind-analysis result.

## Label space

The crisis training repository uses 10 trainable HumAID categories. The separate Carlos/Palisades annotation protocol has an additional `Don't know or can't judge` category; that 11th category should not be silently added to these crisis-model training labels.
