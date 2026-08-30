#!/usr/bin/env python3
"""Score HumAID Audit V2 annotations against the locked key.

Example:
  python research_repo_payload/research_audit/scripts/score_audit_v2.py \
    --key audit_v2_500_hidden_key_LOCKED.csv \
    --annotator claude=claude_annotations.csv \
    --annotator grok=grok_annotations.csv \
    --outdir audit_v2_scoring

Uses Python stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

LABELS = [
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
]

ANNOTATOR_COLUMNS = [
    "annotation_id",
    "primary_label",
    "secondary_label",
    "confidence",
    "ambiguous",
    "reason",
]

KEY_REQUIRED = [
    "annotation_id",
    "event",
    "tweet_id",
    "humaid_label",
    "gpt4o_label",
    "gpt4o_confidence",
    "agreement_group",
]


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def validate_key(rows):
    if not rows:
        raise ValueError("Hidden key is empty.")
    missing = [c for c in KEY_REQUIRED if c not in rows[0]]
    if missing:
        raise ValueError(f"Hidden key missing columns: {missing}")
    ids = [r["annotation_id"].strip() for r in rows]
    if len(ids) != 500:
        raise ValueError(f"Hidden key must have 500 rows; got {len(ids)}.")
    if len(set(ids)) != 500:
        raise ValueError("Hidden key has duplicate annotation_id values.")
    for r in rows:
        if r["humaid_label"] not in LABELS:
            raise ValueError(f"Invalid HumAID label at {r['annotation_id']}: {r['humaid_label']}")
        if r["gpt4o_label"] not in LABELS:
            raise ValueError(f"Invalid GPT-4o label at {r['annotation_id']}: {r['gpt4o_label']}")
    return ids


def validate_annotator(name, rows, expected_ids):
    errors = []
    if not rows:
        return [f"{name}: file is empty"]
    actual_columns = list(rows[0].keys())
    if actual_columns != ANNOTATOR_COLUMNS:
        errors.append(
            f"{name}: columns must be exactly {ANNOTATOR_COLUMNS}; got {actual_columns}"
        )
    ids = [r.get("annotation_id", "").strip() for r in rows]
    if len(rows) != 500:
        errors.append(f"{name}: expected 500 rows; got {len(rows)}")
    if len(set(ids)) != len(ids):
        dupes = [x for x, n in Counter(ids).items() if n > 1]
        errors.append(f"{name}: duplicate annotation_id values: {dupes[:10]}")
    missing_ids = sorted(set(expected_ids) - set(ids))
    extra_ids = sorted(set(ids) - set(expected_ids))
    if missing_ids:
        errors.append(f"{name}: missing IDs (first 10): {missing_ids[:10]}")
    if extra_ids:
        errors.append(f"{name}: unexpected IDs (first 10): {extra_ids[:10]}")

    for i, r in enumerate(rows, 2):
        aid = r.get("annotation_id", f"row-{i}")
        primary = r.get("primary_label", "").strip()
        secondary = r.get("secondary_label", "").strip()
        confidence = r.get("confidence", "").strip()
        ambiguous = r.get("ambiguous", "").strip().lower()
        reason = r.get("reason", "").strip()

        if primary not in LABELS:
            errors.append(f"{name}:{aid}: invalid primary_label={primary!r}")
        if secondary and secondary not in LABELS:
            errors.append(f"{name}:{aid}: invalid secondary_label={secondary!r}")
        if secondary and secondary == primary:
            errors.append(f"{name}:{aid}: secondary_label equals primary_label")
        if confidence not in {"1", "2", "3"}:
            errors.append(f"{name}:{aid}: confidence must be 1/2/3; got {confidence!r}")
        if ambiguous not in {"yes", "no"}:
            errors.append(f"{name}:{aid}: ambiguous must be yes/no; got {ambiguous!r}")
        if not reason:
            errors.append(f"{name}:{aid}: reason is blank")
        if len(errors) >= 100:
            errors.append(f"{name}: validation stopped after 100 errors")
            break
    return errors


def exact_accuracy(a, b):
    if len(a) != len(b):
        raise ValueError("Unequal sequence lengths")
    return sum(x == y for x, y in zip(a, b)) / len(a) if a else float("nan")


def per_class_stats(y_true, y_pred):
    rows = []
    for label in LABELS:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        support = sum(t == label for t in y_true)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append({
            "label": label,
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })
    return rows


def macro_f1(y_true, y_pred):
    return sum(r["f1"] for r in per_class_stats(y_true, y_pred)) / len(LABELS)


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan")
    po = exact_accuracy(a, b)
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in LABELS)
    if math.isclose(1.0 - pe, 0.0):
        return 1.0 if math.isclose(po, 1.0) else 0.0
    return (po - pe) / (1.0 - pe)


def comparison_metrics(name_a, labels_a, name_b, labels_b):
    return {
        "comparison": f"{name_a} vs {name_b}",
        "n": len(labels_a),
        "exact_agreement": exact_accuracy(labels_a, labels_b),
        "macro_f1_treating_second_as_reference": macro_f1(labels_b, labels_a),
        "cohen_kappa": cohen_kappa(labels_a, labels_b),
    }


def secondary_overlap(rows, reference):
    matches = 0
    for r, ref in zip(rows, reference):
        choices = {r["primary_label"].strip()}
        sec = r["secondary_label"].strip()
        if sec:
            choices.add(sec)
        matches += ref in choices
    return matches / len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True, type=Path)
    ap.add_argument(
        "--annotator",
        required=True,
        action="append",
        metavar="NAME=CSV",
        help="Repeat for each independent model annotator, e.g. claude=claude.csv",
    )
    ap.add_argument("--outdir", required=True, type=Path)
    args = ap.parse_args()

    key_rows = read_csv(args.key)
    expected_ids = validate_key(key_rows)
    key_by_id = {r["annotation_id"]: r for r in key_rows}

    annotators = {}
    validation_errors = []
    for spec in args.annotator:
        if "=" not in spec:
            raise SystemExit(f"--annotator must be NAME=CSV, got: {spec}")
        name, raw_path = spec.split("=", 1)
        name = name.strip()
        if not name:
            raise SystemExit("Annotator name cannot be blank")
        rows = read_csv(Path(raw_path))
        errors = validate_annotator(name, rows, expected_ids)
        validation_errors.extend(errors)
        annotators[name] = rows

    args.outdir.mkdir(parents=True, exist_ok=True)
    validation_path = args.outdir / "validation.json"
    validation_path.write_text(
        json.dumps(
            {
                "valid": not validation_errors,
                "errors": validation_errors,
                "annotators": list(annotators),
                "expected_rows": 500,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    if validation_errors:
        raise SystemExit(
            f"Validation failed with {len(validation_errors)} issue(s). "
            f"See {validation_path}"
        )

    # Reorder every annotator to locked-key order.
    ordered = {}
    for name, rows in annotators.items():
        by_id = {r["annotation_id"]: r for r in rows}
        ordered[name] = [by_id[aid] for aid in expected_ids]

    humaid = [r["humaid_label"] for r in key_rows]
    gpt = [r["gpt4o_label"] for r in key_rows]

    headline = [
        comparison_metrics("HumAID", humaid, "GPT-4o", gpt),
    ]
    for name, rows in ordered.items():
        pred = [r["primary_label"] for r in rows]
        headline.append(comparison_metrics(name, pred, "HumAID", humaid))
        headline.append(comparison_metrics(name, pred, "GPT-4o", gpt))
    names = list(ordered)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            la = [r["primary_label"] for r in ordered[a]]
            lb = [r["primary_label"] for r in ordered[b]]
            headline.append(comparison_metrics(a, la, b, lb))

    write_csv(
        args.outdir / "headline_metrics.csv",
        ["comparison", "n", "exact_agreement",
         "macro_f1_treating_second_as_reference", "cohen_kappa"],
        headline,
    )

    contested = [i for i, (h, g) in enumerate(zip(humaid, gpt)) if h != g]
    consensus = [i for i, (h, g) in enumerate(zip(humaid, gpt)) if h == g]
    siding_rows = []
    for name, rows in ordered.items():
        pred = [r["primary_label"] for r in rows]
        counts = Counter()
        for i in contested:
            if pred[i] == gpt[i]:
                counts["gpt4o"] += 1
            elif pred[i] == humaid[i]:
                counts["humaid"] += 1
            else:
                counts["neither"] += 1
        consensus_matches = sum(pred[i] == humaid[i] for i in consensus)
        siding_rows.append({
            "annotator": name,
            "contested_n": len(contested),
            "sided_gpt4o_n": counts["gpt4o"],
            "sided_gpt4o_rate": counts["gpt4o"] / len(contested),
            "sided_humaid_n": counts["humaid"],
            "sided_humaid_rate": counts["humaid"] / len(contested),
            "sided_neither_n": counts["neither"],
            "sided_neither_rate": counts["neither"] / len(contested),
            "consensus_n": len(consensus),
            "consensus_match_n": consensus_matches,
            "consensus_match_rate": consensus_matches / len(consensus),
            "humaid_primary_or_secondary_rate": secondary_overlap(rows, humaid),
            "gpt4o_primary_or_secondary_rate": secondary_overlap(rows, gpt),
        })
    write_csv(
        args.outdir / "contested_siding.csv",
        [
            "annotator","contested_n","sided_gpt4o_n","sided_gpt4o_rate",
            "sided_humaid_n","sided_humaid_rate","sided_neither_n","sided_neither_rate",
            "consensus_n","consensus_match_n","consensus_match_rate",
            "humaid_primary_or_secondary_rate","gpt4o_primary_or_secondary_rate",
        ],
        siding_rows,
    )

    per_class_rows = []
    for name, rows in ordered.items():
        pred = [r["primary_label"] for r in rows]
        for ref_name, ref in [("HumAID", humaid), ("GPT-4o", gpt)]:
            for r in per_class_stats(ref, pred):
                per_class_rows.append({
                    "annotator": name,
                    "reference": ref_name,
                    **r,
                })
    write_csv(
        args.outdir / "per_class_metrics.csv",
        ["annotator","reference","label","support","precision","recall","f1"],
        per_class_rows,
    )

    ambiguity_rows = []
    for name, rows in ordered.items():
        for flag in ["no", "yes"]:
            idx = [i for i, r in enumerate(rows) if r["ambiguous"].strip().lower() == flag]
            pred = [rows[i]["primary_label"] for i in idx]
            h = [humaid[i] for i in idx]
            g = [gpt[i] for i in idx]
            ambiguity_rows.append({
                "annotator": name,
                "ambiguous": flag,
                "n": len(idx),
                "agreement_with_humaid": exact_accuracy(pred, h) if idx else "",
                "agreement_with_gpt4o": exact_accuracy(pred, g) if idx else "",
                "humaid_gpt4o_agreement": exact_accuracy(h, g) if idx else "",
                "mean_confidence": (
                    sum(int(rows[i]["confidence"]) for i in idx) / len(idx)
                    if idx else ""
                ),
            })
    write_csv(
        args.outdir / "ambiguity_summary.csv",
        ["annotator","ambiguous","n","agreement_with_humaid",
         "agreement_with_gpt4o","humaid_gpt4o_agreement","mean_confidence"],
        ambiguity_rows,
    )

    # Row-level disagreement table for adjudication.
    adjudication = []
    for i, key in enumerate(key_rows):
        model_labels = {name: ordered[name][i]["primary_label"] for name in names}
        distinct_models = set(model_labels.values())
        all_labels = set(distinct_models) | {humaid[i], gpt[i]}
        if len(all_labels) == 1:
            continue
        row = {
            "annotation_id": key["annotation_id"],
            "event": key["event"],
            "tweet_id": key["tweet_id"],
            "tweet_text": key.get("tweet_text", ""),
            "humaid_label": humaid[i],
            "gpt4o_label": gpt[i],
            "gpt4o_confidence": key["gpt4o_confidence"],
            "humaid_gpt4o_agree": "yes" if humaid[i] == gpt[i] else "no",
        }
        for name in names:
            rr = ordered[name][i]
            row[f"{name}_primary"] = rr["primary_label"]
            row[f"{name}_secondary"] = rr["secondary_label"]
            row[f"{name}_confidence"] = rr["confidence"]
            row[f"{name}_ambiguous"] = rr["ambiguous"]
            row[f"{name}_reason"] = rr["reason"]
        adjudication.append(row)

    fields = [
        "annotation_id","event","tweet_id","tweet_text","humaid_label","gpt4o_label",
        "gpt4o_confidence","humaid_gpt4o_agree",
    ]
    for name in names:
        fields += [
            f"{name}_primary",f"{name}_secondary",f"{name}_confidence",
            f"{name}_ambiguous",f"{name}_reason",
        ]
    write_csv(args.outdir / "adjudication_queue.csv", fields, adjudication)

    summary = {
        "valid": True,
        "n": 500,
        "annotators": names,
        "humaid_gpt4o_contested_n": len(contested),
        "humaid_gpt4o_consensus_n": len(consensus),
        "adjudication_queue_n": len(adjudication),
        "outputs": [
            "headline_metrics.csv",
            "contested_siding.csv",
            "per_class_metrics.csv",
            "ambiguity_summary.csv",
            "adjudication_queue.csv",
            "validation.json",
        ],
    }
    (args.outdir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
