let allTools = [];
let allStats = null;
let activeCategory = 'All';

const grid = document.getElementById('toolsGrid');
const search = document.getElementById('toolSearch');
const pills = document.getElementById('categoryPills');
const statsEl = document.getElementById('catalogStats');

function card(tool) {
  return `<a href="/tools/${tool.slug}" class="group block rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 hover:shadow-2xl transition hover:-translate-y-1">
    <div class="flex justify-between items-start gap-2">
      <p class="text-xs text-indigo-500 font-semibold">${tool.category}</p>
      <div class="flex gap-1">${tool.premium ? '<span class="text-[10px] px-2 py-1 rounded bg-amber-100 text-amber-700">PRO</span>' : ''}</div>
    </div>
    <h3 class="text-lg font-bold mt-2 group-hover:text-indigo-500">${tool.name}</h3>
    <div class="mt-3 flex items-center justify-between text-xs">
      <span class="${tool.backend_supported ? 'text-emerald-500':'text-slate-400'}">${tool.backend_supported ? 'Backend-powered' : 'Instant in-browser'}</span>
      <span class="text-slate-400">Open tool →</span>
    </div>
  </a>`;
}

function renderCategories(categories) {
  pills.innerHTML = ['All', ...categories].map(c => `<button class="px-3 py-1 rounded-full border text-sm ${c===activeCategory?'bg-indigo-600 text-white border-indigo-600':'border-slate-300 dark:border-slate-700'}" data-cat="${c}">${c}</button>`).join('');
  pills.querySelectorAll('button').forEach((btn) => btn.addEventListener('click', () => {activeCategory = btn.dataset.cat; renderCards(); renderCategories(categories);}));
}

function renderStats() {
  if (!statsEl || !allStats) return;
  statsEl.innerHTML = `
    <div class="rounded-xl p-4 border bg-white dark:bg-slate-900">Tools <p class="text-2xl font-bold">${allStats.total_tools}</p></div>
    <div class="rounded-xl p-4 border bg-white dark:bg-slate-900">Categories <p class="text-2xl font-bold">${allStats.total_categories}</p></div>
    <div class="rounded-xl p-4 border bg-white dark:bg-slate-900">Backend Tools <p class="text-2xl font-bold">${allStats.backend_supported}</p></div>
    <div class="rounded-xl p-4 border bg-white dark:bg-slate-900">Premium <p class="text-2xl font-bold">${allStats.premium_tools}</p></div>`;
}

function renderCards() {
  const q = (search?.value || '').toLowerCase();
  const list = allTools.filter((t) => (activeCategory === 'All' || t.category === activeCategory) && (`${t.name} ${t.category}`.toLowerCase().includes(q)));
  grid.innerHTML = list.map(card).join('');
}

search?.addEventListener('input', renderCards);

fetch('/api/v1/tools/catalog?include_stats=true').then(r => r.json()).then((payload) => {
  const categories = payload.categories.map(c => c.category);
  allTools = payload.categories.flatMap(c => c.tools);
  allStats = payload.stats;
  renderCategories(categories);
  renderStats();
  renderCards();
}).catch(() => {
  grid.innerHTML = '<p class="text-red-500">Unable to load tool catalog.</p>';
});
