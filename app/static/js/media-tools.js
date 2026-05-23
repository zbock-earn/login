function renderMediaUI(slug) {
  const panel = document.getElementById('backendPanel');
  if (!panel) return;

  const urlForm = `
    <form id="mediaUrlForm" class="space-y-2">
      <input name="url" required placeholder="Paste video URL" class="w-full rounded border p-2 dark:bg-slate-800" />
      <div class="flex gap-2">
        <button id="fetchBtn" class="px-3 py-2 rounded bg-indigo-600 text-white" type="submit">Fetch Metadata</button>
        <button id="downloadBtn" class="px-3 py-2 rounded bg-emerald-600 text-white" type="button">Download</button>
      </div>
      <select id="formatSelect" class="w-full rounded border p-2 dark:bg-slate-800"><option value="">Best</option></select>
    </form>
    <div class="text-xs"><a href="YOUR_MONETAG_DIRECT_LINK_HERE" target="_blank" class="underline">Sponsored Link</a></div>
    <pre id="mediaResult" class="text-xs bg-slate-100 dark:bg-slate-800 rounded p-2"></pre>`;

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

  wireHandlers(slug);
}

function wireHandlers(slug) {
  const form = document.getElementById('mediaUrlForm');
  if (form) {
    const result = document.getElementById('mediaResult');
    const select = document.getElementById('formatSelect');
    const fetchBtn = document.getElementById('fetchBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData(form);
      fetchBtn.textContent='Fetching...'; fetchBtn.disabled=true;
      try {
        const r = await fetch('/api/v1/media/metadata',{method:'POST', body:fd});
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Metadata error');
        result.textContent = JSON.stringify({title:data.title, duration:data.duration, warning:data.warning||null}, null, 2); if(data.fallback_url){result.innerHTML += `\nFallback URL: <a class='underline' target='_blank' href='${data.fallback_url}'>Open</a>`;}
        select.innerHTML = '<option value="">Best</option>' + (data.formats||[]).map(f=>`<option value="${f.format_id}">${f.resolution} (${f.ext})</option>`).join('');
      } catch (err) {
        result.innerHTML = `Metadata failed (${err.message}). Fallback: open source directly.\n<a class='underline' target='_blank' href='${fd.get('url')}'>Open Video URL</a>`;
      } finally { fetchBtn.textContent='Fetch Metadata'; fetchBtn.disabled=false; }
    });

    downloadBtn?.addEventListener('click', async ()=>{
      window.open('YOUR_MONETAG_DIRECT_LINK_HERE','_blank');
      const fd = new FormData(form);
      fd.set('format_id', select.value);
      downloadBtn.textContent='Downloading...'; downloadBtn.disabled=true;
      try {
        const r = await fetch('/api/v1/media/download',{method:'POST', body:fd});
        if (r.status===202){const j=await r.json(); result.innerHTML=`${j.message} <a class='underline' target='_blank' href='${j.fallback_url}'>Open Fallback</a>`; return;}
        if (!r.ok) throw new Error('Download failed');
        const blob=await r.blob(); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='video.mp4'; a.click();
      } catch {
        result.innerHTML = `Download failed. Fallback: <a class='underline' target='_blank' href='${fd.get('url')}'>Open source</a>`;
      } finally { downloadBtn.textContent='Download'; downloadBtn.disabled=false; }
    });
  }

  document.querySelectorAll('.mediaUploadForm').forEach((f)=>f.addEventListener('submit', async(e)=>{
    e.preventDefault();
    window.open('YOUR_MONETAG_DIRECT_LINK_HERE','_blank');
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
