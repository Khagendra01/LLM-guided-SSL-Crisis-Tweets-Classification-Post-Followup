# Pilot V2 results — AI-assisted calibration/test

The 50-item Pilot V2 was sampled fresh from the current repository snapshot and excluded all 50 tweets from the earlier pilot. It contains 5 tweets per event and was deliberately stratified to 25 HumAID↔GPT-4o agreement rows and 25 disagreement rows. Therefore these are **audit agreement statistics**, not ordinary test-set accuracy estimates.

The AI-assisted pilot annotations were produced on behalf of the researcher and frozen in commit `7764df79dd75bd8733a472733c0a34cd6ac6fcb1` before the hidden labels were inspected. The pilot was used to test/calibrate the annotation assistant's application of the codebook before the larger Audit V2 first pass.

**Review-status note:** this file does not claim that the researcher personally reviewed or accepted the pilot annotations. Any such human-review claim should be made only if separately documented.

## Primary-label results

| Comparison | Exact agreement | Macro-F1 | Cohen's kappa |
|---|---:|---:|---:|
| AI-assisted first pass ↔ HumAID | 25/50 = **50.0%** | 0.344 | 0.386 |
| AI-assisted first pass ↔ GPT-4o | 40/50 = **80.0%** | 0.607 | 0.748 |
| HumAID ↔ GPT-4o | 25/50 = **50.0%** | 0.371 | 0.406 |

On the 25 deliberately contested HumAID↔GPT-4o rows, the AI-assisted first pass chose:
- GPT-4o's label: **19/25 = 76%**
- HumAID's label: **4/25 = 16%**
- neither: **2/25 = 8%**

On the 25 rows where HumAID and GPT-4o already agreed, the first pass matched that consensus on **21/25 = 84%**.

Allowing the optional secondary label as a plausible alternative increased overlap to:
- HumAID primary-or-secondary match: **35/50 = 70%**
- GPT-4o primary-or-secondary match: **45/50 = 90%**

## Ambiguity signal

The AI-assisted first pass marked 18/50 rows ambiguous.

| Ambiguity flag | n | vs HumAID | vs GPT-4o | HumAID↔GPT-4o |
|---|---:|---:|---:|---:|
| no | 32 | 68.75% | 90.63% | 62.50% |
| yes | 18 | 16.67% | 61.11% | 27.78% |

This is useful evidence that the ambiguity flag identifies genuinely contested items.

## Codebook lessons from consensus misses

Four rows were missed even though HumAID and GPT-4o agreed. They motivated explicit tie-break rules:

1. Active warning/threat status can be `caution_and_advice` even without an imperative.
2. Concrete damage/access disruption should beat generic `other_relevant_information`; road shutdowns belong under infrastructure unless behavioral guidance is the main intent.
3. Generic solidarity/help language without a concrete aid mechanism should not automatically be treated as rescue/donation.
4. `not_humanitarian` should be reserved for genuinely unrelated/metaphorical/entertainment use; claims about a real current disaster generally remain on-topic even when dubious.

The refined V2 codebook captures these rules.

## Methodological status

This pilot tests an **AI annotation assistant within the researcher's workflow**; it does not convert AI output into an independent human annotation and it does not itself establish human review.

The researcher owns the audit workflow and retains final review/adjudication authority. For Audit V2, row-level human review is tracked explicitly. Claude, Grok, Gemini, GPT-4o, and similar systems remain separate model-comparison annotations unless the researcher explicitly adopts a label during review.
