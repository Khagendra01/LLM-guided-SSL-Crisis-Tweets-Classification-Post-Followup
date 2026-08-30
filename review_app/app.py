import csv
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template, send_from_directory

from review_app.storage import (
    LEGAL_LABELS, LEDGER_COLUMNS, SESSION_FIELDS, LOCAL_DIR, QUEUE_PATH, LEDGER_PATH,
    load_queue, load_session, init_session_if_needed, save_session, load_bookmarks, save_bookmarks,
    load_app_state, save_app_state, atomic_write_text, backup_file, append_journal, utc_now
)

app = Flask(__name__, static_folder="static", template_folder="templates")

QUEUE_ITEMS = load_queue()
QUEUE_BY_ID = {x["annotation_id"]: x for x in QUEUE_ITEMS}
ORDERED_IDS = [x["annotation_id"] for x in QUEUE_ITEMS]

init_session_if_needed(QUEUE_ITEMS)
if not (LOCAL_DIR / "review_journal.jsonl").exists():
    append_journal({"action":"startup"})
else:
    append_journal({"action":"startup"})

if not (LOCAL_DIR / "bookmarks.json").exists():
    save_bookmarks({})
if not (LOCAL_DIR / "app_state.json").exists():
    save_app_state({"current_annotation_id": ORDERED_IDS[0]})

def get_session():
    s = load_session()
    if s is None:
        init_session_if_needed(QUEUE_ITEMS)
        s = load_session()
    return s

def blind_item(q, sess_row):
    return {
        "annotation_id": q["annotation_id"],
        "review_priority": q["review_priority"],
        "event": q["event"],
        "tweet_id": q["tweet_id"],
        "tweet_text": q["tweet_text"],
        "human_review_status": sess_row.get("human_review_status","pending"),
        "initial_primary_label": sess_row.get("initial_primary_label",""),
        "initial_secondary_label": sess_row.get("initial_secondary_label",""),
        "initial_confidence": sess_row.get("initial_confidence",""),
        "initial_ambiguous": sess_row.get("initial_ambiguous",""),
        "initial_reason": sess_row.get("initial_reason",""),
        "initial_saved_at_utc": sess_row.get("initial_saved_at_utc",""),
        "evidence_revealed_at_utc": sess_row.get("evidence_revealed_at_utc",""),
        "final_primary_label": sess_row.get("final_primary_label",""),
        "final_secondary_label": sess_row.get("final_secondary_label",""),
        "final_confidence": sess_row.get("final_confidence",""),
        "final_ambiguous": sess_row.get("final_ambiguous",""),
        "review_action": sess_row.get("review_action",""),
        "review_notes": sess_row.get("review_notes",""),
        "reviewed_at_utc": sess_row.get("reviewed_at_utc",""),
        "has_initial": bool(sess_row.get("initial_saved_at_utc")),
        "has_evidence": bool(sess_row.get("evidence_revealed_at_utc")),
        "is_reviewed": sess_row.get("human_review_status")=="reviewed",
    }

def revealed_extra(q):
    return {
        "humaid_label": q.get("humaid_label",""),
        "gpt4o_label": q.get("gpt4o_label",""),
        "gpt4o_confidence": q.get("gpt4o_confidence",""),
        "researcher_first_pass": q.get("researcher_first_pass",""),
        "researcher_first_pass_secondary": q.get("researcher_first_pass_secondary",""),
        "researcher_first_pass_confidence": q.get("researcher_first_pass_confidence",""),
        "researcher_first_pass_ambiguous": q.get("researcher_first_pass_ambiguous",""),
        "researcher_first_pass_reason": q.get("researcher_first_pass_reason",""),
        "claude": q.get("claude",""),
        "claude_secondary": q.get("claude_secondary",""),
        "claude_confidence": q.get("claude_confidence",""),
        "claude_ambiguous": q.get("claude_ambiguous",""),
        "claude_reason": q.get("claude_reason",""),
        "gemini": q.get("gemini",""),
        "gemini_secondary": q.get("gemini_secondary",""),
        "gemini_confidence": q.get("gemini_confidence",""),
        "gemini_ambiguous": q.get("gemini_ambiguous",""),
        "gemini_reason": q.get("gemini_reason",""),
        "grok": q.get("grok",""),
        "grok_secondary": q.get("grok_secondary",""),
        "grok_confidence": q.get("grok_confidence",""),
        "grok_ambiguous": q.get("grok_ambiguous",""),
        "grok_reason": q.get("grok_reason",""),
        "model_consensus_type": q.get("model_consensus_type",""),
        "model_top_label": q.get("model_top_label",""),
        "model_top_count": q.get("model_top_count",""),
        "researcher_ambiguous": q.get("researcher_ambiguous",""),
        "gemini_ambiguous": q.get("gemini_ambiguous",""),
        "grok_ambiguous": q.get("grok_ambiguous",""),
        "bulk_ai_recommended_label": q.get("bulk_ai_recommended_label",""),
        "bulk_recommendation_basis": q.get("bulk_recommendation_basis",""),
        "bulk_notes": q.get("bulk_notes",""),
    }

