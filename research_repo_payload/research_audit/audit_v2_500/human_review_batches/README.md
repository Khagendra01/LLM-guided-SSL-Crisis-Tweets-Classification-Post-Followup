# Researcher-approved human-review batches

Each CSV in this directory records a batch explicitly reviewed and approved by the researcher.

- The batch file preserves the tweet, hidden labels, model consensus, final researcher label, action, and review note.
- `accepted` means the researcher retained the AI-assisted first-pass label.
- `changed` means the researcher selected a different final primary label.
- Batch records do not replace `../researcher_human_review_ledger.csv`; the ledger remains the canonical row-level status file.
- Only explicit researcher confirmations are written here.
