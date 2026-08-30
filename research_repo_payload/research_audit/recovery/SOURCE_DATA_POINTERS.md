# Source data locations

The full HumAID/source data are already present in this repository and are intentionally not duplicated in the recovery directory.

Key paths:
- Original HumAID splits: `data/original/{event}/`
- GPT-4o pseudo-labels: `data/pseudo-labelled/gpt-4o/{event}/{event}_train_pred.csv`
- HumAID rules/tie-break guidance: `zeroshot/rules/humaid_rules.py`
- Existing 500 assistant annotations: `research_repo_payload/research_audit/model_audit_500/humaid_500_model_annotations.csv`
- Existing partial 350-row source key: `research_repo_payload/research_audit/work_in_progress/humaid_500_source_with_hidden_labels_PARTIAL_350.csv`