def compute_review_action(final_label, first_pass):
    return "accepted" if final_label == first_pass else "changed"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/labels")
def labels():
    guide = [
        {"id":"caution_and_advice","def":"Warnings, threat-status alerts, instructions, safety guidance, tips or behavioral advice. An active official warning can qualify without an imperative.","ex":["Evacuate now and avoid Highway 12.","Seven states are currently inside the hurricane cone.","Boil water before drinking."]},
        {"id":"displaced_people_and_evacuations","def":"Evacuation, relocation, displacement or sheltering as movement or accommodation of affected people.","ex":["St. Lucie County will open shelters Sunday.","More than 2,000 residents were evacuated.","Families have been relocated to temporary housing."]},
        {"id":"infrastructure_and_utility_damage","def":"Explicit physical damage, outages or access disruption involving buildings, housing, roads, bridges, electricity, water or communications.","ex":["The bridge collapsed after the earthquake.","Power and cellular service remain unavailable.","Flooding has closed the main highway."]},
        {"id":"injured_or_dead_people","def":"Injuries, casualties, fatalities, death tolls or bodies.","ex":["Three people were killed and twenty were injured.","Officials raised the confirmed death toll to 45."]},
        {"id":"missing_or_found_people","def":"People explicitly described as missing, unaccounted for, found, located or reunited.","ex":["Two children remain missing.","The missing family was found safe."]},
        {"id":"requests_or_urgent_needs","def":"Direct survival or SOS needs of affected people, including rescue, food, water, medicine, shelter, supplies or immediate services.","ex":["We are trapped and need rescue now.","Families urgently need clean water and medicine.","Please send help to this flooded neighborhood."]},
        {"id":"rescue_volunteering_or_donation_effort","def":"Offering or organizing aid, rescue, volunteers, donations, fundraisers, supply collections or relief delivery; calls directed toward potential helpers or donors.","ex":["Donate to the Red Cross wildfire relief fund.","Volunteers are needed at the shelter.","Where can I send supplies to help affected families?"]},
        {"id":"sympathy_and_support","def":"Prayers, condolences, encouragement, solidarity or emotional support without concrete aid action or safety information.","ex":["Praying for everyone affected.","Stay strong, Puerto Rico.","Our condolences to the victims’ families."]},
        {"id":"other_relevant_information","def":"Real disaster-related information that does not fit a more specific impact, need, warning or action category.","ex":["The storm has strengthened to Category 4.","Scientists are examining activity along the earthquake fault.","The region received twelve inches of rain."]},
        {"id":"not_humanitarian","def":"Genuinely unrelated, metaphorical, entertainment, spam-like or contextless content that does not convey information about the real disaster or humanitarian situation.","ex":["My fantasy football season is a disaster.","An unrelated business-news roundup with incidental flood hashtags.","Entertainment content using a hurricane name without discussing the real event."]},
    ]
    ties = [
        "Specific categories beat other_relevant_information.",
        "Road, power and water closures are normally infrastructure; behavioral instructions are caution/advice.",
        "“Evacuate now” can be caution/advice; reports of people evacuating or using shelters are displaced/evacuations.",
        "Affected people asking for immediate help are urgent needs.",
        "Appeals to donors, volunteers or organized relief are rescue/volunteering/donation.",
        "Generic “help” language is not automatically a donation or volunteering effort.",
        "“Stranded” does not automatically mean displaced.",
        "Use infrastructure damage only when damage or disruption is explicit or clear.",
        "Real-event misinformation remains disaster-related unless it is genuinely unrelated or metaphorical.",
        "For mixed tweets, choose the dominant communicative intent, use a secondary label when appropriate and mark ambiguity when reasonable annotators could disagree.",
    ]
    return jsonify({"labels": guide, "ties": ties, "legal": LEGAL_LABELS})

