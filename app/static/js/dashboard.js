let allTools = [];
let activeCategory = 'All';

const grid = document.getElementById('toolsGrid');
const search = document.getElementById('toolSearch');
const pills = document.getElementById('categoryPills');

function card(tool) {
  return `<a href="/tools/${tool.slug}" class="block rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 hover:shadow-xl transition">
    <div class="flex justify-between items-start gap-2"><p class="text-xs text-indigo-500 font-semibold">${tool.category}</p>${tool.premium ? '<span class="text-[10px] px-2 py-1 rounded bg-amber-100 text-amber-700">PRO</span>' : ''}</div>
    <h3 class="text-lg font-bold mt-1">${tool.name}</h3>
    <p class="text-xs mt-2 ${tool.backend_supported ? 'text-emerald-500':'text-slate-400'}">${tool.backend_supported ? 'Backend-powered' : 'Instant in-browser'}</p>
  </a>`;
}

function renderCategories(categories) {
  pills.innerHTML = ['All', ...categories].map(c => `<button class="px-3 py-1 rounded-full border text-sm ${c===activeCategory?'bg-indigo-600 text-white border-indigo-600':'border-slate-300 dark:border-slate-700'}" data-cat="${c}">${c}</button>`).join('');
  pills.querySelectorAll('button').forEach((btn) => btn.addEventListener('click', () => {activeCategory = btn.dataset.cat; renderCards(); renderCategories(categories);}));
}

function renderCards() {
  const q = (search?.value || '').toLowerCase();
  const list = allTools.filter((t) => (activeCategory === 'All' || t.category === activeCategory) && (`${t.name} ${t.category}`.toLowerCase().includes(q)));
  grid.innerHTML = list.map(card).join('');
}

search?.addEventListener('input', renderCards);

fetch('/api/v1/tools/catalog').then(r => r.json()).then((data) => {
  const categories = data.map(c => c.category);
  allTools = data.flatMap(c => c.tools);
  renderCategories(categories);
  renderCards();
}).catch(() => {
  grid.innerHTML = '<p class="text-red-500">Unable to load tool catalog.</p>';
});
