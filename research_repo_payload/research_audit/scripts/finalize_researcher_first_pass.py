#!/usr/bin/env python3
"""Finalize the recovered researcher-owned AI-assisted Audit V2 first pass.

This is a provenance repair, not a relabeling pass. The staged chunks reproduce
the exact previously validated 500-row CSV. Finalization is refused unless the
reconstructed bytes match the original frozen SHA256.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "research_repo_payload" / "research_audit" / "audit_v2_500"
STAGE = AUDIT / ".first_pass_recovery"
OUT = AUDIT / "researcher_ai_assisted_first_pass_FROZEN.csv"
HASH_OUT = AUDIT / "RESEARCHER_FIRST_PASS_SHA256.txt"
REPORT_OUT = AUDIT / "researcher_first_pass_validation.json"

EXPECTED_SHA256 = "38390d45f7e79a274245318a49c289988231b109f8139bb5d8bc933f70512f7a"
EXPECTED_COLUMNS = [
    "annotation_id",
    "primary_label",
    "secondary_label",
    "confidence",
    "ambiguous",
    "reason",
]
LABELS = {
    "caution_and_advice",
    "displaced_people_and_evacuations",
    "infrastructure_and_utility_damage",
    "injured_or_dead_people",
    "missing_or_found_people",
    "not_humanitarian",
    "other_relevant_information",
    "requests_or_urgent_needs",
    "rescue_volunteering_or_donation_effort",
    "sympathy_and_support",
}
PARTS = [
    "part001_0001_0100.csv",
    "part002_0101_0200.csv",
    "part003_0201_0300.csv",
    "part004_0301_0400.csv",
    "part005_0401_0500.csv",
]


def fail(msg: str) -> None:
    raise SystemExit(f"FINALIZATION REFUSED: {msg}")


def main() -> None:
    missing = [name for name in PARTS if not (STAGE / name).exists()]
    if missing:
        fail(f"missing recovery chunks: {missing}")

    # Part 1 contains the header; parts 2-5 are headerless. They were staged
    # from the original csv.writer output, so concatenating bytes is deliberate.
    data = b"".join((STAGE / name).read_bytes() for name in PARTS)
    sha = hashlib.sha256(data).hexdigest()
    if sha != EXPECTED_SHA256:
        fail(f"SHA256 mismatch: got {sha}, expected {EXPECTED_SHA256}")

    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != EXPECTED_COLUMNS:
        fail(f"schema mismatch: {reader.fieldnames}")
    rows = list(reader)

    if len(rows) != 500:
        fail(f"expected 500 data rows, got {len(rows)}")

    expected_ids = [f"AUDITV2_{i:04d}" for i in range(1, 501)]
    ids = [r["annotation_id"] for r in rows]
    if ids != expected_ids:
        fail("annotation IDs are not exactly AUDITV2_0001 through AUDITV2_0500")
    if len(set(ids)) != 500:
        fail("duplicate annotation IDs detected")

    errors = []
    for r in rows:
        aid = r["annotation_id"]
        primary = r["primary_label"]
        secondary = r["secondary_label"]
        if primary not in LABELS:
            errors.append(f"{aid}: invalid primary={primary!r}")
        if secondary and secondary not in LABELS:
            errors.append(f"{aid}: invalid secondary={secondary!r}")
        if secondary and secondary == primary:
            errors.append(f"{aid}: secondary equals primary")
        if r["confidence"] not in {"1", "2", "3"}:
            errors.append(f"{aid}: invalid confidence={r['confidence']!r}")
        if r["ambiguous"] not in {"yes", "no"}:
            errors.append(f"{aid}: invalid ambiguous={r['ambiguous']!r}")
        if not r["reason"].strip():
            errors.append(f"{aid}: blank reason")
    if errors:
        fail("; ".join(errors[:20]))

    # Preserve bytes exactly, including line endings and quoting.
    OUT.write_bytes(data)
    HASH_OUT.write_text(EXPECTED_SHA256 + "\n", encoding="utf-8")

    report = {
        "status": "validated",
        "purpose": "provenance repair of the original frozen AI-assisted first pass; no relabeling performed",
        "annotation_owner": "Khagendra01",
        "annotation_method": "AI-assisted first pass under researcher direction",
        "human_reviewer": "Khagendra01",
        "human_review_status": "pending; tracked separately in researcher_human_review_ledger.csv",
        "rows": 500,
        "unique_annotation_ids": 500,
        "first_id": ids[0],
        "last_id": ids[-1],
        "columns": EXPECTED_COLUMNS,
        "sha256": sha,
        "expected_sha256": EXPECTED_SHA256,
        "sha256_match": True,
        "primary_label_counts": dict(sorted(Counter(r["primary_label"] for r in rows).items())),
        "confidence_counts": dict(sorted(Counter(r["confidence"] for r in rows).items())),
        "ambiguity_counts": dict(sorted(Counter(r["ambiguous"] for r in rows).items())),
        "secondary_nonblank": sum(bool(r["secondary_label"]) for r in rows),
        "validation_errors": [],
    }
    REPORT_OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
