import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
const colors=['#2563eb','#dc6b2f','#16836a','#6b7280'];
const time=s=>`${String(Math.floor(s/3600)).padStart(2,'0')}:${String(Math.floor(s/60)%60).padStart(2,'0')}`;
const twoFrames=fn=>requestAnimationFrame(()=>requestAnimationFrame(fn));
function Report({rows,hash,auto}){
  const [edits,setEdits]=useState({}),[category,setCategory]=useState('learning');
  const pending=useRef(null),button=useRef(null),initial=useRef(true);
  const effective=r=>edits[r.id]??r.category;
  const apps=[...new Set(rows.map(r=>r.app))].sort();
  const learning=rows.filter(r=>effective(r)==='learning').reduce((n,r)=>n+r.end-r.start,0);
  const unclassified=rows.filter(r=>effective(r)==='unclassified').reduce((n,r)=>n+r.end-r.start,0);
  const chosen=rows.find(r=>r.id===555), selectedText=`#555 | ${time(chosen.start)}–${time(chosen.end)} | ${chosen.app} | category=${effective(chosen)}`;
  const apply=()=>{pending.current=performance.now();setEdits(old=>({...old,555:category.trim()}));};
  useEffect(()=>{const handler=e=>{if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();button.current.click();}};window.addEventListener('keydown',handler);return()=>window.removeEventListener('keydown',handler);});
  useEffect(()=>{
    if(initial.current){initial.current=false;twoFrames(()=>{window.probe.ready({rows:rows.length,client_width:innerWidth,client_height:innerHeight});if(auto)setTimeout(()=>window.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',ctrlKey:true,bubbles:true})),500);});}
    if(pending.current!==null){const began=pending.current;pending.current=null;twoFrames(()=>window.probe.corrected({row_count:rows.length,selected_id:555,selected_category:edits[555],learning_seconds:learning,unclassified_seconds:unclassified,displayed_text:document.getElementById('selected-result').textContent,activation_mode:auto?'programmatic Ctrl+Enter key event routed within this window':'manual input',edit_to_two_frames_ms:performance.now()-began}));}
  },[edits]);
  return <main>
    <h1>Synthetic activity day</h1><div className="muted">1440 observations · 24h source time · foreground only · no personal data</div>
    <div className="summary">{apps.map(app=>`${app}: ${rows.filter(r=>r.app===app).reduce((n,r)=>n+r.end-r.start,0)/60} min`).join('    ')}</div>
    <h2>Timeline 09:00–10:00 · each block = one minute</h2>
    <svg className="timeline" aria-label="Activity timeline 09:00 to 10:00">
      {apps.map((app,i)=><text key={app} x="0" y={29+i*30} fontSize="12">{app}</text>)}
      {rows.filter(r=>r.start>=32400&&r.start<36000).map(r=><rect key={r.id} x={100+(r.start-32400)/60*14} y={12+apps.indexOf(r.app)*30} width="13" height="20" fill={effective(r)==='learning'?'#8b3fba':colors[apps.indexOf(r.app)%colors.length]} stroke={r.id===555?'black':'none'} strokeWidth={r.id===555?2:0}/>)}</svg>
    <h2>Detail 09:10–09:20 · selected observation #555</h2>
    <div className="details">{rows.filter(r=>r.id>=551&&r.id<=560).map(r=><div key={r.id} className={'row '+(r.id===555?'chosen':'')}>{`#${r.id}    ${time(r.start)}–${time(r.end)}    ${r.app.padEnd(12)}    ${effective(r)}`}</div>)}</div>
    <div className="result" id="selected-result" role="status">{selectedText}</div>
    <div className="controls"><label htmlFor="correction-category">Category</label><input id="correction-category" aria-label="Correction category" value={category} onChange={e=>setCategory(e.target.value)}/><button ref={button} id="apply-correction" onClick={apply}>Apply correction (Ctrl+Enter)</button></div>
    <div id="category-totals">learning_seconds={learning} · unclassified_seconds={unclassified}</div>
    <footer>App/title inference is excluded. Categories are interpretations; source intervals remain unchanged.</footer>
  </main>;
}
window.probe.fixture().then(data=>createRoot(document.getElementById('root')).render(<Report {...data}/>));
