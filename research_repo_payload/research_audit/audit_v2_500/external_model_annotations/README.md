# External model annotations

This directory stores the frozen blind comparison-model outputs for Audit V2.

- `claude_audit_v2_500_annotations.csv` — 500/500
- `gemini_audit_v2_500_annotations.csv` — 500/500
- `grok_audit_v2_500_annotations.csv` — 500/500

All three use the required schema:

```
annotation_id,primary_label,secondary_label,confidence,ambiguous,reason
```

They were validated for exactly 500 sequential IDs, valid codebook labels, confidence values 1–3, yes/no ambiguity values, and non-empty row-specific rationales.

These are independent **model-comparison annotations**, not human ground truth. They remain separate from the researcher-owned AI-assisted first pass and from subsequent human review/adjudication.

Gemini's upload contained two empty trailing export columns; those empty columns were removed during canonical normalization without changing any annotation field. The replacement Grok upload supersedes the earlier incomplete/placeholder-tail file.
