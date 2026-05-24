function isImageSlug(slug){
  return slug.includes('image-') || slug.includes('color-picker-from-image') || slug.includes('palette-generator') || slug.includes('text-to-image-placeholder-generator') || slug.includes('base64-to-image-vice-versa');
}

function renderImageUI(slug){
  const panel=document.getElementById('backendPanel'); if(!panel||!isImageSlug(slug)) return;
  const map = {
    'image-compressor-jpeg-png-size-reducer': `<form class="imgForm" data-endpoint="/api/v1/images/compress"><input type=file name=file accept="image/*" required class="w-full border rounded p-2"><input type=range name=quality min=10 max=95 value=70 class="w-full"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Compress</button></form>`,
    'image-format-converter-png-to-webp-jpg-to-png-webp-to-jpg-etc': `<form class="imgForm space-y-3" data-endpoint="/api/v1/images/convert-format">
      <div id="convDropzone" class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer bg-slate-50 dark:bg-slate-800">
        <p class="font-semibold">Drop image here or click to upload</p><p id="convFileName" class="text-xs text-slate-500 mt-1">No file selected</p>
        <input id="convFile" type=file name=file accept="image/*" required class="hidden">
      </div>
      <input type="hidden" name="input_format" id="inputFmt" value="AUTO">
      <select name=target_format class="w-full border rounded p-2 dark:bg-slate-800">
        <option>JPEG</option><option>PNG</option><option>WEBP</option><option>BMP</option><option>GIF</option><option>TIFF</option><option>TIF</option><option>ICO</option><option>AVIF</option>
      </select>
      <button class="px-3 py-2 rounded bg-indigo-600 text-white">Download Converted Image</button>
    </form>`,
    'image-resizer-width-height-editor': `<form class="imgForm" data-endpoint="/api/v1/images/resize"><input type=file name=file accept="image/*" required class="w-full border rounded p-2"><div class="grid grid-cols-2 gap-2"><input name=width type=number placeholder=Width required class="border rounded p-2"><input name=height type=number placeholder=Height required class="border rounded p-2"></div><button class="px-3 py-2 rounded bg-indigo-600 text-white">Resize</button></form>`,
    'image-cropper': `<form class="imgForm" data-endpoint="/api/v1/images/crop"><input type=file name=file accept="image/*" required class="w-full border rounded p-2"><div class="grid grid-cols-4 gap-2"><input name=x type=number placeholder=X class="border rounded p-2" required><input name=y type=number placeholder=Y class="border rounded p-2" required><input name=w type=number placeholder=W class="border rounded p-2" required><input name=h type=number placeholder=H class="border rounded p-2" required></div><button class="px-3 py-2 rounded bg-indigo-600 text-white">Crop</button></form><p class="text-xs">Interactive preview click-to-crop available below.</p><canvas id="cropCanvas" class="border rounded w-full"></canvas>`,
    'background-remover-using-free-api-integration': `<form class="imgForm" data-endpoint="/api/v1/images/background-remove"><input type=file name=file accept="image/*" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Remove Background</button></form>`,
    'image-blur-sharpen-tool': `<form class="imgForm" data-endpoint="/api/v1/images/blur-sharpen"><input type=file name=file accept="image/*" required class="w-full border rounded p-2"><select name=mode class="w-full border rounded p-2 dark:bg-slate-800"><option value=blur>Blur</option><option value=sharpen>Sharpen</option></select><input type=range name=intensity min=1 max=10 value=2 class="w-full"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Apply Filter</button></form>`,
    'base64-to-image-vice-versa': `<div class="space-y-2"><form class="imgForm" data-endpoint="/api/v1/images/to-base64"><input type=file name=file accept="image/*" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Image → Base64</button></form><form id="fromB64" class="space-y-2"><textarea name=payload class="w-full border rounded p-2 h-28" placeholder="Paste Base64 data"></textarea><button class="px-3 py-2 rounded bg-emerald-600 text-white">Base64 → Image</button></form></div>`,
    'text-to-image-placeholder-generator': `<form class="imgForm" data-endpoint="/api/v1/images/placeholder"><div class="grid grid-cols-2 gap-2"><input name=width type=number placeholder=Width class="border rounded p-2" required><input name=height type=number placeholder=Height class="border rounded p-2" required></div><input name=bg_hex value="#cccccc" class="border rounded p-2 w-full"><input name=text value="Placeholder" class="border rounded p-2 w-full"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Generate</button></form>`,
    'color-picker-from-image': `<input type=file id=colorFile accept="image/*" class="w-full border rounded p-2"><canvas id=colorCanvas class="border rounded w-full"></canvas><p id=colorInfo class="text-xs"></p>`,
    'palette-generator': `<input type=file id=paletteFile accept="image/*" class="w-full border rounded p-2"><canvas id=paletteCanvas class="hidden"></canvas><div id=paletteBox class="grid grid-cols-5 gap-2"></div>`,
  };
  panel.innerHTML = map[slug] || '<p>Select an image tool.</p>';
  bindImageHandlers(slug);
}

