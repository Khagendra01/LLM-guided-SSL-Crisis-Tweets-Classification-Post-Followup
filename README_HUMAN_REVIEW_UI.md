# Audit V2 Human Review UI

Secure local web app for adjudicating the remaining 495 Audit V2 tweets. Implements anti-anchoring two-stage workflow.

## Setup

```bash
python3 -m venv .venv-review
source .venv-review/bin/activate
pip install -r requirements-review-ui.txt
python -m review_app.app
```

Open http://127.0.0.1:5000 (binds 127.0.0.1 only, no 0.0.0.0, no external requests, no CDN).

## Data inputs

- `research_repo_payload/research_audit/audit_v2_500/unblinded_review/researcher_review_queue_prioritized_UNBLINDED.csv` (queue order)
- `research_repo_payload/research_audit/audit_v2_500/researcher_human_review_ledger.csv` (5 reviewed rows preserved)
- `research_repo_payload/research_audit/audit_v2_500/bulk_ai_adjudication/audit_v2_bulk_ai_adjudication_recommendations.csv`
- `research_repo_payload/research_audit/audit_v2_500/researcher_ai_assisted_first_pass_FROZEN.csv`
- `research_repo_payload/research_audit/audit_v2_500/unblinded_review/canonical_adjudication_queue_UNBLINDED.csv`

All are local; no network calls.

## Workflow

**Stage 1 (blind):** annotation ID, event, tweet text, label codebook, primary/secondary, confidence, ambiguity, reason. No model labels sent to browser.

**Stage 2 (after Save):** click Reveal evidence to see HumAID, GPT-4o (+confidence), researcher first pass, Claude/Gemini/Grok (+ambiguity), consensus type, bulk recommendation. Then Finalize.

`review_action` computed as `accepted` if final equals researcher first pass else `changed`. Only Finalize sets `human_review_status=reviewed`.

Initial decision preserved for anchoring analysis.

## UI features

Progress bar, reviewed/pending/accepted/changed counts, priority group, event, large tweet panel, label guide sidebar (10 labels + tie-breakers), prev/next/save/finalize/skip/bookmark, keyboard: `←`/`→` nav, `b` bookmark, `s` skip, `Ctrl+S` save, `Ctrl+Enter` finalize, filters (P1-P4, event, reviewed/pending/bookmarked, consensus), jump by annotation ID, Validate, Export. Enter in notes does not submit; confirmation before finalize.

## Persistence & safety

Working dir: `research_repo_payload/research_audit/audit_v2_500/local_human_review/`

- `review_session.csv` - session state (500 rows)
- `review_journal.jsonl` - append-only journal
- `bookmarks.json`
- `app_state.json`
- `backups/*.bak` - timestamped backups at startup & before export
- `exports/<timestamp>/` - final exports

Atomic writes (tmp+fsync+replace). Tweet text escaped via `textContent`, never `innerHTML`.

## Backup & recovery

Backups created automatically at init and before export. To restore: copy latest `backups/review_session.csv.*.bak` to `review_session.csv`. Journal replay possible via `review_journal.jsonl`.

## Exports

Export page → `POST /api/export` validates:

- exactly 500 IDs, no duplicates
- 5 original reviewed rows preserved exactly
- all reviewed rows have valid label & notes
- counts match CSVs
- SHA-256 hashes

Generates in `local_human_review/exports/<ts>/`:

1. `final_human_labels.csv`
2. `researcher_human_review_ledger_UPDATED.csv` (exact ledger column order)
3. `researcher_review_queue_UPDATED.csv`
4. `initial_blind_human_decisions.csv`
5. `human_review_completion_summary.json`
6. `human_review_completion_manifest.sha256`

Does not overwrite canonical ledger; manual copy required.

## Validation

```bash
python -m pytest tests/test_review_ui.py -v
```

Covers CSV edge cases, 500 IDs, 5 preserved, 5/495 initial, duplicate prevention, invalid labels, secondary!=primary, persistence, atomic writes, Stage1 hiding, evidence gate, accepted/changed, hashes.

## Provenance warning

> Audit V2 used an AI-assisted first-pass under researcher direction. Only 5 rows are human-reviewed at app start (495 pending). Bulk AI recommendations are not human review. Final claims require row-level ledger review.

## Launch

`python -m review_app.app` prints `Open http://127.0.0.1:5000`

Initial state: **5 reviewed, 495 pending**. Not complete until all 500 finalized.
