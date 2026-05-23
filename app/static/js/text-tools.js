function isTextSlug(slug){
  return slug.includes('case-converter')||slug.includes('word-character-counter')||slug.includes('remove-duplicate-lines')||slug.includes('text-reverser')||slug.includes('lorem-ipsum-placeholder-generator')||slug.includes('find-and-replace-text')||slug.includes('url-encoder-decoder')||slug.includes('html-entity-encoder-decoder')||slug.includes('markdown-to-html-converter')||slug.includes('text-diff-checker')||slug.includes('slug-generator')||slug.includes('binary-to-text-vice-versa');
}

function renderTextUI(slug){
  const panel=document.getElementById('backendPanel'); if(!panel||!isTextSlug(slug)) return;
  panel.innerHTML=`<div class='grid md:grid-cols-2 gap-3'><textarea id='tIn' class='w-full min-h-48 border rounded p-3 dark:bg-slate-800' placeholder='Input'></textarea><textarea id='tOut' class='w-full min-h-48 border rounded p-3 dark:bg-slate-800' placeholder='Output'></textarea></div><div id='textActions' class='flex flex-wrap gap-2 mt-2'></div><button id='copyOut' class='px-3 py-2 rounded bg-emerald-600 text-white mt-2'>Copy Output</button><div id='meta' class='text-xs mt-2 text-slate-500'></div>`;
  const a=document.getElementById('textActions');
  const add=(id,l)=>a.insertAdjacentHTML('beforeend',`<button data-act='${id}' class='px-3 py-2 rounded bg-indigo-600 text-white'>${l}</button>`);
  if(slug.includes('case-converter'))['UPPER','lower','Title','Sentence','Capitalised'].forEach(x=>add('case-'+x.toLowerCase(),x));
  if(slug.includes('word-character-counter')) add('counter','Count');
  if(slug.includes('remove-duplicate-lines')) add('dedupe','Remove Duplicates');
  if(slug.includes('text-reverser')) {add('reverse-chars','Reverse Chars'); add('reverse-words','Reverse Words');}
  if(slug.includes('lorem-ipsum-placeholder-generator')) {add('lorem-p','Generate Paragraphs'); add('lorem-s','Generate Sentences'); add('lorem-w','Generate Words');}
  if(slug.includes('find-and-replace-text')) {a.insertAdjacentHTML('beforeend',`<input id='findTxt' placeholder='Find' class='border rounded p-2'><input id='repTxt' placeholder='Replace' class='border rounded p-2'>`); add('findreplace','Apply');}
  if(slug.includes('url-encoder-decoder')) {add('url-enc','Encode'); add('url-dec','Decode');}
  if(slug.includes('html-entity-encoder-decoder')) {add('html-enc','Encode'); add('html-dec','Decode');}
  if(slug.includes('markdown-to-html-converter')) add('md-html','Convert');
  if(slug.includes('text-diff-checker')) {document.getElementById('tOut').placeholder='Second text for compare'; add('diff','Compare');}
  if(slug.includes('slug-generator')) add('slug','Generate Slug');
  if(slug.includes('binary-to-text-vice-versa')) {add('txt-bin','Text→Binary'); add('bin-txt','Binary→Text');}

  a.addEventListener('click',(e)=>{const b=e.target.closest('button[data-act]'); if(!b) return; runTextAction(b.dataset.act, slug);});
  document.getElementById('copyOut').onclick=()=>navigator.clipboard.writeText(document.getElementById('tOut').value||'');
}

function runTextAction(act,slug){const i=document.getElementById('tIn'),o=document.getElementById('tOut'),m=document.getElementById('meta');const t=i.value||'';
  if(act==='case-upper')o.value=t.toUpperCase(); if(act==='case-lower')o.value=t.toLowerCase(); if(act==='case-title')o.value=t.replace(/\w\S*/g,w=>w[0].toUpperCase()+w.slice(1).toLowerCase()); if(act==='case-sentence')o.value=t.toLowerCase().replace(/(^\s*\w|[.!?]\s*\w)/g,c=>c.toUpperCase()); if(act==='case-capitalised')o.value=t.replace(/\b\w/g,c=>c.toUpperCase());
  if(act==='counter'){const words=(t.trim().match(/\S+/g)||[]).length; const chars=t.length; const paras=t.split(/\n+/).filter(Boolean).length; const spaces=(t.match(/ /g)||[]).length; o.value=`Words: ${words}\nCharacters: ${chars}\nParagraphs: ${paras}\nSpaces: ${spaces}`;}
  if(act==='dedupe')o.value=[...new Set(t.split('\n'))].join('\n');
  if(act==='reverse-chars')o.value=[...t].reverse().join(''); if(act==='reverse-words')o.value=t.split(/\s+/).reverse().join(' ');
  if(act==='lorem-p')o.value=Array.from({length:3},()=>"Lorem ipsum dolor sit amet, consectetur adipiscing elit.").join('\n\n'); if(act==='lorem-s')o.value=Array.from({length:8},(_,n)=>`Lorem ipsum sentence ${n+1}.`).join(' '); if(act==='lorem-w')o.value=Array.from({length:40},()=>"lorem").join(' ');
  if(act==='findreplace'){const f=document.getElementById('findTxt').value; const r=document.getElementById('repTxt').value; o.value=t.split(f).join(r);}
  if(act==='url-enc')o.value=encodeURIComponent(t); if(act==='url-dec')o.value=decodeURIComponent(t);
  if(act==='html-enc'){const d=document.createElement('div'); d.textContent=t; o.value=d.innerHTML;} if(act==='html-dec'){const d=document.createElement('textarea'); d.innerHTML=t; o.value=d.value;}
  if(act==='md-html')o.value=t.replace(/^### (.*$)/gim,'<h3>$1</h3>').replace(/^## (.*$)/gim,'<h2>$1</h2>').replace(/^# (.*$)/gim,'<h1>$1</h1>').replace(/\*\*(.*?)\*\*/gim,'<b>$1</b>').replace(/\*(.*?)\*/gim,'<i>$1</i>').replace(/\n$/gim,'<br/>');
  if(act==='diff'){const b=o.value; const aw=t.split('\n'), bw=b.split('\n'); o.value=bw.map((line,idx)=> line===aw[idx]?`  ${line}`:`- ${aw[idx]||''}\n+ ${line}`).join('\n');}
  if(act==='slug')o.value=t.toLowerCase().trim().replace(/[^a-z0-9\s-]/g,'').replace(/\s+/g,'-').replace(/-+/g,'-');
  if(act==='txt-bin')o.value=[...t].map(c=>c.charCodeAt(0).toString(2).padStart(8,'0')).join(' '); if(act==='bin-txt')o.value=t.split(' ').map(b=>String.fromCharCode(parseInt(b,2))).join('');
  m.textContent=`Executed: ${act}`;
}

window.renderTextUI = renderTextUI;
