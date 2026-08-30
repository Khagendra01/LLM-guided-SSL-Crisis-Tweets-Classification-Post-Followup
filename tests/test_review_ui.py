import csv
import json
import hashlib
import tempfile
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from review_app.storage import (
    LEGAL_LABELS, LEDGER_COLUMNS, LOCAL_DIR, QUEUE_PATH,
    load_queue, load_session, save_session, atomic_write_text, backup_file
)
from review_app.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_csv_special_chars(tmp_path):
    sess_path = LOCAL_DIR / "review_session.csv"
    # ensure tweet with commas, quotes, emoji, HTML, newline round-trips
    special = 'He said, "hello" & <script>alert(1)</script> 😀\nnew line, comma'
    # write via atomic and read back
    from review_app.storage import SESSION_FIELDS
    import io
    row = {k:"" for k in SESSION_FIELDS}
    row.update({"annotation_id":"AUDITV2_9999","tweet_text":special,"tweet_id":"1","event":"test","review_priority":"P1","human_review_status":"pending"})
    sio = io.StringIO()
    w = csv.DictWriter(sio, fieldnames=SESSION_FIELDS)
    w.writeheader()
    w.writerow(row)
    content = sio.getvalue()
    p = tmp_path / "t.csv"
    p.write_text(content, encoding="utf-8")
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert rows[0]["tweet_text"] == special

def test_preserve_500_ids():
    sess = load_session()
    assert len(sess) == 500
    assert len(set(sess.keys())) == 500
    for i in range(1,501):
        aid = f"AUDITV2_{i:04d}"
        assert aid in sess

