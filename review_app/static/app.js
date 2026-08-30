let currentId=null, currentData=null, legal=[], guide=[];
const el=id=>document.getElementById(id);
function msg(t, isErr){ const m=el('msg'); m.textContent=t; m.style.display='block'; m.style.background=isErr?'#a33':'#333'; setTimeout(()=>m.style.display='none',2500); }

async function fetchJSON(u, opts){ const r=await fetch(u, opts); const j=await r.json(); if(!r.ok) throw new Error(j.error||'error'); return j; }

async function init(){
 const lab=await fetchJSON('/api/labels'); legal=lab.legal; guide=lab.labels;
 el('labelGuide').innerHTML=guide.map(g=>`<div class="def"><b>${g.id}</b>: ${esc(g.def)}<br><em>${g.ex.map(esc).join(' | ')}</em></div>`).join('');
 el('tieList').innerHTML=lab.ties.map(t=>`<li>${esc(t)}</li>`).join('');
 const prog=await fetchJSON('/api/progress');
 el('fEvent').innerHTML='<option value="">All events</option>'+prog.events.map(e=>`<option>${esc(e)}</option>`).join('');
 updateProgress(prog);
 loadQueue();
 // key
 const state=await fetchJSON('/api/queue');
 if(state.length){ loadItem(state[0].annotation_id); }
 document.addEventListener('keydown', onKey);
 el('prevBtn').onclick=()=>nav(-1);
 el('nextBtn').onclick=()=>nav(1);
 el('skipBtn').onclick=()=>nav(1);
 el('bookmarkBtn').onclick=toggleBookmark;
 el('jumpBtn').onclick=()=>{ const v=el('jumpId').value.trim().toUpperCase(); if(v) loadItem(v); };
 el('exportBtn').onclick=doExport;
 el('validateBtn').onclick=doValidate;
 el('fPriority').onchange=loadQueue;
 el('fEvent').onchange=loadQueue;
 el('fStatus').onchange=loadQueue;
 el('fConsensus').onchange=loadQueue;
}
function esc(s){ const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

async function updateProgress(p){
 if(!p){ p=await fetchJSON('/api/progress'); }
 el('progFill').style.width=((p.reviewed/p.total*100).toFixed(1))+'%';
 el('progText').textContent=`${p.reviewed}/${p.total} reviewed (${(p.reviewed/p.total*100).toFixed(1)}%)`;
 el('counts').textContent=`Reviewed:${p.reviewed} Pending:${p.pending}`;
 el('counts2').textContent=` Accepted:${p.accepted} Changed:${p.changed} Bookmarked:${p.bookmarked}`;
}

async function loadQueue(){
 const qs=new URLSearchParams({
  priority:el('fPriority').value,
  event:el('fEvent').value,
  status:el('fStatus').value,
  consensus:el('fConsensus').value,
  q:''
 });
 const list=await fetchJSON('/api/queue?'+qs.toString());
 el('queueList').innerHTML=list.map(r=>`<div data-id="${r.annotation_id}" class="${r.annotation_id===currentId?'active':''}">${esc(r.annotation_id)} ${esc(r.review_priority)} ${esc(r.event)} ${r.human_review_status} ${r.bookmarked?'★':''}</div>`).join('');
 el('queueList').querySelectorAll('div').forEach(d=>d.onclick=()=>loadItem(d.dataset.id));
}

async function loadItem(id){
 currentId=id;
 const d=await fetchJSON('/api/item/'+id);
 currentData=d;
 renderCard(d);
 loadQueue();
 updateProgress();
}

function renderCard(d){
 const opts=legal.map(l=>`<option value="${l}" ${d.initial_primary_label===l?'selected':''}>${l}</option>`).join('');
 const opts2='<option value="">(none)</option>'+legal.map(l=>`<option value="${l}" ${d.initial_secondary_label===l?'selected':''}>${l}</option>`).join('');
 const finalOpts=legal.map(l=>`<option value="${l}" ${d.final_primary_label===l?'selected':''}>${l}</option>`).join('');
 const finalOpts2='<option value="">(none)</option>'+legal.map(l=>`<option value="${l}" ${d.final_secondary_label===l?'selected':''}>${l}</option>`).join('');
 let html=`<div><small>${esc(d.annotation_id)} | ${esc(d.review_priority)} | ${esc(d.event)} | ${d.human_review_status} ${d.bookmarked?'★':''} | ${d.index+1}/${d.total}</small></div>
 <div class="tweet">${esc(d.tweet_text)}</div>`;
 if(d.is_reviewed){
   html+=`<p><em>Already reviewed — edit mode available</em> <button id="editBtn">Edit</button></p>`;
 }
 html+=`<div class="label-row"><label>Primary (required)</label><select id="ip">${opts}</select></div>
 <div class="label-row"><label>Secondary (optional)</label><select id="is">${opts2}</select></div>
 <div class="label-row"><label>Confidence: 3=clearly best, 2=plausible alternative, 1=nearly tied</label><select id="ic"><option value="">--</option><option value="3" ${d.initial_confidence=='3'?'selected':''}>3</option><option value="2" ${d.initial_confidence=='2'?'selected':''}>2</option><option value="1" ${d.initial_confidence=='1'?'selected':''}>1</option></select></div>
 <div class="label-row"><label>Ambiguity</label><select id="ia"><option value="">--</option><option value="yes" ${d.initial_ambiguous=='yes'?'selected':''}>yes</option><option value="no" ${d.initial_ambiguous=='no'?'selected':''}>no</option></select></div>
 <div class="label-row"><label>Reason / notes (required, ≥5 chars)</label><textarea id="ir" rows="3">${esc(d.initial_reason||'')}</textarea></div>
 <button id="saveInitial">Save initial (Ctrl+S)</button>`;

 if(d.evidence_visible){
   html+=`<div class="evidence"><h4>Evidence (revealed ${esc(d.evidence_revealed_at_utc||'')})</h4>
   <table>
   <tr><td>HumAID</td><td>${esc(d.humaid_label||'')}</td></tr>
   <tr><td>GPT-4o</td><td>${esc(d.gpt4o_label||'')} conf ${esc(d.gpt4o_confidence||'')}</td></tr>
   <tr><td>Researcher first pass</td><td>${esc(d.researcher_first_pass||'')} sec:${esc(d.researcher_first_pass_secondary||'')} conf:${esc(d.researcher_first_pass_confidence||'')} amb:${esc(d.researcher_first_pass_ambiguous||'')}</td></tr>
   <tr><td>Claude</td><td>${esc(d.claude||'')} amb:${esc(d.claude_ambiguous||'')} sec:${esc(d.claude_secondary||'')}</td></tr>
   <tr><td>Gemini</td><td>${esc(d.gemini||'')} amb:${esc(d.gemini_ambiguous||'')}</td></tr>
   <tr><td>Grok</td><td>${esc(d.grok||'')} amb:${esc(d.grok_ambiguous||'')}</td></tr>
   <tr><td>Consensus</td><td>${esc(d.model_consensus_type||'')} top:${esc(d.model_top_label||'')} count:${esc(d.model_top_count||'')}</td></tr>
   <tr><td>Bulk AI recommendation</td><td>${esc(d.bulk_ai_recommended_label||'')} basis:${esc(d.bulk_recommendation_basis||'')}</td></tr>
   </table>
   <div class="label-row"><label>Final primary</label><select id="fp">${finalOpts}</select></div>
   <div class="label-row"><label>Final secondary</label><select id="fs">${finalOpts2}</select></div>
   <div class="label-row"><label>Final confidence</label><select id="fc"><option value="">--</option><option value="3" ${d.final_confidence=='3'?'selected':''}>3</option><option value="2" ${d.final_confidence=='2'?'selected':''}>2</option><option value="1" ${d.final_confidence=='1'?'selected':''}>1</option></select></div>
   <div class="label-row"><label>Final ambiguity</label><select id="fa"><option value="">--</option><option value="yes" ${d.final_ambiguous=='yes'?'selected':''}>yes</option><option value="no" ${d.final_ambiguous=='no'?'selected':''}>no</option></select></div>
   <div class="label-row"><label>Final notes</label><textarea id="fn" rows="3">${esc(d.review_notes||d.initial_reason||'')}</textarea></div>
   <button id="finalBtn">Finalize (Ctrl+Enter)</button>
   </div>`;
 } else if(d.has_initial){
   html+=`<button id="revealBtn">Reveal evidence</button>`;
 }
 el('card').innerHTML=html;
 // handlers
 const si=el('saveInitial'); if(si) si.onclick=saveInitial;
 const rb=el('revealBtn'); if(rb) rb.onclick=reveal;
 const fb=el('finalBtn'); if(fb) fb.onclick=finalize;
 const eb=el('editBtn'); if(eb) eb.onclick=editMode;
 // prevent Enter in textarea submitting
 ['ir','fn'].forEach(id=>{ const e=el(id); if(e) e.addEventListener('keydown', ev=>{ if(ev.key==='Enter' && !ev.ctrlKey) ev.stopPropagation(); }); });
}

async function saveInitial(){
 const payload={
  initial_primary_label: el('ip').value,
  initial_secondary_label: el('is').value,
  initial_confidence: el('ic').value,
  initial_ambiguous: el('ia').value,
  initial_reason: el('ir').value
 };
 try{ await fetchJSON('/api/item/'+currentId+'/initial', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); msg('Initial saved'); loadItem(currentId); } catch(e){ msg(e.message,true); }
}
async function reveal(){
 try{ await fetchJSON('/api/item/'+currentId+'/reveal', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'}); msg('Evidence revealed'); loadItem(currentId); } catch(e){ msg(e.message,true); }
}
async function finalize(){
 if(!confirm('Finalize this row? This marks it human-reviewed.')) return;
 const payload={
  final_primary_label: el('fp').value,
  final_secondary_label: el('fs').value,
  final_confidence: el('fc').value,
  final_ambiguous: el('fa').value,
  review_notes: el('fn').value
 };
 try{ await fetchJSON('/api/item/'+currentId+'/finalize', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); msg('Finalized'); loadItem(currentId); } catch(e){ msg(e.message,true); }
}
async function editMode(){
 await fetchJSON('/api/item/'+currentId+'/edit', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'}); msg('Edit mode enabled'); loadItem(currentId);
}
async function toggleBookmark(){
 await fetchJSON('/api/bookmark/'+currentId, {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'}); loadItem(currentId); updateProgress();
}
function nav(dir){
 if(!currentData) return;
 const nid=dir<0?currentData.prev_id:currentData.next_id;
 if(nid) loadItem(nid);
}
function onKey(e){
 if(e.target.tagName==='TEXTAREA' || e.target.tagName==='INPUT' || e.target.tagName==='SELECT') {
   if(e.ctrlKey && e.key==='s'){ e.preventDefault(); saveInitial(); }
   if(e.ctrlKey && e.key==='Enter'){ e.preventDefault(); if(el('finalBtn')) finalize(); }
   return;
 }
 if(e.key==='ArrowLeft') nav(-1);
 if(e.key==='ArrowRight') nav(1);
 if(e.key==='b') toggleBookmark();
 if(e.key==='s') nav(1);
}
async function doExport(){
 try{ const r=await fetchJSON('/api/export', {method:'POST'}); msg('Exported to '+r.dir); } catch(e){ msg(e.message,true); }
}
async function doValidate(){
 const r=await fetchJSON('/api/validation'); if(r.issues.length) msg('Issues: '+JSON.stringify(r.issues).slice(0,300),true); else msg('All valid: '+r.total);
}
init();
