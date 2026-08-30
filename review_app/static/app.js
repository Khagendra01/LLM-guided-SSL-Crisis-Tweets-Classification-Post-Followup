let currentId=null, currentData=null, legal=[], guide=[], selPrimary='', selSecondary='', selFinal='', selFinalSec='';
let iaTimer=null, faTimer=null, initTimer=null;
const el=id=>document.getElementById(id);
function msg(t, isErr){ const m=el('msg'); m.textContent=t; m.style.display='block'; m.style.background=isErr?'#991b1b':'#111827'; setTimeout(()=>m.style.display='none',2600); }
async function fetchJSON(u, opts){ const r=await fetch(u, opts); const j=await r.json().catch(()=>({})); if(!r.ok) throw new Error(j.error||'error'); return j; }
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }

async function init(){
 const lab=await fetchJSON('/api/labels'); legal=lab.legal; guide=lab.labels;
 el('labelGuide').innerHTML=guide.map(g=>`<div class="gitem"><b>${esc(g.id)}</b><div>${esc(g.def)}</div><div style="font-style:italic;color:#9ca3af">${g.ex.map(esc).join(' • ')}</div></div>`).join('');
 el('tieList').innerHTML=lab.ties.map(t=>`<li>${esc(t)}</li>`).join('');
 const prog=await fetchJSON('/api/progress');
 el('fEvent').innerHTML='<option value="">All events</option>'+prog.events.map(e=>`<option>${esc(e)}</option>`).join('');
 updateProgress(prog);
 loadQueue();
 const q=await fetchJSON('/api/queue');
 if(q.length) loadItem(q[0].annotation_id);
 document.addEventListener('keydown', onKey);
 el('prevBtn').onclick=()=>nav(-1);
 el('nextBtn').onclick=()=>nav(1);
 el('skipBtn').onclick=()=>nav(1);
 el('bookmarkBtn').onclick=toggleBookmark;
 el('jumpBtn').onclick=()=>{ const v=el('jumpId').value.trim().toUpperCase(); if(v) loadItem(v); };
 el('exportBtn').onclick=doExport;
 el('validateBtn').onclick=doValidate;
 ['fPriority','fEvent','fStatus','fConsensus'].forEach(id=>el(id).onchange=loadQueue);
 el('guideToggle').onclick=()=>el('guidePane').classList.toggle('open');
 el('guideClose').onclick=()=>el('guidePane').classList.remove('open');
}
async function updateProgress(p){
 if(!p) p=await fetchJSON('/api/progress');
 el('progFill').style.width=((p.reviewed/p.total*100).toFixed(1))+'%';
 el('progText').textContent=`${p.reviewed}/${p.total} reviewed • ${(p.reviewed/p.total*100).toFixed(1)}%`;
 el('counts').textContent=`Reviewed ${p.reviewed} · Pending ${p.pending}`;
 el('counts2').textContent=` · Accepted ${p.accepted} · Changed ${p.changed} · ★ ${p.bookmarked}`;
}
async function loadQueue(){
 const qs=new URLSearchParams({priority:el('fPriority').value,event:el('fEvent').value,status:el('fStatus').value,consensus:el('fConsensus').value,q:''});
 const list=await fetchJSON('/api/queue?'+qs.toString());
 el('queueCount').textContent=`(${list.length})`;
 el('queueList').innerHTML=list.map(r=>`
  <div class="queue-item ${r.annotation_id===currentId?'active':''}" data-id="${r.annotation_id}">
    <div class="q-top"><span>${esc(r.annotation_id)}</span><span>${r.bookmarked?'★':''} <span class="badge ${r.human_review_status}">${r.human_review_status}</span></span></div>
    <div class="q-bottom"><span class="badge">${esc(r.review_priority.replace('P1_','P1 ').replace('P2_','P2 ').replace('P3_','P3 ').replace('P4_','P4 ').slice(0,22))}</span><span>${esc(r.event)}</span><span>${esc(r.model_consensus_type)}</span></div>
  </div>`).join('');
 el('queueList').querySelectorAll('.queue-item').forEach(d=>d.onclick=()=>loadItem(d.dataset.id));
}
async function loadItem(id){
 currentId=id;
 const d=await fetchJSON('/api/item/'+id);
 currentData=d;
 selPrimary=d.initial_primary_label||''; selSecondary=d.initial_secondary_label||''; selFinal=d.final_primary_label||d.initial_primary_label||''; selFinalSec=d.final_secondary_label||'';
 renderCard(d);
 loadQueue();
 updateProgress();
 const pos=el('posLabel'); if(pos) pos.textContent=`${d.index+1} / ${d.total}`;
 const bm=el('bookmarkBtn'); if(bm) bm.textContent=(d.bookmarked?'★ Bookmarked':'☆ Bookmark');
}
function labelButtons(selected, secondary, prefix){
 return `<div class="label-grid">${guide.map(g=>{
  const isSel = selected===g.id;
  const isSec = secondary===g.id;
  const cls = isSel?'label-btn selected': isSec?'label-btn selected secondary': 'label-btn';
  return `<button class="${cls}" data-val="${g.id}" data-kind="${prefix}"><div class="name">${esc(g.id)}</div><div class="desc">${esc(g.def)}</div><div class="ex">${esc(g.ex[0])}</div></button>`;
 }).join('')}</div>`;
}
function segButtons(name, value){
 const v = value || (name==='ic' || name==='fc' ? '2' : '');
 return `<div class="seg" data-name="${name}">
  <button data-v="1" class="${v==='1'?'selected':''}">1 — tied / poor</button>
  <button data-v="2" class="${v==='2'?'selected':''}">2 — plausible alt</button>
  <button data-v="3" class="${v==='3'?'selected':''}">3 — clearly best</button>
 </div>`;
}
function toggleButtons(name, value){
 const v = value || 'no';
 return `<div class="toggle" data-name="${name}">
  <button data-v="yes" class="${v==='yes'?'selected':''}">yes — ambiguous</button>
  <button data-v="no" class="${v==='no'?'selected':''}">no — clear</button>
 </div>`;
}
function renderCard(d){
 let html=`<div class="meta-line">
  <span class="chip">${esc(d.annotation_id)}</span>
  <span class="chip">${esc(d.review_priority)}</span>
  <span class="chip">${esc(d.event)}</span>
  <span class="chip">${d.human_review_status}</span>
  ${d.bookmarked?'<span class="chip">★ bookmarked</span>':''}
 </div>
 <div class="tweet">${esc(d.tweet_text)}</div>`;
 if(d.is_reviewed){
   html+=`<div style="margin-top:10px;padding:10px;background:#dcfce7;border:1px solid #86efac;border-radius:10px;font-size:13px">Already reviewed — <button id="editBtn" class="btn small">Edit</button> <span id="finalStatus" style="margin-left:8px;color:#065f46"></span></div>`;
 }
 const autosaveHint = d.human_review_status==='reviewed' ? '' : '<span id="autoStatus" style="font-size:12px;color:#0e7c62;margin-left:8px">● autosave on</span>';
  html+=`<div class="section"><h3>Stage 1 — Your decision ${autosaveHint}</h3>
  <div style="font-size:12px;color:#6b7280;margin-bottom:8px">Click labels — everything autosaves. No button needed.</div>
  <label style="font-weight:700;font-size:12px">Primary label *</label>
  ${labelButtons(selPrimary,'', 'primary')}
  <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Secondary (optional)</label>
  ${labelButtons(selSecondary,'', 'secondary')}</div>
  <div style="margin-top:12px"><label style="font-weight:700;font-size:12px">Confidence *</label>${segButtons('ic', d.initial_confidence)}</div>
  <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Ambiguity *</label>${toggleButtons('ia', d.initial_ambiguous)}</div>
  <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Reason / notes (optional)</label><textarea id="ir" rows="3" placeholder="Optional notes...">${esc(d.initial_reason||'')}</textarea></div>
  <div id="initStatus" style="font-size:12px;color:#6b7280;margin-top:6px"></div>
  <div style="display:flex;gap:8px;margin-top:12px"><button id="cardPrev1" class="btn ghost">← Prev</button><button id="cardNext1" class="btn primary">Next →</button><span style="font-size:12px;color:#6b7280;align-self:center">autosaved instantly</span></div>
 </div>`;

 if(d.evidence_visible){
   html+=`<div class="evidence"><h3 style="margin:0 0 8px">Stage 2 — Evidence & final <span id="finalAutoStatus" style="font-size:12px;color:#0e7c62;font-weight:400">● autosave on</span></h3>
   <div style="font-size:12px;color:#6b7280;margin-bottom:8px">Revealed ${esc(d.evidence_revealed_at_utc||'')} — changing anything autosaves final.</div>
   <table class="ev-table">
    <tr><td>HumAID</td><td>${esc(d.humaid_label)}</td></tr>
    <tr><td>GPT-4o</td><td>${esc(d.gpt4o_label)} <span style="color:#6b7280">conf ${esc(d.gpt4o_confidence)}</span></td></tr>
    <tr><td>Researcher 1st pass</td><td>${esc(d.researcher_first_pass)} ${d.researcher_first_pass_secondary?'→ '+esc(d.researcher_first_pass_secondary):''} <span style="color:#6b7280">c${esc(d.researcher_first_pass_confidence)} ${esc(d.researcher_first_pass_ambiguous)}</span></td></tr>
    <tr><td>Claude</td><td>${esc(d.claude)} <span style="color:#6b7280">amb ${esc(d.claude_ambiguous)}</span></td></tr>
    <tr><td>Gemini</td><td>${esc(d.gemini)} <span style="color:#6b7280">amb ${esc(d.gemini_ambiguous)}</span></td></tr>
    <tr><td>Grok</td><td>${esc(d.grok)} <span style="color:#6b7280">amb ${esc(d.grok_ambiguous)}</span></td></tr>
    <tr><td>Consensus</td><td>${esc(d.model_consensus_type)} · top ${esc(d.model_top_label)} (${esc(d.model_top_count)})</td></tr>
    <tr><td>Bulk AI rec.</td><td>${esc(d.bulk_ai_recommended_label)} <span style="color:#6b7280">${esc(d.bulk_recommendation_basis)}</span></td></tr>
   </table>
   <div style="margin-top:12px"><label style="font-weight:700;font-size:12px">Final primary *</label>${labelButtons(selFinal,'', 'final')}</div>
   <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Final secondary</label>${labelButtons(selFinalSec,'', 'finalSec')}</div>
   <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Final confidence</label>${segButtons('fc', d.final_confidence||d.initial_confidence)}</div>
   <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Final ambiguity</label>${toggleButtons('fa', d.final_ambiguous||d.initial_ambiguous)}</div>
   <div style="margin-top:10px"><label style="font-weight:700;font-size:12px">Final notes (optional)</label><textarea id="fn" rows="3" placeholder="Optional...">${esc(d.review_notes||d.initial_reason||'')}</textarea></div>
   <div id="finalStatus2" style="font-size:12px;color:#6b7280;margin-top:6px"></div>
   <div style="display:flex;gap:8px;margin-top:12px"><button id="cardPrev2" class="btn ghost">← Prev</button><button id="cardNext2" class="btn primary">Next →</button></div>
   </div>`;
 } else if(d.has_initial){
   html+=`<div id="revealStatus" style="margin-top:12px;font-size:12px;color:#0e7c62">✓ Initial autosaved — revealing evidence...</div>`;
 }
  el('card').innerHTML=html;
 attachCardHandlers(d);
 document.querySelector('.card-pane')?.scrollTo({top:0, behavior:'instant'});
 if(d.has_initial && !d.evidence_visible){
   setTimeout(()=>reveal(true), 300);
 }
}
function attachCardHandlers(d){
 document.querySelectorAll('.label-btn').forEach(b=>{
   b.onclick=()=>{
     const v=b.dataset.val, kind=b.dataset.kind;
     if(kind==='primary'){ selPrimary=v; updateLabelSelection('primary', v); scheduleInitAutosave(); }
     else if(kind==='secondary'){ selSecondary = (selSecondary===v?'':v); updateLabelSelection('secondary', selSecondary); scheduleInitAutosave(); }
     else if(kind==='final'){ selFinal=v; updateLabelSelection('final', v); scheduleFinalAutosave(); }
     else if(kind==='finalSec'){ selFinalSec = (selFinalSec===v?'':v); updateLabelSelection('finalSec', selFinalSec); scheduleFinalAutosave(); }
   };
 });
 document.querySelectorAll('.seg').forEach(g=>{
   g.querySelectorAll('button').forEach(b=>b.onclick=()=>{
     g.querySelectorAll('button').forEach(x=>x.classList.remove('selected'));
     b.classList.add('selected'); g.dataset.value=b.dataset.v;
     if(g.dataset.name==='ic') scheduleInitAutosave();
     else scheduleFinalAutosave();
   });
 });
 document.querySelectorAll('.toggle').forEach(g=>{
   g.querySelectorAll('button').forEach(b=>b.onclick=()=>{
     g.querySelectorAll('button').forEach(x=>x.classList.remove('selected'));
     b.classList.add('selected'); g.dataset.value=b.dataset.v;
     if(g.dataset.name==='ia') scheduleInitAutosave();
     else scheduleFinalAutosave();
   });
 });
 const ir=el('ir'); if(ir) ir.addEventListener('input', ()=>scheduleInitAutosave(true));
 const fn=el('fn'); if(fn) fn.addEventListener('input', ()=>scheduleFinalAutosave(true));
 const cb1=el('cardNext1'); if(cb1) cb1.onclick=()=>nav(1);
 const cbp1=el('cardPrev1'); if(cbp1) cbp1.onclick=()=>nav(-1);
 const cb2=el('cardNext2'); if(cb2) cb2.onclick=()=>nav(1);
 const cbp2=el('cardPrev2'); if(cbp2) cbp2.onclick=()=>nav(-1);
 const eb=el('editBtn'); if(eb) eb.onclick=editMode;
 ['ir','fn'].forEach(id=>{ const e=el(id); if(e) e.addEventListener('keydown', ev=>{ if(ev.key==='Enter' && !ev.ctrlKey) ev.stopPropagation(); }); });
}
function updateLabelSelection(kind, val){
 document.querySelectorAll(`.label-btn[data-kind="${kind}"]`).forEach(b=>{
   b.classList.toggle('selected', b.dataset.val===val);
 });
}
function getSegVal(name){ const g=document.querySelector(`.seg[data-name="${name}"]`); if(!g) return ''; const s=g.querySelector('.selected'); if(s) return s.dataset.v; return g.dataset.value||''; }
function getToggleVal(name){ const g=document.querySelector(`.toggle[data-name="${name}"]`); if(!g) return ''; const s=g.querySelector('.selected'); if(s) return s.dataset.v; return g.dataset.value||''; }