def test_preserve_five_reviewed():
    sess = load_session()
    reviewed = [k for k,v in sess.items() if v["human_review_status"]=="reviewed"]
    assert len(reviewed) == 5
    assert set(reviewed) == {"AUDITV2_0017","AUDITV2_0019","AUDITV2_0027","AUDITV2_0028","AUDITV2_0031"}
    # check exact ledger values
    import csv
    ledger = {}
    with open(ROOT/"research_repo_payload/research_audit/audit_v2_500/researcher_human_review_ledger.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["human_review_status"]=="reviewed":
                ledger[r["annotation_id"]] = r
    for aid in reviewed:
        assert sess[aid]["final_primary_label"] == ledger[aid]["final_primary_label"]
        assert sess[aid]["review_action"] == ledger[aid]["review_action"]

def test_initial_counts(client):
    prog = client.get("/api/progress").json
    assert prog["total"] == 500
    assert prog["reviewed"] == 5
    assert prog["pending"] == 495

def test_prevent_invalid_labels(client):
    r = client.post("/api/item/AUDITV2_0001/initial", json={"initial_primary_label":"bad_label","initial_secondary_label":"","initial_confidence":"3","initial_ambiguous":"no","initial_reason":"valid reason here"})
    assert r.status_code == 400
    r = client.post("/api/item/AUDITV2_0001/initial", json={"initial_primary_label":"caution_and_advice","initial_secondary_label":"caution_and_advice","initial_confidence":"3","initial_ambiguous":"no","initial_reason":"valid reason"})
    assert r.status_code == 400
    assert "Secondary cannot equal" in r.json["error"]

def test_confidence_validation(client):
    r = client.post("/api/item/AUDITV2_0001/initial", json={"initial_primary_label":"caution_and_advice","initial_secondary_label":"","initial_confidence":"5","initial_ambiguous":"no","initial_reason":"valid reason"})
    assert r.status_code == 400

def test_stage1_hides_model_labels(client):
    # pick a pending id
    sess = load_session()
    pending = [k for k,v in sess.items() if v["human_review_status"]=="pending"][0]
    data = client.get(f"/api/item/{pending}").json
    assert data["evidence_visible"] is False
    for field in ["humaid_label","gpt4o_label","claude","gemini","grok","bulk_ai_recommended_label"]:
        assert field not in data, f"{field} leaked in Stage1"

def test_evidence_only_after_initial(client):
    sess = load_session()
    aid = "AUDITV2_0002"
    # ensure pending and no initial
    orig = dict(sess[aid])
    # try reveal without initial
    r = client.post(f"/api/item/{aid}/reveal", json={})
    assert r.status_code == 400
    # now save initial properly
    r = client.post(f"/api/item/{aid}/initial", json={"initial_primary_label":"other_relevant_information","initial_secondary_label":"","initial_confidence":"2","initial_ambiguous":"yes","initial_reason":"Testing evidence gate"})
    assert r.status_code == 200
    r = client.post(f"/api/item/{aid}/reveal", json={})
    assert r.status_code == 200
    data = client.get(f"/api/item/{aid}").json
    assert data["evidence_visible"] is True
    assert "humaid_label" in data
    # cleanup
    sess = load_session()
    sess[aid] = orig
    save_session(sess)

def test_accepted_vs_changed(client):
    # find a row where researcher_first_pass known
    from review_app.app import QUEUE_BY_ID
    aid = "AUDITV2_0003"
    q = QUEUE_BY_ID[aid]
    first = q["researcher_first_pass"]
    sess = load_session()
    orig = dict(sess[aid])
    # set initial
    client.post(f"/api/item/{aid}/initial", json={"initial_primary_label":first,"initial_secondary_label":"","initial_confidence":"3","initial_ambiguous":"no","initial_reason":"initial reason"})
    client.post(f"/api/item/{aid}/reveal", json={})
    # finalize same as first -> accepted
    r = client.post(f"/api/item/{aid}/finalize", json={"final_primary_label":first,"final_secondary_label":"","final_confidence":"3","final_ambiguous":"no","review_notes":"final notes ok"})
    assert r.json["row"]["review_action"] == "accepted"
    # now test changed: revert to pending then finalize different
    sess = load_session()
    sess[aid]["human_review_status"]="pending"
    sess[aid]["reviewed_at_utc"]=""
    save_session(sess)
    other = "caution_and_advice" if first!="caution_and_advice" else "sympathy_and_support"
    r = client.post(f"/api/item/{aid}/finalize", json={"final_primary_label":other,"final_secondary_label":"","final_confidence":"3","final_ambiguous":"no","review_notes":"changed notes"})
    assert r.json["row"]["review_action"] == "changed"
    # cleanup
    sess = load_session()
    sess[aid] = orig
    save_session(sess)

def test_persistence_across_restart(client):
    aid = "AUDITV2_0004"
    sess = load_session()
    orig = dict(sess[aid])
    client.post(f"/api/item/{aid}/initial", json={"initial_primary_label":"sympathy_and_support","initial_secondary_label":"","initial_confidence":"3","initial_ambiguous":"no","initial_reason":"persist test reason"})
    # reload from disk
    sess2 = load_session()
    assert sess2[aid]["initial_primary_label"] == "sympathy_and_support"
    # cleanup
    sess2[aid]=orig
    save_session(sess2)

def test_atomic_and_backup(tmp_path):
    dest = tmp_path / "atomic.txt"
    atomic_write_text(dest, "hello")
    assert dest.read_text() == "hello"
    atomic_write_text(dest, "world")
    assert dest.read_text() == "world"
    # backup
    bdir = LOCAL_DIR / "backups"
    # backup_file uses LOCAL_DIR/backups but test file not there; create dummy in LOCAL_DIR
    dummy = LOCAL_DIR / "dummy_test.txt"
    dummy.write_text("x")
    backup_file(dummy)
    assert any(p.name.startswith("dummy_test.txt.") for p in (LOCAL_DIR/"backups").iterdir())
    dummy.unlink()

def test_exports_and_hashes(client):
    # exports should validate 500, preserve 5, hashes match
    r = client.post("/api/export", json={})
    # may succeed even with pending rows (pending rows have empty final but that's allowed per ledger spec)
    assert r.status_code == 200
    data = r.json
    sub = Path(data["dir"])
    assert (sub / "human_review_completion_manifest.sha256").exists()
    manifest = (sub / "human_review_completion_manifest.sha256").read_text()
    for line in manifest.strip().split("\n"):
        h, fname = line.split("  ")
        actual = hashlib.sha256((sub / fname).read_bytes()).hexdigest()
        assert h == actual
    summary = json.loads((sub / "human_review_completion_summary.json").read_text())
    assert summary["total"] == 500
    assert summary["reviewed"] == 5
    # check updated ledger column order
    with open(sub / "researcher_human_review_ledger_UPDATED.csv", encoding="utf-8") as f:
        header = next(csv.reader(f))
        assert header == LEDGER_COLUMNS
        rows = list(csv.DictReader(open(sub / "researcher_human_review_ledger_UPDATED.csv", encoding="utf-8")))
        assert len(rows) == 500
        assert len(set(r["annotation_id"] for r in rows)) == 500

def test_bookmark(client):
    aid = "AUDITV2_0005"
    client.post(f"/api/bookmark/{aid}", json={"bookmarked": True})
    prog = client.get("/api/progress").json
    assert prog["bookmarked"] >= 1
    client.post(f"/api/bookmark/{aid}", json={"bookmarked": False})
