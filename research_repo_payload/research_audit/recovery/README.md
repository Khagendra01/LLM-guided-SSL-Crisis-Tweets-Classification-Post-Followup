# Audit source-mapping recovery checkpoint

This directory records the provenance-recovery work for the existing 500-item assistant/model audit.

## Current defensible state

- 500/500 assistant annotation decisions exist: `AUDIT0001`–`AUDIT0500`.
- 350/500 source mappings are verified and traceable.
- `AUDIT0351`–`AUDIT0500` remain unresolved for source provenance only.
- No regenerated mapping should be accepted unless the same reconstruction first reproduces all surviving `AUDIT0001`–`AUDIT0350` mappings exactly by annotation ID, event, and tweet ID.

## Files

- `RECOVERY_FORENSICS_2026-08-29.md` — repository/data-version investigation and findings.
- `AUDIT_351_500_RECOVERY_STATUS.md` — recovery acceptance test and historical/current blob fingerprints.
- `NEEDED_TO_UNLOCK_351_500.txt` — artifacts that would permit exact recovery.
- `reconstruct_audit_sampler_DOCUMENTED.js` — documented historical sampler, retained only as a recovery reference.
- `reviewer_update_with_recovery_forensics_2026-08-29.zip` — consolidated reviewer checkpoint package.

These assistant/model audit labels are exploratory researcher-supervised audit evidence, not independent new human ground truth.
