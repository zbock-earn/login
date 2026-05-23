const categories = {
  "Media & Video Tools": ["YouTube Video Downloader", "TikTok Video Downloader", "Instagram Reel Downloader", "Video to GIF Converter", "Video Audio Extractor"],
  "Image & Graphic Tools": ["Image Compressor", "Image Format Converter", "Image Resizer", "Image Cropper", "Background Remover", "Color Picker from Image", "Palette Generator", "Text to Image Placeholder Generator", "Image Blur/Sharpen Tool", "Base64 to Image & Vice Versa"],
  "PDF & Document Tools": ["PDF Merger", "PDF Splitter", "PDF to Word Converter", "Word to PDF", "PDF Password Remover", "Image to PDF Converter", "EPUB to PDF Converter", "TXT to PDF"],
  "Text & Content Tools": ["Case Converter", "Word & Character Counter", "Remove Duplicate Lines", "Text Reverser", "Lorem Ipsum Placeholder Generator", "Find and Replace Text", "URL Encoder / Decoder", "HTML Entity Encoder / Decoder", "Markdown to HTML Converter", "Text Diff Checker", "Slug Generator", "Binary to Text & Vice Versa"],
  "Calculators & Converters": ["Currency Converter", "Age Calculator", "Percentage Calculator", "GST / Tax Calculator", "Loan / EMI Calculator", "Unit Converter", "Hex to RGB & RGB to Hex Converter", "Binary/Octal/Hexadecimal Converter", "Time Zone Converter", "Crypto Price Ticker / Converter"],
  "Developer & Cyber Tools": ["Strong Password Generator", "QR Code Generator", "QR Code Scanner", "HTML Formatter / Minifier", "CSS Formatter / Minifier", "JSON Formatter / Validator", "User Agent Finder", "MD5 / SHA-256 Hash Generator", "IP Address Finder", "Website Ping / Status Checker"]
};

const allTools = Object.entries(categories).flatMap(([category, tools]) =>
  tools.map((name) => ({ name, category, slug: name.toLowerCase().replace(/[^a-z0-9]+/g, '-') }))
);

const grid = document.getElementById('toolsGrid');
const search = document.getElementById('toolSearch');

function renderCards(list) {
  grid.innerHTML = list.map((tool) => `
    <a href="/tools/${tool.slug}" class="block rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 hover:shadow-lg">
      <p class="text-xs text-indigo-500 font-semibold">${tool.category}</p>
      <h3 class="text-lg font-bold mt-1">${tool.name}</h3>
    </a>
  `).join('');
}

search?.addEventListener('input', (e) => {
  const q = e.target.value.toLowerCase();
  renderCards(allTools.filter((t) => t.name.toLowerCase().includes(q) || t.category.toLowerCase().includes(q)));
});

renderCards(allTools);
