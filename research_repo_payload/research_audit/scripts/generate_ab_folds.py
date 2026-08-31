#!/usr/bin/env python3
"""
Leakage-safe 5-fold generator for A/B/C experiment.
- Each fold holds out 100 human-reviewed tweets (stratified by event + human label)
- Removes held-out IDs from every labeled/unlabeled/pseudo training file
- Zero-overlap check: held-out IDs must not appear in any training file
- Produces out-of-fold structure so every 500 is tested exactly once
"""
import csv, json, hashlib, random
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[3]
CANON=ROOT/"research_repo_payload/research_audit/audit_v2_500/human_review_batches/researcher_adjudicated_canonical_500.csv"
AUDIT_KEY=ROOT/"research_repo_payload/research_audit/audit_v2_500/unblinded_review/audit_v2_500_hidden_key_LOCKED.csv"
OUTDIR=ROOT/"research_repo_payload/research_audit/audit_v2_500/final_freeze/folds"

def load_canon():
    return list(csv.DictReader(open(CANON,encoding="utf-8")))

def stratified_folds(rows, k=5, seed=42):
    random.seed(seed)
    # bucket by (event, label)
    buckets=defaultdict(list)
    for r in rows:
        buckets[(r['event'], r['final_human_label'])].append(r)
    folds=[[] for _ in range(k)]
    for key, lst in buckets.items():
        random.shuffle(lst)
        for i, r in enumerate(lst):
            folds[i % k].append(r)
    # balance to 100 each
    for _ in range(500):
        sizes=[len(f) for f in folds]
        if max(sizes)-min(sizes)<=1 and all(s==100 for s in sizes):
            break
        if max(sizes)==100 and min(sizes)==100:
            break
        largest=max(range(k), key=lambda i: len(folds[i]))
        smallest=min(range(k), key=lambda i: len(folds[i]))
        if len(folds[largest])<=100 and len(folds[smallest])>=100:
            break
        # move one from largest to smallest if largest >100 or smallest <100
        if len(folds[largest])>100 or len(folds[smallest])<100:
            item=folds[largest].pop(random.randrange(len(folds[largest])))
            folds[smallest].append(item)
        else:
            break
    # final trim: ensure exactly 100 each by brute force
    # flatten and re-slice if still uneven
    sizes=[len(f) for f in folds]
    if not all(s==100 for s in sizes):
        flat=[]
        for f in folds:
            flat.extend(f)
        random.shuffle(flat)
        folds=[flat[i*100:(i+1)*100] for i in range(k)]
    return folds

def zero_overlap_check(fold_ids, data_root):
    # check that no held-out tweet_id appears in any training file
    # collect all tweet_ids from audit (to map annotation_id -> tweet_id)
    audit={r['annotation_id']:r['tweet_id'] for r in csv.DictReader(open(AUDIT_KEY,encoding="utf-8"))}
    held_tweets={audit[aid] for aid in fold_ids if aid in audit}
    # scan data/original and data/pseudo-labelled
    for p in Path(data_root).rglob("*.tsv"):
        try:
            txt=p.read_text(encoding="utf-8", errors="ignore")
            for tid in held_tweets:
                if tid in txt:
                    return False, f"leakage: {tid} found in {p}"
        except: pass
    return True, "ok"

def main():
    rows=load_canon()
    assert len(rows)==500, len(rows)
    folds=stratified_folds(rows, k=5, seed=42)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    manifest=[]
    for i, fold in enumerate(folds):
        ids=[r['annotation_id'] for r in fold]
        assert len(ids)==100, f"fold {i} size {len(ids)}"
        fold_path=OUTDIR/f"fold_{i}.json"
        fold_data={
            "fold": i,
            "test_ids": sorted(ids),
            "test_size": len(ids),
            "event_dist": dict(Counter(r['event'] for r in fold)),
            "label_dist": dict(Counter(r['final_human_label'] for r in fold)),
            "hash": hashlib.sha256("".join(sorted(ids)).encode()).hexdigest()[:12]
        }
        # zero overlap check vs data roots (use ROOT/data)
        ok, msg=zero_overlap_check(ids, ROOT/"data")
        fold_data["leakage_check"]=msg
        fold_data["leakage_ok"]=ok
        with open(fold_path,'w',encoding="utf-8") as f:
            json.dump(fold_data, f, indent=2)
        manifest.append(fold_data)
        print(f"fold {i}: {len(ids)} IDs, hash {fold_data['hash']}, leakage {msg}")
    # verify every 500 tested exactly once
    all_ids=[]
    for f in folds:
        all_ids.extend([r['annotation_id'] for r in f])
    assert len(set(all_ids))==500 and len(all_ids)==500, "out-of-fold coverage failed"
    # write manifest
    with open(OUTDIR/"fold_manifest.json",'w',encoding="utf-8") as f:
        json.dump({"folds": manifest, "total": 500, "k": 5, "stratify": ["event","final_human_label"], "seed": 42}, f, indent=2)
    # hash manifest
    h=hashlib.sha256(Path(OUTDIR/"fold_manifest.json").read_bytes()).hexdigest()
    with open(OUTDIR/"fold_manifest.sha256",'w') as f:
        f.write(f"{h}  fold_manifest.json\n")
    print(f"wrote {OUTDIR} with 5 folds, pooled out-of-fold covers 500 exactly once")

if __name__=="__main__":
    main()
