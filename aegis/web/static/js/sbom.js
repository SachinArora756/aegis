/* Aegis Dashboard — SBOM Page */

let allComponents = [];
let debounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  loadComponents();

  const search = document.getElementById('sbom-search');
  if (search) search.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyFilters, 300);
  });

  document.getElementById('filter-ecosystem')?.addEventListener('change', applyFilters);
  document.getElementById('filter-repo')?.addEventListener('change', applyFilters);
});

async function loadComponents() {
  const tbody = document.getElementById('sbom-table-body');
  const statsBar = document.getElementById('sbom-stats');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-gray-500">Loading...</td></tr>';

  try {
    allComponents = await fetchJSON('/api/sbom/components');
    populateFilterDropdowns();
    renderTable(allComponents);
    renderStats(allComponents);
  } catch {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-red-400">Failed to load SBOM data</td></tr>';
  }
}

function populateFilterDropdowns() {
  const ecosystems = [...new Set(allComponents.map(c => c.ecosystem).filter(Boolean))].sort();
  const repos = [...new Set(allComponents.map(c => c.repo).filter(Boolean))].sort();

  const ecoSelect = document.getElementById('filter-ecosystem');
  if (ecoSelect) {
    ecoSelect.innerHTML = '<option value="">All Ecosystems</option>' +
      ecosystems.map(e => `<option value="${escapeHtml(e)}">${escapeHtml(e)}</option>`).join('');
  }

  const repoSelect = document.getElementById('filter-repo');
  if (repoSelect) {
    repoSelect.innerHTML = '<option value="">All Repos</option>' +
      repos.map(r => `<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`).join('');
  }
}

function applyFilters() {
  const search = (document.getElementById('sbom-search')?.value || '').toLowerCase();
  const eco = document.getElementById('filter-ecosystem')?.value || '';
  const repo = document.getElementById('filter-repo')?.value || '';

  const filtered = allComponents.filter(c => {
    if (search && !c.component_name?.toLowerCase().includes(search) && !c.purl?.toLowerCase().includes(search)) return false;
    if (eco && c.ecosystem !== eco) return false;
    if (repo && c.repo !== repo) return false;
    return true;
  });

  renderTable(filtered);
  renderStats(filtered);
}

function renderTable(components) {
  const tbody = document.getElementById('sbom-table-body');
  if (!tbody) return;

  if (!components.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-gray-500">No components found</td></tr>';
    return;
  }

  tbody.innerHTML = components.map((c, i) => `
    <tr class="table-row-hover border-b border-gray-700/50 cursor-pointer" onclick="toggleRow(${i})">
      <td class="px-4 py-3 text-sm text-gray-300">${escapeHtml(c.repo || '')}</td>
      <td class="px-4 py-3 text-sm font-medium text-gray-200">${escapeHtml(c.component_name || '')}</td>
      <td class="px-4 py-3 text-sm text-gray-400 font-mono">${escapeHtml(c.version || '')}</td>
      <td class="px-4 py-3 text-sm text-gray-500 font-mono text-xs max-w-[200px] truncate" title="${escapeHtml(c.purl || '')}">${escapeHtml(c.purl || '')}</td>
      <td class="px-4 py-3 text-sm">${ecosystemBadge(c.ecosystem)}</td>
      <td class="px-4 py-3 text-sm text-gray-400">${escapeHtml(c.license || '-')}</td>
      <td class="px-4 py-3 text-sm">${vulnCount(c.vulnerabilities)}</td>
    </tr>
    <tr id="detail-${i}" class="hidden bg-gray-800/30">
      <td colspan="7" class="px-6 py-4">
        ${renderDetail(c)}
      </td>
    </tr>
  `).join('');
}

function toggleRow(idx) {
  const row = document.getElementById(`detail-${idx}`);
  if (row) row.classList.toggle('hidden');
}

function ecosystemBadge(eco) {
  if (!eco) return '<span class="text-gray-500">-</span>';
  const colors = { npm: 'bg-red-900/40 text-red-300', pypi: 'bg-blue-900/40 text-blue-300', go: 'bg-cyan-900/40 text-cyan-300', maven: 'bg-orange-900/40 text-orange-300', cargo: 'bg-yellow-900/40 text-yellow-300' };
  const cls = colors[eco.toLowerCase()] || 'bg-gray-700 text-gray-300';
  return `<span class="inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}">${escapeHtml(eco)}</span>`;
}

function vulnCount(vulns) {
  if (!vulns || !vulns.length) return '<span class="text-green-400 text-xs font-medium">Clean</span>';
  const critHigh = vulns.filter(v => v.severity === 'Critical' || v.severity === 'High').length;
  if (critHigh > 0) return `<span class="text-red-400 font-medium text-xs">${vulns.length} (${critHigh} critical/high)</span>`;
  return `<span class="text-yellow-400 text-xs font-medium">${vulns.length}</span>`;
}

function renderDetail(c) {
  const parts = [];
  if (c.purl) parts.push(`<p class="text-xs text-gray-500 font-mono mb-2">${escapeHtml(c.purl)}</p>`);
  if (c.vulnerabilities?.length) {
    parts.push('<div class="space-y-2">');
    c.vulnerabilities.forEach(v => {
      parts.push(`
        <div class="flex items-center gap-3 bg-gray-900/50 rounded p-2">
          ${severityBadge(v.severity)}
          <span class="text-sm text-gray-300 font-mono">${escapeHtml(v.cve || v.id || '')}</span>
          <span class="text-xs text-gray-500 flex-1">${escapeHtml(v.description || '')}</span>
          ${v.fixed_version ? `<span class="text-xs text-green-400">Fix: ${escapeHtml(v.fixed_version)}</span>` : ''}
        </div>
      `);
    });
    parts.push('</div>');
  } else {
    parts.push('<p class="text-sm text-green-400">No known vulnerabilities</p>');
  }
  return parts.join('');
}

function renderStats(components) {
  const el = document.getElementById('sbom-stats');
  if (!el) return;
  const repos = new Set(components.map(c => c.repo)).size;
  const totalVulns = components.reduce((n, c) => n + (c.vulnerabilities?.length || 0), 0);
  el.innerHTML = `
    <span class="text-gray-400">${components.length} components</span>
    <span class="text-gray-600">&middot;</span>
    <span class="text-gray-400">${repos} repos</span>
    <span class="text-gray-600">&middot;</span>
    <span class="${totalVulns ? 'text-red-400' : 'text-green-400'}">${totalVulns} vulnerabilities</span>
  `;
}