async function blobDownload(r, name){ const b=await r.blob(); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=name; a.click(); }

function bindImageHandlers(slug){
  document.querySelectorAll('.imgForm').forEach(f=>f.addEventListener('submit', async(e)=>{e.preventDefault(); const fd=new FormData(f); const r=await fetch(f.dataset.endpoint,{method:'POST',body:fd}); if(!r.ok){alert('Failed');return;} if(f.dataset.endpoint.includes('to-base64')){const j=await r.json(); document.getElementById('toolOutput').textContent=j.base64; return;} await blobDownload(r,'image-tool-output');}));
  document.getElementById('fromB64')?.addEventListener('submit', async(e)=>{e.preventDefault(); const fd=new FormData(e.target); const r=await fetch('/api/v1/images/from-base64',{method:'POST', body:fd}); if(r.ok) await blobDownload(r,'decoded.png');});
  setupColorPicker(); setupPalette(); setupCropCanvas(); setupConverterDropzone();
}
function setupColorPicker(){const f=document.getElementById('colorFile'); if(!f) return; const c=document.getElementById('colorCanvas'); const x=c.getContext('2d'); const info=document.getElementById('colorInfo'); f.onchange=()=>{const i=new Image(); i.onload=()=>{c.width=i.width;c.height=i.height;x.drawImage(i,0,0)}; i.src=URL.createObjectURL(f.files[0]);}; c.onclick=(e)=>{const r=c.getBoundingClientRect();const d=x.getImageData(e.clientX-r.left,e.clientY-r.top,1,1).data; const hex='#'+[d[0],d[1],d[2]].map(v=>v.toString(16).padStart(2,'0')).join(''); info.textContent=`HEX ${hex} | RGB(${d[0]},${d[1]},${d[2]})`;};}
function setupPalette(){const f=document.getElementById('paletteFile'); if(!f) return; f.onchange=()=>{const img=new Image(); img.onload=()=>{const c=document.getElementById('paletteCanvas'); const x=c.getContext('2d'); c.width=100;c.height=100; x.drawImage(img,0,0,100,100); const dt=x.getImageData(0,0,100,100).data; const freq={}; for(let i=0;i<dt.length;i+=16){const k=`${dt[i]},${dt[i+1]},${dt[i+2]}`;freq[k]=(freq[k]||0)+1;} const top=Object.entries(freq).sort((a,b)=>b[1]-a[1]).slice(0,10); document.getElementById('paletteBox').innerHTML=top.map(([rgb])=>`<div class='h-12 rounded' style='background:rgb(${rgb})'></div>`).join('');}; img.src=URL.createObjectURL(f.files[0]);};}
function setupCropCanvas(){const canvas=document.getElementById('cropCanvas'); if(!canvas) return; const fileInput=document.querySelector('.imgForm input[type=file]'); const fx=document.querySelector('input[name=x]'),fy=document.querySelector('input[name=y]'); fileInput.onchange=()=>{const img=new Image(); img.onload=()=>{canvas.width=img.width;canvas.height=img.height;canvas.getContext('2d').drawImage(img,0,0);}; img.src=URL.createObjectURL(fileInput.files[0]);}; canvas.onclick=(e)=>{const r=canvas.getBoundingClientRect(); fx.value=Math.floor(e.clientX-r.left); fy.value=Math.floor(e.clientY-r.top);};}

window.renderImageUI = renderImageUI;

function setupConverterDropzone(){const dz=document.getElementById('convDropzone');const f=document.getElementById('convFile');const n=document.getElementById('convFileName');const iFmt=document.getElementById('inputFmt'); if(!dz||!f) return; dz.onclick=()=>f.click(); ['dragenter','dragover'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.add('border-indigo-500');})); ['dragleave','drop'].forEach(ev=>dz.addEventListener(ev,e=>{e.preventDefault();dz.classList.remove('border-indigo-500');})); dz.addEventListener('drop',e=>{const file=e.dataTransfer.files?.[0]; if(file){f.files=e.dataTransfer.files; n.textContent=file.name; iFmt.value=(file.name.split('.').pop()||'AUTO').toUpperCase();}}); f.addEventListener('change',()=>{const file=f.files?.[0]; if(file){n.textContent=file.name; iFmt.value=(file.name.split('.').pop()||'AUTO').toUpperCase();}});}
