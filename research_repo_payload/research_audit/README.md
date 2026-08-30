# Research Audit Follow-up

This directory contains follow-up audit, annotation, and reproduction artifacts generated from the public crisis-classification repository.

## Provenance

### Historical audit

- `model_audit_500/humaid_500_model_annotations.csv` contains the historical assistant/model audit labels.
- `work_in_progress/humaid_500_source_with_hidden_labels_PARTIAL_350.csv` contains only the first 350/500 verified source mappings.
- The historical audit is frozen as **500 annotation decisions / 350 traceable source mappings / 150 unresolved source mappings**. It is not being reconstructed further as part of Audit V2.

### Audit V2

Audit V2 is a new, clean, reproducible **researcher-owned annotation audit**.

- The researcher (`Khagendra01`) owns the audit labels and annotation protocol.
- AI is used as a first-pass annotation assistant acting on the researcher's behalf under the fixed HumAID Audit V2 codebook.
- The researcher is the designated human reviewer and final adjudicator.
- Human-review status is tracked row by row in `audit_v2_500/researcher_human_review_ledger.csv`.
- A row should be described as human-reviewed only after the researcher records acceptance or a corrected label.
- See `ANNOTATION_PROVENANCE_V2.md` for the paper-facing provenance wording.

Independent Claude/Grok/Gemini outputs are retained separately as **model comparison annotations** and are not counted as additional human annotators.

## Audit V2 resources

- `HUMAID_AUDIT_V2_CODEBOOK.md` — refined 10-label codebook and tie-break rules.
- `ANNOTATION_PROVENANCE_V2.md` — annotation ownership, AI-assistance disclosure, and human-review policy.
- `ANNOTATOR_INSTRUCTIONS_V2.md` — blind instructions for independent comparison models.
- `pilot_v2_50/` — calibration pilot and results.
- `audit_v2_500/` — 500-row blind audit, templates, reproducibility manifest, review ledger, and handoff bundle.
- `scripts/generate_audit_v2.py` — deterministic sampler.
- `scripts/score_audit_v2.py` — validation/scoring pipeline.

## Reproduction

- `reproduction/` contains GPT-4o evaluation summaries and canonical LG-CoTrain aggregate results reconstructed from committed repository outputs.

## Label space

The crisis training repository uses 10 trainable HumAID categories. The separate Carlos/Palisades annotation protocol has an additional `Don't know or can't judge` category; that 11th category should not be silently added to these crisis-model training labels.