@app.route("/api/progress")
def progress():
    sess = get_session()
    reviewed = sum(1 for v in sess.values() if v.get("human_review_status")=="reviewed")
    pending = len(sess)-reviewed
    accepted = sum(1 for v in sess.values() if v.get("review_action")=="accepted")
    changed = sum(1 for v in sess.values() if v.get("review_action")=="changed")
    bookmarks = load_bookmarks()
    return jsonify({
        "total": len(sess),
        "reviewed": reviewed,
        "pending": pending,
        "accepted": accepted,
        "changed": changed,
        "bookmarked": len(bookmarks),
        "events": sorted(set(x["event"] for x in QUEUE_ITEMS)),
        "priorities": sorted(set(x["review_priority"] for x in QUEUE_ITEMS)),
    })

@app.route("/api/queue")
def queue():
    sess = get_session()
    bookmarks = load_bookmarks()
    priority = request.args.get("priority","")
    event = request.args.get("event","")
    status = request.args.get("status","")
    consensus = request.args.get("consensus","")
    qfilter = request.args.get("q","")
    out = []
    for q in QUEUE_ITEMS:
        aid = q["annotation_id"]
        s = sess.get(aid, {})
        if priority and q["review_priority"] != priority:
            continue
        if event and q["event"] != event:
            continue
        if consensus and q.get("model_consensus_type") != consensus:
            continue
        st = s.get("human_review_status","pending")
        bm = aid in bookmarks
        if status == "reviewed" and st != "reviewed":
            continue
        if status == "pending" and st == "reviewed":
            continue
        if status == "bookmarked" and not bm:
            continue
        if qfilter and qfilter.lower() not in aid.lower():
            continue
        out.append({
            "annotation_id": aid,
            "review_priority": q["review_priority"],
            "event": q["event"],
            "model_consensus_type": q.get("model_consensus_type",""),
            "human_review_status": st,
            "bookmarked": bm,
            "has_initial": bool(s.get("initial_saved_at_utc")),
            "has_evidence": bool(s.get("evidence_revealed_at_utc")),
        })
    return jsonify(out)

@app.route("/api/item/<aid>")
def get_item(aid):
    if aid not in QUEUE_BY_ID:
        return jsonify({"error":"not found"}), 404
    q = QUEUE_BY_ID[aid]
    sess = get_session()
    s = sess.get(aid, {})
    is_reviewed = s.get("human_review_status")=="reviewed"
    has_initial = bool(s.get("initial_saved_at_utc"))
    has_evidence = bool(s.get("evidence_revealed_at_utc"))
    base = blind_item(q, s)
    bookmarks = load_bookmarks()
    base["bookmarked"] = aid in bookmarks
    # Stage logic: if reviewed, always reveal; if has_evidence, reveal; else blind
    if is_reviewed or has_evidence:
        base.update(revealed_extra(q))
        base["evidence_visible"] = True
    else:
        base["evidence_visible"] = False
    # include index
    idx = ORDERED_IDS.index(aid)
    base["index"] = idx
    base["total"] = len(ORDERED_IDS)
    # prev/next
    base["prev_id"] = ORDERED_IDS[idx-1] if idx>0 else None
    base["next_id"] = ORDERED_IDS[idx+1] if idx < len(ORDERED_IDS)-1 else None
    return jsonify(base)

