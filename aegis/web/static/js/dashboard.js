/* Aegis Dashboard — Dashboard Page */

document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadRecentAlerts();
  wireActions();

  if (!document.body.dataset.demo) {
    setInterval(loadStats, 60000);
  }
});

async function loadStats() {
  try {
    const data = await fetchJSON('/api/stats');
    const map = {
      'stat-repos': data.repos_scanned ?? 0,
      'stat-components': data.total_components ?? 0,
      'stat-vulns': data.active_vulns ?? 0,
      'stat-articles': data.articles_today ?? 0,
    };
    for (const [id, val] of Object.entries(map)) {
      const el = document.getElementById(id);
      if (el) animateCount(el, val);
    }
    const lastRun = document.getElementById('last-run');
    if (lastRun && data.last_run) {
      lastRun.textContent = formatTimeAgo(data.last_run);
    }
  } catch {
    showToast('Failed to load stats', 'error');
  }
}

async function loadRecentAlerts() {
  const container = document.getElementById('recent-alerts');
  if (!container) return;
  try {
    const articles = await fetchJSON('/api/news/articles?limit=10');
    if (!articles.length) {
      container.innerHTML = '<p class="text-gray-500 text-sm text-center py-8">No recent alerts. Run a news cycle or demo to see results.</p>';
      return;
    }
    container.innerHTML = articles.map(a => `
      <div class="bg-gray-800/50 rounded-lg p-4 card-hover border border-gray-700/50">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-200 truncate">${escapeHtml(a.title)}</h4>
            <p class="text-xs text-gray-500 mt-1">${escapeHtml(a.source || '')} &middot; ${formatTimeAgo(a.published)}</p>
          </div>
          <div class="flex-shrink-0">${classificationBadge(a.classification)}</div>
        </div>
        ${a.impact_score != null ? `<div class="mt-2">${impactBar(a.impact_score)}</div>` : ''}
        ${a.affected_packages?.length ? `
          <div class="mt-2 flex flex-wrap gap-1">
            ${a.affected_packages.slice(0, 4).map(p =>
              `<span class="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">${escapeHtml(typeof p === 'string' ? p : p.name || '')}</span>`
            ).join('')}
            ${a.affected_packages.length > 4 ? `<span class="text-xs text-gray-500">+${a.affected_packages.length - 4} more</span>` : ''}
          </div>
        ` : ''}
      </div>
    `).join('');
  } catch {
    container.innerHTML = '<p class="text-red-400 text-sm text-center py-4">Failed to load alerts</p>';
  }
}

function wireActions() {
  const btnSbom = document.getElementById('action-sbom');
  if (btnSbom) btnSbom.addEventListener('click', () => { window.location.href = '/sbom'; });

  const btnNews = document.getElementById('action-news');
  if (btnNews) btnNews.addEventListener('click', async () => {
    btnNews.disabled = true;
    btnNews.textContent = 'Running...';
    try {
      const result = await fetchJSON('/api/news/run', { method: 'POST' });
      showToast(result.message || 'News cycle complete', 'success');
      loadRecentAlerts();
    } catch {
      showToast('News cycle failed', 'error');
    } finally {
      btnNews.disabled = false;
      btnNews.textContent = 'Run News Cycle';
    }
  });

  const btnDemo = document.getElementById('action-demo');
  if (btnDemo) btnDemo.addEventListener('click', () => { window.location.href = '/demo'; });
}
