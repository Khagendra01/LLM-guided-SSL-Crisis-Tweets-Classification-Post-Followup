// DOCUMENTED historical audit sampler (recovery reference only).
// IMPORTANT: Do not accept regenerated AUDIT0351-AUDIT0500 unless the same run
// exactly reproduces the surviving AUDIT0001-AUDIT0350 event/tweet_id mapping.

function h32(s) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

// For each source row:
// group = human === gpt ? "agree" : "disagree"
// band = conf < 0.70 ? "low" : conf < 0.90 ? "medium" : "high"
// rank = h32("full500-v1|" + event + "|" + tweet_id + "|" + tweet_text)

const globalHuman = new Map();
const globalPred = new Map();
const globalBand = new Map();

function pick(pool, k, local) {
  const cand = pool.slice().sort((a, b) => a.rank - b.rank), sel = [];
  while (sel.length < k && cand.length) {
    let bestI = 0, bestS = -1e9;
    for (let i = 0; i < cand.length; i++) {
      const r = cand[i];
      const score =
        9 / (1 + (globalHuman.get(r.human) || 0)) +
        7 / (1 + (globalPred.get(r.gpt) || 0)) +
        5 / (1 + (globalBand.get(r.band) || 0)) +
        5 / (1 + (local.get(r.human) || 0)) +
        ((r.band === "low") ? 1.5 : 0) +
        ((h32("j|" + r.event + "|" + r.tweet_id) % 1000) / 1e6);
      if (score > bestS) { bestS = score; bestI = i; }
    }
    const r = cand.splice(bestI, 1)[0];
    sel.push(r);
    globalHuman.set(r.human, (globalHuman.get(r.human) || 0) + 1);
    globalPred.set(r.gpt, (globalPred.get(r.gpt) || 0) + 1);
    globalBand.set(r.band, (globalBand.get(r.band) || 0) + 1);
    local.set(r.human, (local.get(r.human) || 0) + 1);
  }
  return sel;
}

// Per event: pick 25 disagree, then 25 agree, updating global counters.
// After all events:
// selected.sort((a,b) => h32("display500-v1|"+a.tweet_id)-h32("display500-v1|"+b.tweet_id));
// selected.forEach((r,i) => r.annotation_id = "AUDIT" + String(i+1).padStart(4,"0"));
