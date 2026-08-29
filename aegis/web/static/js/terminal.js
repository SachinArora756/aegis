/* Aegis Dashboard — Terminal Emulator */

class Terminal {
  constructor(elementId) {
    this.el = document.getElementById(elementId);
    this.cursorEl = null;
    if (!this.el) console.error(`Terminal: element #${elementId} not found`);
  }

  clear() {
    if (this.el) this.el.innerHTML = '';
    this.cursorEl = null;
  }

  writeLine(text, style = 'step') {
    if (!this.el) return;
    this._removeCursor();

    if (style === 'divider') {
      const div = document.createElement('div');
      div.className = 'term-divider';
      this.el.appendChild(div);
      this.scrollToBottom();
      return;
    }

    const line = document.createElement('div');
    line.className = `term-line term-${style}`;
    line.textContent = text;
    this.el.appendChild(line);
    this.scrollToBottom();
  }

  writeBox(lines) {
    if (!this.el) return;
    this._removeCursor();
    const box = document.createElement('div');
    box.className = 'term-box';
    lines.forEach(l => {
      const ln = document.createElement('div');
      ln.className = 'term-line term-box-line';
      ln.textContent = l;
      box.appendChild(ln);
    });
    this.el.appendChild(box);
    this.scrollToBottom();
  }

  writeHtml(html) {
    if (!this.el) return;
    this._removeCursor();
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    this.el.appendChild(wrapper);
    this.scrollToBottom();
  }

  showCursor() {
    if (!this.el || this.cursorEl) return;
    this.cursorEl = document.createElement('span');
    this.cursorEl.className = 'terminal-cursor';
    this.cursorEl.innerHTML = '&nbsp;';
    const wrap = document.createElement('div');
    wrap.className = 'term-line';
    wrap.appendChild(this.cursorEl);
    this.el.appendChild(wrap);
    this.scrollToBottom();
  }

  hideCursor() {
    this._removeCursor();
  }

  _removeCursor() {
    if (this.cursorEl) {
      const parent = this.cursorEl.parentElement;
      if (parent) parent.remove();
      this.cursorEl = null;
    }
  }

  scrollToBottom() {
    if (this.el) {
      this.el.scrollTop = this.el.scrollHeight;
    }
  }
}