@app.route("/api/item/<aid>/initial", methods=["POST"])
def save_initial(aid):
    if aid not in QUEUE_BY_ID:
        return jsonify({"error":"not found"}), 404
    sess = get_session()
    row = sess.get(aid)
    if not row:
        return jsonify({"error":"not found"}), 404
    if row.get("human_review_status")=="reviewed" and not request.json.get("force"):
        # allow overwrite only if edit mode? For initial, blocked if reviewed without force
        return jsonify({"error":"Already reviewed. Use edit mode."}), 400
    data = request.json or {}
    pl = (data.get("initial_primary_label") or data.get("primary") or "").strip()
    sl = (data.get("initial_secondary_label") or data.get("secondary") or "").strip()
    conf = str(data.get("initial_confidence") or data.get("confidence") or "").strip()
    amb = (data.get("initial_ambiguous") or data.get("ambiguous") or "").strip()
    reason = (data.get("initial_reason") or data.get("reason") or "").strip()
    if pl not in LEGAL_LABELS:
        return jsonify({"error":"Invalid primary"}), 400
    if sl and sl not in LEGAL_LABELS:
        return jsonify({"error":"Invalid secondary"}), 400
    if sl and sl == pl:
        return jsonify({"error":"Secondary cannot equal primary"}), 400
    if conf not in ("1","2","3"):
        return jsonify({"error":"Confidence must be 1,2,3"}), 400
    if amb not in ("yes","no"):
        return jsonify({"error":"Ambiguity must be yes/no"}), 400
    if len(reason) < 5:
        return jsonify({"error":"Reason required >=5 chars"}), 400
    prev = dict(row)
    row["initial_primary_label"] = pl
    row["initial_secondary_label"] = sl
    row["initial_confidence"] = conf
    row["initial_ambiguous"] = amb
    row["initial_reason"] = reason
    row["initial_saved_at_utc"] = utc_now()
    # reset evidence if re-saving initial? keep existing evidence timestamp if already revealed? Clear? Keep
    sess[aid] = row
    save_session(sess)
    append_journal({"action":"save_initial","annotation_id":aid,"prev":prev,"new":dict(row)})
    save_app_state({"current_annotation_id": aid})
    return jsonify({"ok": True, "row": row})

@app.route("/api/item/<aid>/reveal", methods=["POST"])
def reveal(aid):
    if aid not in QUEUE_BY_ID:
        return jsonify({"error":"not found"}), 404
    sess = get_session()
    row = sess.get(aid)
    if not row.get("initial_saved_at_utc"):
        return jsonify({"error":"Save initial decision before revealing evidence"}), 400
    if not row.get("evidence_revealed_at_utc"):
        prev = row.get("evidence_revealed_at_utc")
        row["evidence_revealed_at_utc"] = utc_now()
        sess[aid] = row
        save_session(sess)
        append_journal({"action":"reveal_evidence","annotation_id":aid,"prev":prev,"new":row["evidence_revealed_at_utc"]})
    q = QUEUE_BY_ID[aid]
    return jsonify({"ok": True, "evidence": revealed_extra(q), "row": row})

@app.route("/api/item/<aid>/finalize", methods=["POST"])
def finalize(aid):
    if aid not in QUEUE_BY_ID:
        return jsonify({"error":"not found"}), 404
    sess = get_session()
    row = sess.get(aid)
    data = request.json or {}
    # require evidence revealed or already reviewed
    if not row.get("evidence_revealed_at_utc") and row.get("human_review_status")!="reviewed":
        # check if has_initial and caller wants to finalize without reveal? Must reveal first per workflow, but allow if they have evidence?
        return jsonify({"error":"Reveal evidence before finalizing"}), 400
    pl = (data.get("final_primary_label") or data.get("primary") or row.get("initial_primary_label") or "").strip()
    sl = (data.get("final_secondary_label") or data.get("secondary") or "").strip()
    conf = str(data.get("final_confidence") or data.get("confidence") or "").strip()
    amb = (data.get("final_ambiguous") or data.get("ambiguous") or "").strip()
    notes = (data.get("review_notes") or data.get("reason") or data.get("final_reason") or "").strip()
    # if final fields empty, use initial
    if not pl:
        pl = row.get("initial_primary_label","")
    if not conf:
        conf = row.get("initial_confidence","")
    if not amb:
        amb = row.get("initial_ambiguous","")
    if not notes:
        notes = row.get("initial_reason","")
    if pl not in LEGAL_LABELS:
        return jsonify({"error":"Invalid final primary"}), 400
    if sl and sl not in LEGAL_LABELS:
        return jsonify({"error":"Invalid final secondary"}), 400
    if sl and sl == pl:
        return jsonify({"error":"Secondary cannot equal primary"}), 400
    if conf not in ("1","2","3"):
        return jsonify({"error":"Final confidence must be 1,2,3"}), 400
    if amb not in ("yes","no"):
        return jsonify({"error":"Final ambiguity must be yes/no"}), 400
    if len(notes) < 5:
        return jsonify({"error":"Final notes required >=5 chars"}), 400
    q = QUEUE_BY_ID[aid]
    first_pass = q.get("researcher_first_pass","")
    action = compute_review_action(pl, first_pass)
    prev = dict(row)
    row["final_primary_label"] = pl
    row["final_secondary_label"] = sl
    row["final_confidence"] = conf
    row["final_ambiguous"] = amb
    row["review_notes"] = notes
    row["review_action"] = action
    row["human_review_status"] = "reviewed"
    row["reviewed_at_utc"] = utc_now()
    sess[aid] = row
    save_session(sess)
    append_journal({"action":"finalize","annotation_id":aid,"prev":prev,"new":dict(row)})
    return jsonify({"ok": True, "row": row})

