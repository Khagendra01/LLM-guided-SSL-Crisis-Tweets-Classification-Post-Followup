# AUDIT 351–500 Recovery Status

## Current state

- `humaid_500_model_annotations.csv` contains **500/500** assistant/model annotations (`AUDIT0001`–`AUDIT0500`).
- The surviving source/hidden-key mapping contains **350/500** rows (`AUDIT0001`–`AUDIT0350`).
- Therefore `AUDIT0351`–`AUDIT0500` have assistant labels but are not currently traceable back to their original tweet/HumAID/GPT-4o source row in the surviving checkpoint.

## Why the missing 150 were not silently regenerated

The documented deterministic sampler was rerun against the current fork snapshot. The regenerated ordering did **not** reproduce the existing `AUDIT0001`–`AUDIT0350` mapping. Appending regenerated rows 351–500 would therefore risk attaching the wrong source tweets to already-recorded assistant annotations.

## Required acceptance test

Any recovered/regenerated mapping must first reproduce the existing 350 rows **exactly** by `annotation_id`, `event`, and `tweet_id`. Only after that check passes should rows `AUDIT0351`–`AUDIT0500` be accepted.

## Historical source blob fingerprints

- `california_wildfires_2018`: `02f92071418758b489c9423087326217171ff6e9`
- `canada_wildfires_2016`: `88f9b3faee7796d88ecc9cc095231d2f0594aa78`
- `cyclone_idai_2019`: `77762095367a210069f0e0939bcfcdb8ff337213`
- `hurricane_dorian_2019`: `51a3470da0aba7517258e0f33790674353eb4e77`
- `hurricane_florence_2018`: `0b202ea28f35488ed4d3f902dd81ca892329004a`
- `hurricane_harvey_2017`: `b1f9f7a04749bdc5d9a052016747109b09e52b07`
- `hurricane_irma_2017`: `fd18abdef4f8d8541d76a553cf527545d3c60ca3`
- `hurricane_maria_2017`: `981885453645895877fbc70d25e89a71ef8b7901`
- `kaikoura_earthquake_2016`: `9ab4a8eec7b30cf23d01b7e8e881914f7fc06927`
- `kerala_floods_2018`: `9e11e21950cad2eaa2b8c3516ae19798f2cc1a21`

## Current fork blob fingerprints

- `california_wildfires_2018`: `4ff8c4946b30f8eea4d17f31e760e89119587e38`
- `canada_wildfires_2016`: `a97ca25b9fe789bcc096a073b8c24cfd140cc535`
- `cyclone_idai_2019`: `b48343c62be1bbaa5a43af348ed83e9400a1f7b6`
- `hurricane_dorian_2019`: `99636c941ffabd92a8edc950fde42c0b14153f3f`
- `hurricane_florence_2018`: `dc6afc72cea4d6d1e9ba15208f248d5375711b12`
- `hurricane_harvey_2017`: `0f1c5ab0b01567bf1d8f3f18d63efc4e6c924fa4`
- `hurricane_irma_2017`: `22eaceb4055725c64d57a6f72b68831c3ce970c3`
- `hurricane_maria_2017`: `b7b215ed55b6f1db0f1dbb5b3221e27b8540d8e6`
- `kaikoura_earthquake_2016`: `cec60827ffe7ce59b256fac099d90580a9b2960b`
- `kerala_floods_2018`: `bc63719c0c62fdf181a895f3d58a3017b95ca5d1`

These differing blob SHAs are a provenance clue. The historical source snapshot or an old intermediate selected-row file is the preferred recovery source.

## Safe reviewer interpretation

Treat the first 350 joined rows as the currently traceable model-audit subset. Treat the 500 assistant annotations as complete annotation output, but do **not** claim full 500-row source traceability until the missing mapping is recovered. The labels are assistant/model audit labels produced under the user-directed annotation workflow; they are not independent new human ground truth.
