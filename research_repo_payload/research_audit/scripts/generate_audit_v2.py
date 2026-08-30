#!/usr/bin/env python3
"""Generate a clean, reproducible 500-item HumAID Audit V2.

Public outputs contain NO HumAID/GPT-4o labels and NO source tweet IDs.
The hidden key is written outside the repository for workflow-artifact upload.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research_repo_payload" / "research_audit" / "audit_v2_500"
PRIVATE = Path(os.environ.get("AUDIT_V2_PRIVATE_DIR", "/tmp/audit_v2_private"))
SEED = "audit-v2-500-2026-08-30-v1"
ALGORITHM_VERSION = "audit-v2-stratified-balanced-v1"

EVENTS = [
    "california_wildfires_2018",
    "canada_wildfires_2016",
    "cyclone_idai_2019",
    "hurricane_dorian_2019",
    "hurricane_florence_2018",
    "hurricane_harvey_2017",
    "hurricane_irma_2017",
    "hurricane_maria_2017",
    "kaikoura_earthquake_2016",
    "kerala_floods_2018",
]

PILOT_V2_TWEET_IDS = {
    "798277386928328704","1167867834401058816","797919730141044736","729675384740925440",
    "913431937917779968","910683192159621120","1032517703221878784","1168329160688721920",
    "729724398022725633","798331492699029504","902598532036788225","1064568896592633856",
    "903426311833694209","1107578702945308672","909225008353832960","914532210493067265",
    "1039540313390505984","1040550470266306560","1167970289684082691","1030874753588854785",
    "1109347378702835712","908031153344524301","1032260132602662912","908229744591642624",
    "1031530274264248321","910610735981527040","1110843071346982912","1062923311565418496",
    "1037212045656158208","1041584037607956480","1168233306091151360","1061705177894477824",
    "913409616826028032","729798306688212992","903747398048120837","1168241657386610689",
    "728964931215753217","903709361482203136","1107637759198539776","1061841505780883456",
    "1108227041126727681","902650066086834176","734779332426633216","908313499042025473",
    "1041989898545373184","797790695352254465","1061496887931428865","1041839083054661632",
    "797916808426582017","905966109567971328",
}

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


def h32(s: str) -> int:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def band(conf: float) -> str:
    if conf < 0.70:
        return "low"
    if conf < 0.90:
        return "medium"
    return "high"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_old_pilot_ids() -> set[str]:
    p = ROOT / "research_repo_payload" / "research_audit" / "pilot_50" / "humaid_50_pilot_hidden_key.csv"
    ids: set[str] = set()
    with p.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tid = (r.get("tweet_id") or r.get("source_tweet_id") or "").strip()
            if tid:
                ids.add(tid)
    return ids


def load_candidates(excluded: set[str]):
    by_event = {}
    source_hashes = {}
    for event in EVENTS:
        path = ROOT / "data" / "pseudo-labelled" / "gpt-4o" / event / f"{event}_train_pred.csv"
        source_hashes[event] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        rows = []
        with path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("status") != "ok":
                    continue
                tid = str(r.get("tweet_id", "")).strip()
                text = r.get("tweet_text", "")
                if not tid or not text or tid in excluded:
                    continue
                human = r["class_label"]
                gpt = r["predicted_label"]
                conf = float(r["confidence"])
                rows.append({
                    "event": event,
                    "tweet_id": tid,
                    "tweet_text": text,
                    "human": human,
                    "gpt": gpt,
                    "confidence": conf,
                    "group": "agree" if human == gpt else "disagree",
                    "band": band(conf),
                    "rank": h32(f"{SEED}|{event}|{tid}|{text}"),
                    "source_path": source_hashes[event]["path"],
                })
        by_event[event] = rows
    return by_event, source_hashes


def pick(pool, k, global_human, global_gpt, global_band, local_human):
    cand = sorted(pool, key=lambda r: (r["rank"], r["tweet_id"]))
    selected = []
    while len(selected) < k:
        if not cand:
            raise RuntimeError(f"Pool exhausted at {len(selected)}/{k}")
        best_i = None
        best_score = None
        for i, r in enumerate(cand):
            score = (
                9 / (1 + global_human[r["human"]])
                + 7 / (1 + global_gpt[r["gpt"]])
                + 5 / (1 + global_band[r["band"]])
                + 5 / (1 + local_human[r["human"]])
                + (1.5 if r["band"] == "low" else 0)
                + (h32(f"{SEED}|jitter|{r['event']}|{r['tweet_id']}") % 1000) / 1_000_000
            )
            key = (score, -r["rank"], r["tweet_id"])
            if best_score is None or key > best_score:
                best_score = key
                best_i = i
        r = cand.pop(best_i)
        selected.append(r)
        global_human[r["human"]] += 1
        global_gpt[r["gpt"]] += 1
        global_band[r["band"]] += 1
        local_human[r["human"]] += 1
    return selected


def write_csv(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE.mkdir(parents=True, exist_ok=True)

    old_pilot = read_old_pilot_ids()
    excluded = set(old_pilot) | set(PILOT_V2_TWEET_IDS)
    by_event, source_hashes = load_candidates(excluded)

    gh, gg, gb = Counter(), Counter(), Counter()
    selected = []
    event_summary = []

    for event in EVENTS:
        local_h = Counter()
        rows = by_event[event]
        disagree_pool = [r for r in rows if r["group"] == "disagree"]
        agree_pool = [r for r in rows if r["group"] == "agree"]
        dsel = pick(disagree_pool, 25, gh, gg, gb, local_h)
        asel = pick(agree_pool, 25, gh, gg, gb, local_h)
        evsel = dsel + asel
        selected.extend(evsel)
        event_summary.append({
            "event": event,
            "n": 50,
            "agree": 25,
            "disagree": 25,
            "low_confidence": sum(r["band"] == "low" for r in evsel),
            "medium_confidence": sum(r["band"] == "medium" for r in evsel),
            "high_confidence": sum(r["band"] == "high" for r in evsel),
        })

    selected.sort(key=lambda r: (h32(f"{SEED}|display|{r['event']}|{r['tweet_id']}"), r["event"], r["tweet_id"]))
    if len(selected) != 500:
        raise AssertionError(len(selected))
    if len({r["tweet_id"] for r in selected}) != 500:
        raise AssertionError("duplicate tweet IDs")
    if any(r["tweet_id"] in excluded for r in selected):
        raise AssertionError("pilot overlap")

    for i, r in enumerate(selected, 1):
        r["annotation_id"] = f"AUDITV2_{i:04d}"

    blind_rows = [{
        "annotation_id": r["annotation_id"],
        "event": r["event"],
        "tweet_text": r["tweet_text"],
        "primary_label": "",
        "secondary_label": "",
        "confidence": "",
        "ambiguous": "",
        "reason": "",
    } for r in selected]

    template_rows = [{
        "annotation_id": r["annotation_id"],
        "primary_label": "",
        "secondary_label": "",
        "confidence": "",
        "ambiguous": "",
        "reason": "",
    } for r in selected]

    key_rows = [{
        "annotation_id": r["annotation_id"],
        "event": r["event"],
        "tweet_id": r["tweet_id"],
        "tweet_text": r["tweet_text"],
        "humaid_label": r["human"],
        "gpt4o_label": r["gpt"],
        "gpt4o_confidence": f"{r['confidence']:.6g}",
        "agreement_group": r["group"],
        "confidence_band": r["band"],
        "sampling_rank": r["rank"],
        "source_path": r["source_path"],
        "seed": SEED,
        "algorithm_version": ALGORITHM_VERSION,
    } for r in selected]

    blind_path = OUT / "audit_v2_500_blind.csv"
    write_csv(blind_path,
              ["annotation_id","event","tweet_text","primary_label","secondary_label","confidence","ambiguous","reason"],
              blind_rows)
    write_csv(OUT / "annotator_A_output_template.csv",
              ["annotation_id","primary_label","secondary_label","confidence","ambiguous","reason"],
              template_rows)
    write_csv(OUT / "annotator_B_output_template.csv",
              ["annotation_id","primary_label","secondary_label","confidence","ambiguous","reason"],
              template_rows)
    write_csv(OUT / "sampling_summary.csv",
              ["event","n","agree","disagree","low_confidence","medium_confidence","high_confidence"],
              event_summary)

    key_path = PRIVATE / "audit_v2_500_hidden_key_LOCKED.csv"
    write_csv(key_path,
              ["annotation_id","event","tweet_id","tweet_text","humaid_label","gpt4o_label","gpt4o_confidence",
               "agreement_group","confidence_band","sampling_rank","source_path","seed","algorithm_version"],
              key_rows)

    try:
        repo_commit = subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        repo_commit = "unknown"

    manifest = {
        "algorithm_version": ALGORITHM_VERSION,
        "seed": SEED,
        "source_repo_commit": repo_commit,
        "events": EVENTS,
        "sample_size": 500,
        "per_event": 50,
        "per_event_agree": 25,
        "per_event_disagree": 25,
        "excluded_old_pilot_tweet_ids": len(old_pilot),
        "excluded_pilot_v2_tweet_ids": len(PILOT_V2_TWEET_IDS),
        "selected_unique_tweet_ids": 500,
        "annotation_owner": "Khagendra01",
        "annotation_method": "AI-assisted first pass under researcher direction",
        "human_reviewer": "Khagendra01",
        "final_decision_authority": "Khagendra01",
        "human_review_status": "tracked row-by-row; pending until researcher acceptance/change is recorded",
        "human_review_ledger": "research_repo_payload/research_audit/audit_v2_500/researcher_human_review_ledger.csv",
        "provenance_document": "research_repo_payload/research_audit/ANNOTATION_PROVENANCE_V2.md",
        "source_files": source_hashes,
        "public_blind_sha256": sha256_file(blind_path),
        "hidden_key_sha256": sha256_file(key_path),
        "note": "Hidden key is intentionally not committed; workflow uploads it as a private artifact. Researcher human-review status is tracked separately and is never inferred from AI generation.",
    }
    (OUT / "reproduction_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT / "HIDDEN_KEY_SHA256.txt").write_text(manifest["hidden_key_sha256"] + "\n", encoding="utf-8")

    private_manifest = PRIVATE / "private_manifest.json"
    private_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "sample_size": 500,
        "blind": str(blind_path),
        "blind_sha256": manifest["public_blind_sha256"],
        "hidden_key": str(key_path),
        "hidden_key_sha256": manifest["hidden_key_sha256"],
        "global_humaid_counts": dict(gh),
        "global_gpt_counts": dict(gg),
        "global_confidence_bands": dict(gb),
    }, indent=2))


if __name__ == "__main__":
    main()
