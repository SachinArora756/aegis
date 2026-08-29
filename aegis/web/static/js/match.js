/* Aegis Dashboard — Match Results Page */

document.addEventListener('DOMContentLoaded', () => {
  loadMatchResults();
});

async function loadMatchResults() {
  const container = document.getElementById('match-results');
  if (!container) return;

  container.innerHTML = '<div class="text-center py-12 text-gray-500">Loading match results...</div>';

  try {
    const results = await fetchJSON('/api/match/results');
    if (!results.length) {
      container.innerHTML = '<div class="text-center py-12 text-gray-500">No match results yet. Run a match cycle or demo to see results.</div>';
      return;
    }
    renderGrouped(container, results);
  } catch {
    container.innerHTML = '<div class="text-center py-12 text-red-400">Failed to load match results</div>';
  }
}

function renderGrouped(container, results) {
  const grouped = {};
  results.forEach(r => {
    const key = r.news_id || r.news_title || 'Unknown Incident';
    if (!grouped[key]) grouped[key] = { title: r.news_title || `Incident #${r.news_id}`, items: [] };
    grouped[key].items.push(r);
  });

  container.innerHTML = Object.values(grouped).map(group => `
    <div class="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden mb-4">
      <div class="p-4 border-b border-gray-700/50">
        <h3 class="text-sm font-semibold text-gray-200">${escapeHtml(group.title)}</h3>
        <div class="flex gap-3 mt-2">
          ${summaryBadges(group.items)}
        </div>
      </div>
      <div class="divide-y divide-gray-700/30">
        ${group.items.map(renderMatchItem).join('')}
      </div>
    </div>
  `).join('');
}

function summaryBadges(items) {
  const vuln = items.filter(i => i.is_vulnerable === true).length;
  const safe = items.filter(i => i.is_vulnerable === false).length;
  const notFound = items.filter(i => i.is_vulnerable == null && i.status === 'not_found').length;
  const parts = [];
  if (vuln) parts.push(`<span class="text-xs font-medium text-red-400">${vuln} vulnerable</span>`);
  if (safe) parts.push(`<span class="text-xs font-medium text-green-400">${safe} safe</span>`);
  if (notFound) parts.push(`<span class="text-xs font-medium text-gray-500">${notFound} not found</span>`);
  return parts.join('');
}

function renderMatchItem(item) {
  const statusColor = item.is_vulnerable === true ? 'border-l-red-500'
    : item.is_vulnerable === false ? 'border-l-green-500'
    : 'border-l-gray-600';

  const statusIcon = item.is_vulnerable === true ? '<span class="text-red-400 text-lg">&#9888;</span>'
    : item.is_vulnerable === false ? '<span class="text-green-400 text-lg">&#10003;</span>'
    : '<span class="text-gray-500 text-lg">?</span>';

  return `
    <div class="flex items-center gap-4 px-4 py-3 border-l-4 ${statusColor}">
      <div class="flex-shrink-0">${statusIcon}</div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium text-gray-200">${escapeHtml(item.component_name || '')}</span>
          <span class="text-xs text-gray-500 font-mono">${escapeHtml(item.version_in_use || '')}</span>
          ${item.ecosystem ? ecosystemTag(item.ecosystem) : ''}
        </div>
        <div class="text-xs text-gray-500 mt-0.5">
          ${item.repo ? `<span>${escapeHtml(item.repo)}</span>` : ''}
          ${item.purl ? `<span class="font-mono ml-2">${escapeHtml(item.purl)}</span>` : ''}
        </div>
      </div>
      <div class="flex-shrink-0 text-right">
        ${item.vulnerable_versions ? `<div class="text-xs text-red-400 font-mono">${escapeHtml(item.vulnerable_versions)}</div>` : ''}
        ${matchStatusLabel(item)}
      </div>
    </div>
  `;
}

function ecosystemTag(eco) {
  return `<span class="text-xs bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded">${escapeHtml(eco)}</span>`;
}

function matchStatusLabel(item) {
  if (item.is_vulnerable === true) return '<span class="text-xs font-medium text-red-400">VULNERABLE</span>';
  if (item.is_vulnerable === false) return '<span class="text-xs font-medium text-green-400">SAFE</span>';
  if (item.status === 'not_found') return '<span class="text-xs font-medium text-gray-500">NOT FOUND</span>';
  if (item.status === 'manual_review') return '<span class="text-xs font-medium text-yellow-400">REVIEW</span>';
  return '<span class="text-xs text-gray-500">UNKNOWN</span>';
}
