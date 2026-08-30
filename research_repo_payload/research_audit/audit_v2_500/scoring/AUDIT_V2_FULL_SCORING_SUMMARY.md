# Audit V2 full scoring summary

All four annotation sets are now complete, aligned, and frozen:

- Researcher-owned AI-assisted first pass: **500/500**
- Claude independent model pass: **500/500**
- Gemini independent model pass: **500/500**
- Grok independent model pass: **500/500**

The locked hidden key was opened only after the external model outputs were frozen.

## Important sampling caveat

Audit V2 is deliberately **disagreement-enriched**: each of the 10 events contributes 25 rows where HumAID and GPT-4o agree and 25 where they disagree. Therefore the agreement percentages below are annotation-audit statistics, **not ordinary test-set classifier accuracy estimates**.

## Headline agreement

| Comparison | Exact agreement | Macro-F1 | Cohen's kappa |
|---|---:|---:|---:|
| HumAID ↔ GPT-4o | 50.0% | 0.498 | 0.441 |
| Researcher first pass ↔ HumAID | 51.8% | 0.523 | 0.461 |
| Researcher first pass ↔ GPT-4o | 64.6% | 0.643 | 0.605 |
| Claude ↔ HumAID | 48.4% | 0.486 | 0.423 |
| Claude ↔ GPT-4o | 61.8% | 0.621 | 0.573 |
| Gemini ↔ HumAID | 51.8% | 0.526 | 0.461 |
| Gemini ↔ GPT-4o | 62.4% | 0.638 | 0.580 |
| Grok ↔ HumAID | 53.0% | 0.516 | 0.474 |
| Grok ↔ GPT-4o | 63.6% | 0.634 | 0.593 |

Pairwise agreement between the researcher first pass and independent models is substantially higher:

- Researcher ↔ Claude: **75.0%**
- Researcher ↔ Gemini: **68.2%**
- Researcher ↔ Grok: **70.8%**
- Claude ↔ Gemini: **73.6%**
- Claude ↔ Grok: **75.8%**
- Gemini ↔ Grok: **69.4%**

## HumAID/GPT-4o disagreement stratum

The sample contains exactly 250 HumAID↔GPT-4o disagreements.

- Researcher first pass: GPT-4o 135 (54.0%), HumAID 71 (28.4%), neither 44 (17.6%)
- Claude: GPT-4o 130 (52.0%), HumAID 63 (25.2%), neither 57 (22.8%)
- Gemini: GPT-4o 123 (49.2%), HumAID 70 (28.0%), neither 57 (22.8%)
- Grok: GPT-4o 127 (50.8%), HumAID 74 (29.6%), neither 49 (19.6%)

All four passes independently favor the GPT-4o side more often than the original HumAID side on deliberately contested rows. This is an audit finding; it does not by itself prove GPT-4o is correct.

## Four-way audit consensus

Across researcher first pass + Claude + Gemini + Grok:

- 4 of 4 agree: **268/500**
- 3 of 4 agree: **142/500**
- 2-2 tie: **42/500**
- 2-1-1 split: **46/500**
- all four different: **2/500**

Thus **410/500** rows have a 3-of-4 or 4-of-4 audit/model consensus.

Among the 268 unanimous rows:

- 140 match both HumAID and GPT-4o
- 72 match GPT-4o while differing from HumAID
- 27 match HumAID while differing from GPT-4o
- 29 match neither

Therefore **101/268 unanimous rows** have a unanimous audit/model label different from HumAID. These are the highest-priority candidates for researcher human review.

## Human-review status

No main-audit row is automatically marked human-reviewed by this scoring step. All 500 researcher-review ledger rows remain pending.

The prioritized queue and full hidden key are intentionally committed on the public, unblinded handoff branch:

- `../unblinded_review/researcher_review_queue_prioritized_UNBLINDED.csv`
- `../unblinded_review/audit_v2_500_hidden_key_LOCKED.csv`
- `../unblinded_review/canonical_adjudication_queue_UNBLINDED.csv`

Do not use this branch for a future blind annotation experiment.

Recommended review order:

1. unanimous 4-of-4 audit/model consensus that disagrees with HumAID;
2. 3-of-4 consensus that disagrees with HumAID;
3. split/tied audit cases;
4. strong consensus matching HumAID.

After researcher review and adjudication, labels explicitly accepted or changed by the researcher can become the corrected Audit V2 label set used for downstream GPU experiments.
