# AUDIT0351–AUDIT0500 Recovery Forensics — 2026-08-29

## Scope

This note records the read-only recovery checks performed after reopening the reconstructed reviewer package and the current GitHub repository.

Repository: `Khagendra01/LLM-guided-SSL-Crisis-Tweets-Classification-Post-Followup`

Observed branches:
- `main`
- `research-audit-v2`

Both pointed to commit `edd6c3e4b9fff6d9bc2d205090acea8276113821` at the start of the recovery check.

## Historical source-blob test

The recovery checkpoint preserved 10 historical Git blob SHAs for the event-level GPT-4o train-prediction CSVs.

Those historical blob SHAs were queried in:
1. the follow-up repository, and
2. the public lab repository `deeplearning-lab-csueb/LLM-guided-SSL-Crisis-Tweets-Classification`.

All 10 historical blob lookups returned 404 in both repositories. They are therefore not retrievable as Git blobs from those repositories.

The current `main` files exactly match the *current* blob fingerprints already recorded in the reconstructed package. `research-audit-v2` has the same current fingerprints, not the historical ones.

## Surviving 350 vs current GPT-4o train-prediction files

The 350-row partial key was compared by `(event, tweet_id)` against the current GPT-4o `*_train_pred.csv` files.

Overall:
- surviving partial rows: 350
- tweet IDs found in the current corresponding GPT-4o event file: 133
- exact tweet-text matches among found rows: 130
- HumAID/class-label matches among found rows: 133/133
- GPT-4o predicted-label matches among found rows: 133/133
- GPT-4o confidence matches among found rows: 133/133
- rows exact on text + human label + GPT label + confidence: 130

Per event:

| Event | Surviving rows | Found in current GPT file | Exact full-row inputs |
|---|---:|---:|---:|
| california_wildfires_2018 | 38 | 0 | 0 |
| canada_wildfires_2016 | 28 | 28 | 28 |
| cyclone_idai_2019 | 36 | 36 | 36 |
| hurricane_dorian_2019 | 32 | 0 | 0 |
| hurricane_florence_2018 | 34 | 0 | 0 |
| hurricane_harvey_2017 | 40 | 0 | 0 |
| hurricane_irma_2017 | 35 | 0 | 0 |
| hurricane_maria_2017 | 36 | 36 | 34 |
| kaikoura_earthquake_2016 | 33 | 33 | 32 |
| kerala_floods_2018 | 38 | 0 | 0 |

The three text-only mismatches found in the four surviving-current events were minor text edits/encoding differences; labels and confidence remained identical.

## Original-split spot checks

Representative audit tweet IDs from events missing in current GPT files were checked against the current original HumAID train/dev/test splits.

Found in current original train split:
- `hurricane_florence_2018`
- `hurricane_harvey_2017`
- `hurricane_irma_2017`

Absent from all current original train/dev/test splits:
- `california_wildfires_2018`
- `hurricane_dorian_2019`
- `kerala_floods_2018`

This is evidence of source/dataset-version drift, not merely display ordering.

## Repository history checks

For the checked GPT-4o train-prediction path, repository history shows the file entering the follow-up repository in the initial release commit. No earlier version with the historical blob is present in that repository history.

No additional selected-row recovery artifact was found on `research-audit-v2`; its work-in-progress directory contains only `humaid_500_source_with_hidden_labels_PARTIAL_350.csv`.

## Recovery conclusion

`AUDIT0351`–`AUDIT0500` must **not** be attached to regenerated current-source rows.

The documented acceptance test remains mandatory:

> A candidate historical source reconstruction must reproduce all surviving `AUDIT0001`–`AUDIT0350` mappings exactly by `annotation_id`, `event`, and `tweet_id` before any regenerated `AUDIT0351`–`AUDIT0500` mappings can be accepted.

Until a historical source artifact is recovered, the defensible status remains:
- 500/500 assistant annotation decisions complete.
- 350/500 source mappings verified and traceable.
- 150/500 source mappings unresolved for provenance only.
