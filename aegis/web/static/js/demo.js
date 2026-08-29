/* Aegis Dashboard — Demo Page */

let ws = null;
let terminal = null;

document.addEventListener('DOMContentLoaded', () => {
  terminal = new Terminal('terminal-output');

  document.querySelectorAll('.demo-btn[data-section]').forEach(btn => {
    btn.addEventListener('click', () => runDemo(btn.dataset.section));
  });
  document.getElementById('btn-clear')?.addEventListener('click', () => {
    terminal.clear();
    resetPipeline();
    updateStatus('idle');
    updateLineCount();
  });
});

function runDemo(section) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close();
  }

  terminal.clear();
  terminal.showCursor();
  setButtons(false);
  resetPipeline();
  updateStatus('running');

  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${window.location.host}/api/demo/stream/${section}`;
  ws = new WebSocket(url);

  ws.onopen = () => {
    const fast = document.getElementById('fast-mode')?.checked || false;
    ws.send(JSON.stringify({ fast }));
  };

  ws.onmessage = (evt) => {
    try {
      const event = JSON.parse(evt.data);
      handleEvent(event);
      updateLineCount();
    } catch {
      terminal.writeLine(evt.data, 'step');
      updateLineCount();
    }
  };

  ws.onclose = () => {
    terminal.hideCursor();
    setButtons(true);
    updateStatus('idle');
  };

  ws.onerror = () => {
    terminal.writeLine('Connection error — is the server running?', 'alert');
    terminal.hideCursor();
    setButtons(true);
    updateStatus('error');
  };
}

function handleEvent(event) {
  switch (event.type) {
    case 'line':
      terminal.writeLine(event.text || '', event.style || 'step');
      break;

    case 'box':
      terminal.writeBox(event.lines || []);
      break;

    case 'highlight':
      highlightNode(event.node, event.state || 'active');
      break;

    case 'phase':
      terminal.writeLine('', 'step');
      terminal.writeLine(`${'='.repeat(60)}`, 'divider');
      terminal.writeLine(event.text || event.name || '', 'header');
      terminal.writeLine(`${'='.repeat(60)}`, 'divider');
      terminal.writeLine('', 'step');
      break;

    case 'done':
      terminal.hideCursor();
      terminal.writeLine('', 'step');
      terminal.writeLine('Demo complete.', 'ok');
      setButtons(true);
      updateStatus('complete');
      setAllNodesDone();
      break;

    default:
      if (event.text) terminal.writeLine(event.text, event.style || 'step');
  }
}

function setButtons(enabled) {
  ['btn-full', 'btn-sbom', 'btn-news', 'btn-match', 'btn-chat'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.disabled = !enabled;
      btn.classList.toggle('opacity-50', !enabled);
      btn.classList.toggle('cursor-not-allowed', !enabled);
    }
  });
}

function updateStatus(state) {
  const textEl = document.getElementById('demo-status-text');
  const dotEl = document.getElementById('demo-status-dot');
  const map = {
    idle:     { text: 'Idle',     dotCss: 'bg-gray-600',  textCss: 'text-gray-500' },
    running:  { text: 'Running',  dotCss: 'bg-blue-400 animate-pulse',  textCss: 'text-blue-400' },
    complete: { text: 'Complete', dotCss: 'bg-green-400', textCss: 'text-green-400' },
    error:    { text: 'Error',    dotCss: 'bg-red-400',   textCss: 'text-red-400' },
  };
  const s = map[state] || map.idle;
  if (textEl) {
    textEl.textContent = s.text;
    textEl.className = `text-xs ${s.textCss}`;
  }
  if (dotEl) {
    dotEl.className = `w-2 h-2 rounded-full ${s.dotCss}`;
  }
}

function updateLineCount() {
  const el = document.getElementById('terminal-line-count');
  if (el && terminal && terminal.el) {
    const count = terminal.el.children.length;
    el.textContent = `${count} lines`;
  }
}

/* Pipeline diagram */
const STAGES = ['sbom', 'news', 'match', 'validator', 'chat'];

function resetPipeline() {
  STAGES.forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    if (el) {
      el.classList.remove('active', 'completed');
      const status = el.querySelector('.stage-status');
      if (status) status.textContent = 'Idle';
    }
  });
}

function highlightNode(name, state) {
  const el = document.getElementById(`stage-${name}`);
  if (!el) return;
  el.classList.remove('active', 'completed');
  if (state === 'active') {
    el.classList.add('active');
    const status = el.querySelector('.stage-status');
    if (status) status.textContent = 'Running...';
  } else if (state === 'done') {
    el.classList.add('completed');
    const status = el.querySelector('.stage-status');
    if (status) status.textContent = 'Done';
  }
}

function setAllNodesDone() {
  STAGES.forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    if (el) {
      el.classList.remove('active');
      el.classList.add('completed');
      const status = el.querySelector('.stage-status');
      if (status) status.textContent = 'Done';
    }
  });
}
