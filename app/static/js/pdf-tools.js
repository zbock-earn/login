function isPdfSlug(slug){
  return slug.includes('pdf-') || slug.includes('word-to-pdf') || slug.includes('image-to-pdf-converter') || slug.includes('epub-to-pdf-converter') || slug.includes('txt-to-pdf');
}

function renderPdfUI(slug){
  const panel=document.getElementById('backendPanel'); if(!panel||!isPdfSlug(slug)) return;
  const map={
    'pdf-merger-combine-multiple-pdfs': `<form class="pdfForm" data-endpoint="/api/v1/pdf/merge"><input type=file name=files multiple accept="application/pdf" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Merge PDFs</button></form>`,
    'pdf-splitter': `<form class="pdfForm" data-endpoint="/api/v1/pdf/split"><input type=file name=file accept="application/pdf" required class="w-full border rounded p-2"><input name=pages placeholder="e.g. 1,2,5" class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Split PDF</button></form>`,
    'pdf-to-word-converter-simple-text-extraction': `<form class="pdfForm" data-endpoint="/api/v1/pdf/pdf-to-word"><input type=file name=file accept="application/pdf" required class="w-full border rounded p-2"><select name=output class="w-full border rounded p-2 dark:bg-slate-800"><option value=txt>TXT</option><option value=docx>DOCX</option></select><button class="px-3 py-2 rounded bg-indigo-600 text-white">Convert</button></form>`,
    'word-to-pdf': `<form class="pdfForm" data-endpoint="/api/v1/pdf/word-to-pdf"><input type=file name=file accept=".txt,.doc,.docx" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Word to PDF</button></form>`,
    'pdf-password-remover': `<form class="pdfForm" data-endpoint="/api/v1/pdf/password-remover"><input type=file name=file accept="application/pdf" required class="w-full border rounded p-2"><input name=password type=password placeholder="Password if required" class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Remove Password</button></form>`,
    'image-to-pdf-converter': `<form class="pdfForm" data-endpoint="/api/v1/pdf/image-to-pdf"><input type=file name=files multiple accept="image/*" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">Images to PDF</button></form>`,
    'epub-to-pdf-converter': `<form class="pdfForm" data-endpoint="/api/v1/pdf/epub-to-pdf"><input type=file name=file accept=".epub" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">EPUB to PDF</button></form>`,
    'txt-to-pdf': `<form class="pdfForm" data-endpoint="/api/v1/pdf/txt-to-pdf"><input type=file name=file accept=".txt,text/plain" required class="w-full border rounded p-2"><button class="px-3 py-2 rounded bg-indigo-600 text-white">TXT to PDF</button></form>`,
  };
  panel.innerHTML = map[slug] || panel.innerHTML;
  bindPdfHandlers();
}

function bindPdfHandlers(){
  document.querySelectorAll('.pdfForm').forEach(f=>f.addEventListener('submit', async(e)=>{
    e.preventDefault(); const fd = new FormData(f);
    const r = await fetch(f.dataset.endpoint,{method:'POST',body:fd});
    if(!r.ok){alert('PDF operation failed'); return;}
    const blob = await r.blob();
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    const ep=f.dataset.endpoint;
    a.download= ep.includes('pdf-to-word')? 'converted.txt' : ep.includes('split')?'split.pdf':ep.includes('merge')?'merged.pdf':'output.pdf';
    a.click();
  }));
}

window.renderPdfUI = renderPdfUI;
