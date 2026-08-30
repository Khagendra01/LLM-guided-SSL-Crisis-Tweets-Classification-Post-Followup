# Audit V2 independent annotator instructions

You are performing an **independent blind model annotation** of crisis tweets using the HumAID Audit V2 codebook.

## Inputs you may use

Use only:
1. `audit_v2_500_blind.csv`
2. `HUMAID_AUDIT_V2_CODEBOOK.md`

Do **not** inspect the repository's original labels, GPT-4o predictions, hidden key, prior ChatGPT annotations, or another annotator's output.

## Required output

Return a CSV with exactly these columns, in this order:

```
annotation_id,primary_label,secondary_label,confidence,ambiguous,reason
```

Requirements:
- preserve all 500 `annotation_id` values exactly and once each;
- one primary label from the 10-label codebook;
- secondary label is optional and must differ from primary;
- confidence must be integer `1`, `2`, or `3`;
- ambiguous must be `yes` or `no`;
- reason should be concise (preferably <= 25 words);
- base the decision only on the supplied event and visible tweet text;
- do not browse/search for the tweet or infer its hidden source label;
- output **CSV only**, with no Markdown fence or prose before/after it.

These outputs are model annotations. They must not be described as independent human ground truth.
