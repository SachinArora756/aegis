/* Aegis Dashboard — Global Utilities */

async function fetchJSON(url, options = {}) {
  try {
    const resp = await fetch(url, {
      headers: { 'Accept': 'application/json', ...options.headers },
      ...options,
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${text}`);
    }
    return await resp.json();
  } catch (err) {
    console.error(`fetchJSON(${url}):`, err);
    throw err;
  }
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return 'unknown';
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.max(0, now - then);
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

function escapeHtml(str) {
  const el = document.createElement('span');
  el.textContent = str;
  return el.innerHTML;
}

function classificationBadge(cls) {
  const map = {
    supply_chain_vuln: { label: 'Supply Chain', css: 'badge-supply-chain' },
    threat_intel:      { label: 'Threat Intel', css: 'badge-threat-intel' },
    general_info:      { label: 'General',      css: 'badge-general-info' },
  };
  const info = map[cls] || { label: cls || 'Unknown', css: 'badge-general-info' };
  return `<span class="badge ${info.css}">${escapeHtml(info.label)}</span>`;
}

function severityBadge(severity) {
  if (!severity) return '';
  const s = severity.toLowerCase();
  const colors = {
    critical: 'bg-severity-critical',
    high:     'bg-severity-high',
    medium:   'bg-severity-medium',
    low:      'bg-severity-low',
  };
  const bg = colors[s] || 'bg-gray-600';
  return `<span class="badge text-white ${bg}">${escapeHtml(severity)}</span>`;
}

function impactBar(score) {
  if (score == null) return '';
  const pct = Math.min(100, Math.max(0, score * 10));
  let level = 'low';
  if (score >= 8) level = 'critical';
  else if (score >= 6) level = 'high';
  else if (score >= 4) level = 'medium';
  return `<div class="impact-bar w-full">
    <div class="impact-bar-fill ${level}" style="width:${pct}%"></div>
  </div>`;
}

/* Theme */
(function initTheme() {
  const stored = localStorage.getItem('aegis-theme');
  if (stored === 'light') {
    document.documentElement.classList.remove('dark');
  } else {
    document.documentElement.classList.add('dark');
  }
})();

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('aegis-theme', isDark ? 'dark' : 'light');
}

/* Active nav link */
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === '/' && path === '/') {
      link.classList.add('active');
    } else if (href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    }
  });
});

/* Toast notifications */
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'toast-out 0.3s ease forwards';
    toast.addEventListener('animationend', () => toast.remove());
  }, 4000);
}

/* Counting animation for stat numbers */
function animateCount(el, target, duration = 800) {
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased).toLocaleString();
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
