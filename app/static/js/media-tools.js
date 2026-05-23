function renderMediaUI(slug) {
  const panel = document.getElementById('backendPanel');
  if (!panel) return;

  const urlForm = `
    <form id="mediaUrlForm" class="space-y-3">
      <input name="url" required placeholder="Paste video URL" class="w-full rounded border p-2 dark:bg-slate-800" />
      <div class="flex gap-2">
        <button id="fetchBtn" class="px-3 py-2 rounded bg-indigo-600 text-white" type="submit">Fetch Metadata</button>
        <button id="downloadBtn" class="px-3 py-2 rounded bg-emerald-600 text-white" type="button">Download</button>
      </div>
      <select id="formatSelect" class="w-full rounded border p-2 dark:bg-slate-800"><option value="">Best</option></select>
    </form>
    <div id="mediaPreview" class="hidden rounded border p-3 bg-slate-50 dark:bg-slate-800">
      <img id="mediaThumb" class="w-40 h-24 object-cover rounded mb-2" alt="thumbnail" />
      <p id="mediaTitle" class="text-sm font-semibold"></p>
    </div>
    <div id="mediaResult" class="text-xs bg-slate-100 dark:bg-slate-800 rounded p-2 whitespace-pre-wrap"></div>`;

  const uploadForm = (endpoint, label, extra='') => `
    <form class="mediaUploadForm space-y-2" data-endpoint="${endpoint}">
      <input type="file" name="file" accept="video/mp4,video/*" required class="w-full rounded border p-2" />
      ${extra}
      <button class="px-3 py-2 rounded bg-indigo-600 text-white" type="submit">${label}</button>
    </form><p class="text-xs">Result downloads automatically.</p>`;

  if (slug.includes('youtube-video-downloader') || slug.includes('tiktok-video-downloader') || slug.includes('instagram-reel-downloader')) panel.innerHTML = urlForm;
  else if (slug.includes('video-to-gif-converter')) panel.innerHTML = uploadForm('/api/v1/media/video-to-gif','Convert to GIF','<input name="fps" type="number" min="5" max="24" value="12" class="w-full rounded border p-2 dark:bg-slate-800"/>');
  else if (slug.includes('video-audio-extractor')) panel.innerHTML = uploadForm('/api/v1/media/extract-audio','Extract MP3','<select name="bitrate" class="w-full rounded border p-2 dark:bg-slate-800"><option>128k</option><option selected>192k</option><option>256k</option></select>');
  else return;

  wireHandlers();
}

function wireHandlers() {
  const form = document.getElementById('mediaUrlForm');
  if (form) {
    const result = document.getElementById('mediaResult');
    const select = document.getElementById('formatSelect');
    const fetchBtn = document.getElementById('fetchBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const preview = document.getElementById('mediaPreview');
    const thumb = document.getElementById('mediaThumb');
    const title = document.getElementById('mediaTitle');

    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData(form);
      fetchBtn.textContent='Fetching...'; fetchBtn.disabled=true;
      result.textContent='';
      try {
        const r = await fetch('/api/v1/media/metadata',{method:'POST', body:fd});
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Metadata error');
        title.textContent = data.title || 'Video';
        if (data.thumbnail) { thumb.src = data.thumbnail; preview.classList.remove('hidden'); }
        result.textContent = JSON.stringify({title:data.title, duration:data.duration}, null, 2);
        select.innerHTML = '<option value="">Best</option>' + (data.formats||[]).map(f=>`<option value="${f.format_id}">${f.resolution} (${f.ext})</option>`).join('');
      } catch (err) {
        result.textContent = `Metadata failed: ${err.message}`;
      } finally { fetchBtn.textContent='Fetch Metadata'; fetchBtn.disabled=false; }
    });

    downloadBtn?.addEventListener('click', async ()=>{
      const fd = new FormData(form);
      fd.set('format_id', select.value);
      downloadBtn.textContent='Downloading...'; downloadBtn.disabled=true;
      try {
        const r = await fetch('/api/v1/media/download',{method:'POST', body:fd});
        if (!r.ok) throw new Error('Network response was not ok');
        const blob = await r.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display='none';
        a.href=url;
        a.download='MZ_Tools_Media.mp4';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      } catch {
        alert('Download execution failed. Please retry!');
      } finally {
        downloadBtn.textContent='Download'; downloadBtn.disabled=false;
      }
    });
  }

  document.querySelectorAll('.mediaUploadForm').forEach((f)=>f.addEventListener('submit', async(e)=>{
    e.preventDefault();
    const btn = f.querySelector('button');
    btn.textContent='Processing...'; btn.disabled=true;
    const fd = new FormData(f);
    const r = await fetch(f.dataset.endpoint,{method:'POST', body:fd});
    btn.textContent='Done'; btn.disabled=false;
    if(!r.ok){alert('Processing failed');return;}
    const blob = await r.blob();
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download = f.dataset.endpoint.includes('gif') ? 'converted.gif' : 'audio.mp3'; a.click();
  }));
}

window.renderMediaUI = renderMediaUI;
