import csv
import json
import os
import hashlib
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

LEGAL_LABELS = [
    "caution_and_advice",
    "displaced_people_and_evacuations",
    "infrastructure_and_utility_damage",
    "injured_or_dead_people",
    "missing_or_found_people",
    "requests_or_urgent_needs",
    "rescue_volunteering_or_donation_effort",
    "sympathy_and_support",
    "other_relevant_information",
    "not_humanitarian",
]

LEDGER_COLUMNS = [
    "annotation_id","annotation_owner","annotation_method","human_reviewer","human_review_status","final_primary_label","review_action","review_notes"
]

SESSION_FIELDS = [
    "annotation_id","review_priority","event","tweet_id","tweet_text",
    "initial_primary_label","initial_secondary_label","initial_confidence","initial_ambiguous","initial_reason","initial_saved_at_utc",
    "evidence_revealed_at_utc",
    "final_primary_label","final_secondary_label","final_confidence","final_ambiguous","review_action","review_notes","reviewed_at_utc","human_review_status"
]

ROOT = Path(__file__).resolve().parent.parent
LOCAL_DIR = ROOT / "research_repo_payload/research_audit/audit_v2_500/local_human_review"
QUEUE_PATH = ROOT / "research_repo_payload/research_audit/audit_v2_500/unblinded_review/researcher_review_queue_prioritized_UNBLINDED.csv"
LEDGER_PATH = ROOT / "research_repo_payload/research_audit/audit_v2_500/researcher_human_review_ledger.csv"
BULK_PATH = ROOT / "research_repo_payload/research_audit/audit_v2_500/bulk_ai_adjudication/audit_v2_bulk_ai_adjudication_recommendations.csv"
CANONICAL_QUEUE = ROOT / "research_repo_payload/research_audit/audit_v2_500/unblinded_review/canonical_adjudication_queue_UNBLINDED.csv"
FROZEN_FIRST_PASS = ROOT / "research_repo_payload/research_audit/audit_v2_500/researcher_ai_assisted_first_pass_FROZEN.csv"

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def atomic_write_text(dest: Path, content: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent))
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dest)
    finally:
        try:
            os.unlink(tmp)
        except: pass

def atomic_write_json(dest: Path, obj):
    atomic_write_text(dest, json.dumps(obj, indent=2, ensure_ascii=False))

def append_journal(entry: dict):
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    p = LOCAL_DIR / "review_journal.jsonl"
    entry["timestamp_utc"] = utc_now()
    line = json.dumps(entry, ensure_ascii=False)
    with open(p, "a", encoding="utf-8") as f:
        f.write(line+"\n")
        f.flush()
        os.fsync(f.fileno())

def backup_file(src: Path):
    if not src.exists():
        return
    bdir = LOCAL_DIR / "backups"
    bdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst = bdir / f"{src.name}.{ts}.bak"
    shutil.copy2(src, dst)

