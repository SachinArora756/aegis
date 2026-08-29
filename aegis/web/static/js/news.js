/* Aegis Dashboard — News Page */

let allArticles = [];

document.addEventListener('DOMContentLoaded', () => {
  loadArticles();

  document.querySelectorAll('.news-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.news-tab').forEach(t => t.classList.remove('active', 'border-blue-400', 'text-blue-400'));
      tab.classList.add('active', 'border-blue-400', 'text-blue-400');
      filterByClassification(tab.dataset.classification);
    });
  });

  document.getElementById('btn-news-run')?.addEventListener('click', runNewsCycle);
});

async function loadArticles() {
  const container = document.getElementById('news-grid');
  if (!container) return;

  container.innerHTML = '<div class="col-span-full text-center py-12 text-gray-500">Loading articles...</div>';

  try {
    allArticles = await fetchJSON('/api/news/articles');
    renderArticles(allArticles);
    updateNewsCounts();
  } catch {
    container.innerHTML = '<div class="col-span-full text-center py-12 text-red-400">Failed to load articles</div>';
  }
}

function filterByClassification(cls) {
  if (!cls || cls === 'all') {
    renderArticles(allArticles);
  } else {
    renderArticles(allArticles.filter(a => a.classification === cls));
  }
}

function renderArticles(articles) {
  const container = document.getElementById('news-grid');
  if (!container) return;

  if (!articles.length) {
    container.innerHTML = '<div class="col-span-full text-center py-12 text-gray-500">No articles found. Run a news cycle to fetch articles.</div>';
    return;
  }

  container.innerHTML = articles.map(a => `
    <div class="bg-gray-800/50 rounded-lg border border-gray-700/50 p-5 card-hover cursor-pointer" onclick="viewArticle(${a.id})">
      <div class="flex items-start justify-between gap-2 mb-3">
        ${classificationBadge(a.classification)}
        ${a.impact_score != null ? `<span class="text-xs font-mono ${a.impact_score >= 7 ? 'text-red-400' : 'text-gray-500'}">${a.impact_score}/10</span>` : ''}
      </div>
      <h3 class="text-sm font-semibold text-gray-200 mb-2 line-clamp-2">${escapeHtml(a.title)}</h3>
      <p class="text-xs text-gray-500 mb-3">${escapeHtml(a.source || 'Unknown source')} &middot; ${formatTimeAgo(a.published)}</p>
      ${a.summary ? `<p class="text-xs text-gray-400 line-clamp-3 mb-3">${escapeHtml(a.summary)}</p>` : ''}
      ${a.impact_score != null ? `<div class="mb-3">${impactBar(a.impact_score)}</div>` : ''}
      ${renderAffectedPackages(a.affected_packages)}
    </div>
  `).join('');
}

function renderAffectedPackages(packages) {
  if (!packages?.length) return '';
  return `
    <div class="flex flex-wrap gap-1 mt-2">
      ${packages.slice(0, 5).map(p => {
        const name = typeof p === 'string' ? p : (p.name || '');
        return `<span class="text-xs bg-gray-700/80 text-gray-300 px-2 py-0.5 rounded font-mono">${escapeHtml(name)}</span>`;
      }).join('')}
      ${packages.length > 5 ? `<span class="text-xs text-gray-500">+${packages.length - 5}</span>` : ''}
    </div>
  `;
}

function viewArticle(id) {
  window.location.href = `/news/${id}`;
}

function updateNewsCounts() {
  const counts = { all: allArticles.length, supply_chain_vuln: 0, threat_intel: 0, general_info: 0 };
  allArticles.forEach(a => {
    if (counts[a.classification] !== undefined) counts[a.classification]++;
  });
  Object.entries(counts).forEach(([key, val]) => {
    const el = document.getElementById(`count-${key}`);
    if (el) el.textContent = val;
  });
}

async function runNewsCycle() {
  const btn = document.getElementById('btn-news-run');
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = 'Running...';
  try {
    const result = await fetchJSON('/api/news/run', { method: 'POST' });
    showToast(result.message || 'News cycle complete', 'success');
    await loadArticles();
  } catch {
    showToast('News cycle failed', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run News Cycle';
  }
}
