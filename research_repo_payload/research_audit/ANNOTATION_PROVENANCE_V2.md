# Audit V2 annotation provenance and ownership

## Researcher-owned audit

Audit V2 is a **researcher-owned annotation audit**. The researcher is responsible for the annotation protocol, acceptance of final labels, and any adjudication decisions.

For the researcher's Audit V2 label set:

- **annotation_owner:** `Khagendra01` (researcher)
- **annotation_method:** `AI-assisted first pass under researcher direction`
- **AI role:** annotation assistant applying the fixed HumAID Audit V2 codebook on the researcher's behalf
- **human_reviewer:** `Khagendra01`
- **final_decision_authority:** `Khagendra01`
- **human_review_status:** tracked row-by-row in `audit_v2_500/researcher_human_review_ledger.csv`

The AI-assisted first pass must not be described as an independent human annotation. It is part of the researcher's annotation workflow. A row becomes **human-reviewed** only after the researcher has inspected it and recorded an acceptance or change in the review ledger.

## Pilot calibration/test

Before the 500-item Audit V2, the AI-assisted annotation procedure was tested on a smaller blind pilot and its agreement characteristics against HumAID and GPT-4o were measured.

The pilot provided a calibration/test of how the annotation assistant applied the codebook. **No claim is made here that the pilot itself was personally reviewed or accepted by the researcher unless such review is separately documented.**

Likewise, pilot testing does not automatically mark any of the later 500 rows as human-reviewed. Main-audit review status is recorded separately, row by row.

## Independent comparison models

Claude and Grok/Gemini, when used, are **independent model comparison annotations**. Their outputs are not part of the researcher's label set unless the researcher later reviews/adjudicates a row and explicitly adopts a label.

They should therefore be stored separately from the researcher-owned final audit labels.

## Paper-facing wording

Recommended methods wording before row-level human review is complete:

> Audit V2 used an AI-assisted first-pass annotation workflow conducted on behalf of the researcher under a predefined HumAID codebook. An initial blind pilot was used to test the first-pass procedure and measure its agreement characteristics. AI supplied a first-pass label, optional secondary label, confidence, ambiguity flag, and short rationale. Final annotation responsibility, human review, and adjudication authority remained with the researcher. Human-review status was recorded explicitly at the row level; labels were treated as human-reviewed only after researcher acceptance or revision was recorded.

After all 500 rows have actually been reviewed, the following additional statement is appropriate:

> All final Audit V2 labels were reviewed by the researcher. AI was used only as an annotation assistant for the initial labeling pass; final label acceptance and adjudication remained with the researcher.

Do not use the second statement until the row-level ledger confirms review of all 500 rows.
