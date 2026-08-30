# Pilot V2 results

The 50-item Pilot V2 was sampled fresh from the current repository snapshot and excluded all 50 tweets from the earlier pilot. It contains 5 tweets per event and was deliberately stratified to 25 HumAID↔GPT-4o agreement rows and 25 disagreement rows. Therefore these are **audit agreement statistics**, not ordinary test-set accuracy estimates.

The ChatGPT annotations were frozen in commit `7764df79dd75bd8733a472733c0a34cd6ac6fcb1` before the hidden labels were inspected.

## Primary-label results

| Comparison | Exact agreement | Macro-F1 | Cohen's kappa |
|---|---:|---:|---:|
| ChatGPT ↔ HumAID | 25/50 = **50.0%** | 0.344 | 0.386 |
| ChatGPT ↔ GPT-4o | 40/50 = **80.0%** | 0.607 | 0.748 |
| HumAID ↔ GPT-4o | 25/50 = **50.0%** | 0.371 | 0.406 |

On the 25 deliberately contested HumAID↔GPT-4o rows, ChatGPT chose:
- GPT-4o's label: **19/25 = 76%**
- HumAID's label: **4/25 = 16%**
- neither: **2/25 = 8%**

On the 25 rows where HumAID and GPT-4o already agreed, ChatGPT matched that consensus on **21/25 = 84%**.

Allowing ChatGPT's optional secondary label as a plausible alternative increased overlap to:
- HumAID primary-or-secondary match: **35/50 = 70%**
- GPT-4o primary-or-secondary match: **45/50 = 90%**

## Ambiguity signal

ChatGPT marked 18/50 rows ambiguous.

| ChatGPT ambiguity flag | n | vs HumAID | vs GPT-4o | HumAID↔GPT-4o |
|---|---:|---:|---:|---:|
| no | 32 | 68.75% | 90.63% | 62.50% |
| yes | 18 | 16.67% | 61.11% | 27.78% |

This is useful evidence that the ambiguity flag is identifying genuinely contested items.

## Codebook lessons from consensus misses

Four rows were missed even though HumAID and GPT-4o agreed. They motivate explicit tie-break rules:

1. Active warning/threat status can be `caution_and_advice` even without an imperative.
2. Concrete damage/access disruption should beat generic `other_relevant_information`; road shutdowns belong under infrastructure unless behavioral guidance is the main intent.
3. Generic solidarity/help language without a concrete aid mechanism should not automatically be treated as rescue/donation.
4. `not_humanitarian` should be reserved for genuinely unrelated/metaphorical/entertainment use; claims about a real current disaster generally remain on-topic even when dubious.

The refined V2 codebook captures these rules.

## Methodological status

ChatGPT, Claude, Grok, Gemini, GPT-4o, and similar systems are **model annotators**, not independent human annotators. Their agreement is useful exploratory evidence and can help target adjudication, but it must not be described as new human ground truth. A paper claiming corrected ground truth should still obtain human adjudication for the final disputed subset or full audit.