@app.route("/api/item/<aid>/edit", methods=["POST"])
def edit_start(aid):
    if aid not in QUEUE_BY_ID:
        return jsonify({"error":"not found"}), 404
    sess = get_session()
    row = sess.get(aid)
    if row.get("human_review_status")!="reviewed":
        return jsonify({"error":"Not reviewed"}), 400
    # revert to pending but keep initial?
    prev = dict(row)
    row["human_review_status"] = "pending"
    row["reviewed_at_utc"] = ""
    # keep evidence etc
    sess[aid] = row
    save_session(sess)
    append_journal({"action":"edit_mode","annotation_id":aid,"prev":prev,"new":dict(row)})
    return jsonify({"ok": True})

@app.route("/api/bookmark/<aid>", methods=["POST"])
def bookmark(aid):
    bm = load_bookmarks()
    data = request.json or {}
    val = data.get("bookmarked")
    if val is None:
        # toggle
        if aid in bm:
            del bm[aid]
        else:
            bm[aid] = utc_now()
    elif val:
        bm[aid] = utc_now()
    else:
        bm.pop(aid, None)
    save_bookmarks(bm)
    append_journal({"action":"bookmark","annotation_id":aid,"bookmarked": aid in bm})
    return jsonify({"ok": True, "bookmarked": aid in bm})

@app.route("/api/validation")
def validation():
    sess = get_session()
    issues = []
    for aid, row in sess.items():
        if row.get("human_review_status")=="reviewed":
            if row.get("final_primary_label") not in LEGAL_LABELS:
                issues.append({"annotation_id":aid,"issue":"invalid final_primary"})
            if row.get("final_secondary_label") and row["final_secondary_label"]==row["final_primary_label"]:
                issues.append({"annotation_id":aid,"issue":"secondary equals primary"})
            if row.get("review_notes","").strip()=="":
                issues.append({"annotation_id":aid,"issue":"missing notes"})
            if row.get("review_action") not in ("accepted","changed"):
                issues.append({"annotation_id":aid,"issue":"invalid review_action"})
        else:
            # pending rows should not be marked reviewed
            pass
    # check duplicates/missing
    if len(sess)!=500:
        issues.append({"issue":f"session has {len(sess)} rows expected 500"})
    return jsonify({"issues": issues, "total": len(sess)})

