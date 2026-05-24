const ALL_FORMATS = ['.doc','.docx','.pdf','.txt','.rtf','.odt','.html','.htm','.md','.csv','.xls','.xlsx','.xlsm','.ods','.ppt','.pptx','.odp','.pdfa','.epub','.mobi','.azw3','.fb2','.lit','.lrf','.wps','.wpd','.pages','.numbers','.key','.tex','.latex','.bib','.xml','.json','.yaml','.yml','.rst','.tsv','.log','.jpg','.jpeg','.png','.gif','.webp','.bmp','.tiff','.tif','.ico','.svg','.psd','.ai','.eps','.raw','.cr2','.nef','.arw','.dng','.heic','.heif','.avif','.tga','.dds','.hdr','.exr','.jp2','.j2k','.jxl','.wmf','.emf','.mp3','.wav','.aac','.flac','.ogg','.m4a','.wma','.amr','.opus','.ape','.aiff','.aif','.m4r','.mid','.midi','.mp4','.mkv','.avi','.mov','.wmv','.flv','.webm','.m4v','.mpeg','.mpg','.3gp','.3g2','.ts','.mts','.vob'];
const search = document.getElementById('formatSearchInput');
const select = document.getElementById('targetFormat');
const input = document.getElementById('fileInput');
const dz = document.getElementById('dropZone');
const statusEl = document.getElementById('status');
let selectedFile = null;

function renderOptions(q=''){ select.innerHTML = ALL_FORMATS.filter(f=>f.includes(q.toLowerCase())).map(f=>`<option value="${f}">${f}</option>`).join(''); }
search?.addEventListener('input', e=>renderOptions(e.target.value)); renderOptions();
dz?.addEventListener('click', ()=>input.click());
input?.addEventListener('change', ()=>{ selectedFile=input.files[0]; statusEl.textContent = selectedFile?`Selected: ${selectedFile.name}`:'No file'; });
['dragover','drop'].forEach(ev=>dz?.addEventListener(ev,e=>{e.preventDefault(); if(ev==='drop'){selectedFile=e.dataTransfer.files[0]; statusEl.textContent=`Selected: ${selectedFile.name}`;}}));

document.getElementById('convertBtn')?.addEventListener('click', async ()=>{
  if(!selectedFile){statusEl.textContent='Please choose a file';return;}
  statusEl.textContent='Converting...';
  const fd = new FormData(); fd.append('file', selectedFile); fd.append('target_ext', select.value);
  const r = await fetch('/api/v1/convert/convert',{method:'POST', body:fd});
  if(!r.ok){statusEl.textContent='Conversion failed';return;}
  const blob = await r.blob();
  const url = window.URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=`converted${select.value}`; document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url);
  statusEl.textContent='Done';
});
