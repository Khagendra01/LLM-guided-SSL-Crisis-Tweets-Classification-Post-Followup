# Paper Experiment — Human Benchmark vs Original Labels

## Freeze
- 500/500 manually reviewed (P1 101/101, P2 78/78, P3 90/90, P4 231/231)
- Canonical: `researcher_adjudicated_canonical_500.csv` (hash d06926...)
- Export: `local_human_review/exports/20260831T053053Z` (manifest verified)
- All original labels and model outputs preserved separately (Humaid/gpt 5.6/claude/gemini/grok + researcher_first_pass)

## Benchmark Comparison (human as ground truth, 500)
- human vs HumAID: 37.8% exact, macroF1 0.391, kappa 0.303
- human vs gpt 5.6: 39.4%, 0.412, 0.322
- human vs researcher_first_pass: 35.0% (175 accepted / 325 changed)
- human vs claude 38.2%, gemini 40.6%, grok 40.2%
- Contested 250: human sided gpt 5.6 31.2%, HumAID 28.0%, neither 40.8% (researcher_first_pass sided gpt 5.6 54%)
- Per-class recall collapse on human `other_relevant` (0.65 recall but 0.17 precision vs HumAID) — human conservative
- `other_relevant` remains high across all priorities (P1 51.5%, P2 32.1%, P3 46.7%, P4 41.1%) — not P1-specific

## Retrain / Evaluate Plan

### A. Original labels
```bash
python -m lg_cotrain.run_experiment --events california_wildfires_2018 canada_wildfires_2016 ... --budgets 5 10 25 50
# data/original/* with HumAID labels
```

### B. Corrected human labels
Replace 500 audit labels with `human_benchmark_500.csv` as corrected train subset or as test set:
```bash
# Use human_benchmark_500.csv as gold test; training data remains original but evaluation switches
python research_repo_payload/research_audit/scripts/score_audit_v2.py --key audit_v2_500_hidden_key_LOCKED.csv --annotator human=human_benchmark_500.csv --outdir scoring_human
# For training: inject corrected labels into data/pseudo-labelled/human-corrected/
python -m lg_cotrain.run_experiment --pseudo-label-source human-corrected --events ...
```

### C. Human + pseudo-labelled
Combine corrected 500 with gpt 5.6 pseudo-labelled pool:
```bash
python -m lg_cotrain.run_experiment --pseudo-label-source gpt-4o --events ... # baseline
# vs human-corrected + pseudo
```

### Hypotheses (to be tested by A/B/C)
- H1: Sub-70 macro-F1 on original data may be partly due to potential label noise — to be tested; current 37.8-40.6% agreement on disagreement-enriched audit describes this sample only, not corpus-wide accuracy.
- H2: Training/evaluating on corrected human labels is hypothesized to improve macro-F1 on the human benchmark, especially `other_relevant` vs `rescue`/`infra`/`urgent-needs` confusion — awaiting A/B/C results.
- H3: Human + pseudo is hypothesized to further improve over human-only — awaiting A/B/C results.
- All are hypotheses until the leakage-safe 5-fold A/B/C retraining reports pooled out-of-fold metrics with bootstrap CIs.

### Reliability (optional)
Second human on stratified 100 (25 per priority) to compute Cohen's kappa vs your benchmark — not to replace ownership.

### Commands for reviewer
```bash
python research_repo_payload/research_audit/scripts/score_audit_v2.py --key .../audit_v2_500_hidden_key_LOCKED.csv --annotator human=final_freeze/human_benchmark_500.csv --annotator claude=... --outdir /tmp/score
cat /tmp/score/headline_metrics.csv
```