@app.route("/api/export", methods=["POST"])
def do_export():
    sess = get_session()
    # validate
    if len(sess)!=500:
        return jsonify({"error":"Session must have 500 rows"}), 400
    # preserve 5 reviewed rows check? They are in session already
    ledger_reviewed = {}
    with open(LEDGER_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["human_review_status"]=="reviewed":
                ledger_reviewed[r["annotation_id"]] = r
    for aid, lr in ledger_reviewed.items():
        sr = sess.get(aid)
        if not sr or sr.get("human_review_status")!="reviewed" or sr.get("final_primary_label")!=lr["final_primary_label"]:
            return jsonify({"error":f"Ledger preserved row {aid} mismatch"}), 400
    # check all finalized rows valid
    pending = [a for a,r in sess.items() if r.get("human_review_status")!="reviewed"]
    # Actually export should include pending? Spec says updated ledger must have 500 IDs, but pending rows still represent? For exports, pending rows will have empty final? The ledger format expects pending? Original ledger has pending rows with empty final. So exports should be similar.
    # But validation says all newly finalized rows contain valid labels and notes - we check only reviewed
    for aid, r in sess.items():
        if r.get("human_review_status")=="reviewed":
            if r.get("final_primary_label") not in LEGAL_LABELS:
                return jsonify({"error":f"Invalid label {aid}"}), 400
            if r.get("review_notes","").strip()=="":
                return jsonify({"error":f"Missing notes {aid}"}), 400
    # create exports
    exp_dir = LOCAL_DIR / "exports"
    exp_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sub = exp_dir / ts
    sub.mkdir(parents=True, exist_ok=True)
    # backup before export
    backup_file(LOCAL_DIR / "review_session.csv")
    # 1 final_human_labels.csv
    p1 = sub / "final_human_labels.csv"
    with open(p1, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["annotation_id","final_primary_label","human_review_status","review_action"])
        w.writeheader()
        for aid in ORDERED_IDS:
            r = sess[aid]
            w.writerow({"annotation_id":aid,"final_primary_label":r.get("final_primary_label",""),"human_review_status":r.get("human_review_status",""),"review_action":r.get("review_action","")})
    # 2 researcher_human_review_ledger_UPDATED.csv
    p2 = sub / "researcher_human_review_ledger_UPDATED.csv"
    with open(p2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        w.writeheader()
        for aid in sorted(sess.keys()):
            r = sess[aid]
            w.writerow({
                "annotation_id": aid,
                "annotation_owner": "Khagendra01",
                "annotation_method": "AI-assisted first pass under researcher direction",
                "human_reviewer": "Khagendra01",
                "human_review_status": r.get("human_review_status","pending"),
                "final_primary_label": r.get("final_primary_label",""),
                "review_action": r.get("review_action",""),
                "review_notes": r.get("review_notes",""),
            })
    # 3 researcher_review_queue_UPDATED.csv  (prioritized queue with updated status)
    p3 = sub / "researcher_review_queue_UPDATED.csv"
    with open(p3, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(csv.DictReader(open(QUEUE_PATH, encoding="utf-8")).fieldnames)
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for q in QUEUE_ITEMS:
            aid = q["annotation_id"]
            r = sess[aid]
            row = {k: q.get(k,"") for k in fieldnames}
            row["human_review_status"] = r.get("human_review_status","")
            row["final_primary_label"] = r.get("final_primary_label","")
            row["review_action"] = r.get("review_action","")
            row["review_notes"] = r.get("review_notes","")
            w.writerow(row)
    # 4 initial_blind_human_decisions.csv
    p4 = sub / "initial_blind_human_decisions.csv"
    with open(p4, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["annotation_id","initial_primary_label","initial_secondary_label","initial_confidence","initial_ambiguous","initial_reason","initial_saved_at_utc"])
        w.writeheader()
        for aid in ORDERED_IDS:
            r = sess[aid]
            w.writerow({k: r.get(k,"") for k in ["annotation_id","initial_primary_label","initial_secondary_label","initial_confidence","initial_ambiguous","initial_reason","initial_saved_at_utc"]})
    # 5 human_review_completion_summary.json
    reviewed = sum(1 for v in sess.values() if v.get("human_review_status")=="reviewed")
    accepted = sum(1 for v in sess.values() if v.get("review_action")=="accepted")
    changed = sum(1 for v in sess.values() if v.get("review_action")=="changed")
    summary = {
        "total": 500,
        "reviewed": reviewed,
        "pending": 500-reviewed,
        "accepted": accepted,
        "changed": changed,
        "export_timestamp_utc": utc_now(),
        "export_dir": str(sub),
    }
    p5 = sub / "human_review_completion_summary.json"
    atomic_write_text(p5, json.dumps(summary, indent=2))
    # 6 manifest sha256
    p6 = sub / "human_review_completion_manifest.sha256"
    lines = []
    for p in [p1,p2,p3,p4,p5]:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{h}  {p.name}")
    atomic_write_text(p6, "\n".join(lines)+"\n")
    append_journal({"action":"export","dir":str(sub),"summary":summary})
    return jsonify({"ok": True, "dir": str(sub), "summary": summary, "files": [str(x.name) for x in [p1,p2,p3,p4,p5,p6]]})

@app.route("/api/journal")
def journal():
    p = LOCAL_DIR / "review_journal.jsonl"
    if not p.exists():
        return jsonify([])
    lines = p.read_text(encoding="utf-8").strip().split("\n")[-50:]
    return jsonify([json.loads(l) for l in lines if l.strip()])

if __name__ == "__main__":
    print("Open http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