function setStatus(id, txt, isErr){ const e=el(id); if(e){ e.textContent=txt; e.style.color=isErr?'#991b1b':'#0e7c62'; } }

function scheduleInitAutosave(debounced=false){
 clearTimeout(initTimer);
 const delay = debounced ? 150 : 15;
 initTimer=setTimeout(tryAutosaveInitial, delay);
}
function scheduleFinalAutosave(debounced=false){
 clearTimeout(faTimer);
 const delay = debounced ? 150 : 15;
 faTimer=setTimeout(tryAutosaveFinal, delay);
}
async function tryAutosaveInitial(){
 if(!currentId) return;
 const reason=(el('ir')?.value||'').trim();
 let conf=getSegVal('ic')||'2', amb=getToggleVal('ia')||'no';
 if(!selPrimary){
   setStatus('initStatus','○ pick a primary label','');
   return;
 }
 setStatus('initStatus','● saving...','');
 const payload={initial_primary_label:selPrimary,initial_secondary_label:selSecondary,initial_confidence:conf,initial_ambiguous:amb,initial_reason:reason};
 try{
   await fetchJSON('/api/item/'+currentId+'/initial',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
   setStatus('initStatus','✓ autosaved','');
   const wasVisible=currentData.evidence_visible;
   const fresh=await fetchJSON('/api/item/'+currentId);
   currentData=fresh;
   if(!wasVisible && fresh.has_initial){
     await reveal(true);
   } else {
     updateProgress();
     loadQueue();
   }
 } catch(e){ setStatus('initStatus', e.message, true); }
}
async function reveal(silent=false){
 try{ await fetchJSON('/api/item/'+currentId+'/reveal',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
   if(!silent) msg('Evidence revealed');
   const fresh=await fetchJSON('/api/item/'+currentId);
   currentData=fresh;
   if(!selFinal) selFinal=selPrimary;
   renderCard(fresh);
   updateProgress(); loadQueue();
   if(fresh.evidence_visible) scheduleFinalAutosave();
 } catch(e){ if(!silent) msg(e.message,true); setStatus('initStatus', e.message, true); }
}
async function tryAutosaveFinal(){
 if(!currentId || !currentData?.evidence_visible) return;
 const notes=(el('fn')?.value||'').trim();
 let fc=getSegVal('fc')||'2', fa=getToggleVal('fa')||'no';
 if(!selFinal){
   setStatus('finalStatus2','○ pick final primary','');
   return;
 }
 setStatus('finalStatus2','● saving final...','');
 const payload={final_primary_label:selFinal,final_secondary_label:selFinalSec,final_confidence:fc,final_ambiguous:fa,review_notes:notes};
 try{
   await fetchJSON('/api/item/'+currentId+'/finalize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
   setStatus('finalStatus2','✓ final autosaved (reviewed)','');
   const fresh=await fetchJSON('/api/item/'+currentId);
   currentData=fresh;
   updateProgress(); loadQueue();
 } catch(e){ setStatus('finalStatus2', e.message, true); }
}
async function editMode(){ await fetchJSON('/api/item/'+currentId+'/edit',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}); msg('Edit mode'); loadItem(currentId); }
async function toggleBookmark(){ await fetchJSON('/api/bookmark/'+currentId,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}); loadItem(currentId); updateProgress(); }
function nav(dir){ if(!currentData) return; const nid=dir<0?currentData.prev_id:currentData.next_id; if(nid) loadItem(nid); }
function onKey(e){
 if(e.target.tagName==='TEXTAREA' || e.target.tagName==='INPUT'){
   if(e.ctrlKey && e.key==='s'){ e.preventDefault(); tryAutosaveInitial(); }
   if(e.ctrlKey && e.key==='Enter'){ e.preventDefault(); tryAutosaveFinal(); }
   return;
 }
 if(e.key==='ArrowLeft') nav(-1);
 if(e.key==='ArrowRight') nav(1);
 if(e.key==='b') toggleBookmark();
 if(e.key==='s') nav(1);
}
async function doExport(){ try{ const r=await fetchJSON('/api/export',{method:'POST'}); msg('Exported to '+r.dir); } catch(e){ msg(e.message,true); } }
async function doValidate(){ const r=await fetchJSON('/api/validation'); if(r.issues.length) msg('Issues: '+JSON.stringify(r.issues).slice(0,300),true); else msg('All valid: '+r.total); }
init();