def load_queue():
    items = []
    with open(QUEUE_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            items.append(row)
    bulk = {}
    if BULK_PATH.exists():
        with open(BULK_PATH, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                bulk[r["annotation_id"]] = r
    frozen = {}
    if FROZEN_FIRST_PASS.exists():
        with open(FROZEN_FIRST_PASS, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                frozen[r["annotation_id"]] = r
    canon = {}
    if CANONICAL_QUEUE.exists():
        with open(CANONICAL_QUEUE, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                canon[r["annotation_id"]] = r
    for it in items:
        aid = it["annotation_id"]
        b = bulk.get(aid, {})
        it["bulk_ai_recommended_label"] = b.get("bulk_ai_recommended_label","")
        it["bulk_recommendation_basis"] = b.get("bulk_recommendation_basis","")
        it["bulk_notes"] = b.get("bulk_notes","")
        ff = frozen.get(aid, {})
        it["researcher_first_pass_secondary"] = ff.get("secondary_label","")
        it["researcher_first_pass_confidence"] = ff.get("confidence","")
        it["researcher_first_pass_ambiguous"] = ff.get("ambiguous","")
        it["researcher_first_pass_reason"] = ff.get("reason","")
        c = canon.get(aid, {})
        it["claude_secondary"] = c.get("claude_secondary","")
        it["claude_confidence"] = c.get("claude_confidence","")
        it["claude_reason"] = c.get("claude_reason","")
        it["gemini_secondary"] = c.get("gemini_secondary","")
        it["gemini_confidence"] = c.get("gemini_confidence","")
        it["gemini_reason"] = c.get("gemini_reason","")
        it["grok_secondary"] = c.get("grok_secondary","")
        it["grok_confidence"] = c.get("grok_confidence","")
        it["grok_reason"] = c.get("grok_reason","")
    return items

def load_session():
    p = LOCAL_DIR / "review_session.csv"
    if not p.exists():
        return None
    rows = {}
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["annotation_id"]] = r
    return rows

def init_session_if_needed(queue_items):
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    (LOCAL_DIR / "backups").mkdir(parents=True, exist_ok=True)
    (LOCAL_DIR / "exports").mkdir(parents=True, exist_ok=True)
    p = LOCAL_DIR / "review_session.csv"
    if p.exists():
        return
    ledger_reviewed = {}
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["human_review_status"] == "reviewed":
                    ledger_reviewed[r["annotation_id"]] = r
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SESSION_FIELDS)
        w.writeheader()
        for q in queue_items:
            aid = q["annotation_id"]
            lr = ledger_reviewed.get(aid)
            if lr:
                row = {
                    "annotation_id": aid,
                    "review_priority": q["review_priority"],
                    "event": q["event"],
                    "tweet_id": q["tweet_id"],
                    "tweet_text": q["tweet_text"],
                    "initial_primary_label": "",
                    "initial_secondary_label": "",
                    "initial_confidence": "",
                    "initial_ambiguous": "",
                    "initial_reason": "",
                    "initial_saved_at_utc": "",
                    "evidence_revealed_at_utc": "",
                    "final_primary_label": lr["final_primary_label"],
                    "final_secondary_label": "",
                    "final_confidence": "3",
                    "final_ambiguous": "no",
                    "review_action": lr["review_action"],
                    "review_notes": lr["review_notes"],
                    "reviewed_at_utc": "2026-08-30T00:00:00Z",
                    "human_review_status": "reviewed",
                }
            else:
                row = {
                    "annotation_id": aid,
                    "review_priority": q["review_priority"],
                    "event": q["event"],
                    "tweet_id": q["tweet_id"],
                    "tweet_text": q["tweet_text"],
                    "initial_primary_label": "",
                    "initial_secondary_label": "",
                    "initial_confidence": "",
                    "initial_ambiguous": "",
                    "initial_reason": "",
                    "initial_saved_at_utc": "",
                    "evidence_revealed_at_utc": "",
                    "final_primary_label": "",
                    "final_secondary_label": "",
                    "final_confidence": "",
                    "final_ambiguous": "",
                    "review_action": "",
                    "review_notes": "",
                    "reviewed_at_utc": "",
                    "human_review_status": "pending",
                }
            w.writerow(row)
    backup_file(p)
    append_journal({"action":"init_session","rows":len(queue_items)})

def save_session(rows_dict):
    p = LOCAL_DIR / "review_session.csv"
    fieldnames = SESSION_FIELDS
    out = []
    for aid, row in rows_dict.items():
        out.append(row)
    # sort by queue order
    queue_order = {}
    with open(QUEUE_PATH, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f)):
            queue_order[r["annotation_id"]] = i
    out.sort(key=lambda x: queue_order.get(x["annotation_id"], 9999))
    import io
    sio = io.StringIO()
    w = csv.DictWriter(sio, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writeheader()
    for r in out:
        w.writerow({k: r.get(k,"") for k in fieldnames})
    content = sio.getvalue()
    atomic_write_text(p, content)

def load_bookmarks():
    p = LOCAL_DIR / "bookmarks.json"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_bookmarks(obj):
    atomic_write_json(LOCAL_DIR / "bookmarks.json", obj)

def load_app_state():
    p = LOCAL_DIR / "app_state.json"
    if not p.exists():
        return {"current_annotation_id": None}
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_app_state(obj):
    atomic_write_json(LOCAL_DIR / "app_state.json", obj)

def validate_review_fields(d, require_reason=False):
    pl = d.get("primary","") or d.get("initial_primary_label","") or d.get("final_primary_label","")
    sl = d.get("secondary","") or d.get("initial_secondary_label","") or d.get("final_secondary_label","")
    conf = str(d.get("confidence","") or d.get("initial_confidence","") or d.get("final_confidence",""))
    amb = d.get("ambiguous","") or d.get("initial_ambiguous","") or d.get("final_ambiguous","")
    if pl not in LEGAL_LABELS:
        return False, "Primary label must be one of 10 legal labels"
    if sl:
        if sl not in LEGAL_LABELS:
            return False, "Secondary label invalid"
        if sl == pl:
            return False, "Secondary cannot equal primary"
    if conf not in ("1","2","3"):
        return False, "Confidence must be 1, 2, or 3"
    if amb not in ("yes","no"):
        return False, "Ambiguity must be yes or no"
    return True, ""
