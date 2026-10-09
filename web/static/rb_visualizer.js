(function () {
  const keyInput = document.getElementById('rbv-key');
  const insertBtn = document.getElementById('rbv-insert-btn');
  const deleteBtn = document.getElementById('rbv-delete-btn');
  const resetBtn = document.getElementById('rbv-reset-btn');
  const errorEl = document.getElementById('rbv-error');
  const keysEl = document.getElementById('rbv-keys');
  const diagramEl = document.getElementById('rbv-diagram');
  const traceEl = document.getElementById('rbv-trace');
  const bulkInput = document.getElementById('rbv-bulk-input');
  const bulkBtn = document.getElementById('rbv-bulk-btn');

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function inlineMd(text) {
    return escapeHtml(text).replace(/`([^`]+?)`/g, '<code>$1</code>');
  }

  function renderState(state) {
    diagramEl.innerHTML = state.diagram || '';
    keysEl.textContent = state.keys && state.keys.length ? 'Keys: ' + state.keys.join(', ') : 'Tree is empty.';
    if (state.trace && state.trace.length) {
      traceEl.innerHTML = '<ol>' +
        state.trace
          .map((step) => (
            '<li>' + inlineMd(step.note) +
            (step.diagram ? '<div class="step-diagram">' + step.diagram + '</div>' : '') +
            '</li>'
          ))
          .join('') +
        '</ol>';
    } else {
      traceEl.innerHTML = '<p class="log-empty">No operation yet.</p>';
    }
  }

  function showError(msg) {
    errorEl.textContent = msg || '';
  }

  async function refreshFromServer() {
    const res = await fetch('/api/rbtree/state');
    renderState(await res.json());
  }

  function parseKey() {
    const raw = keyInput.value.trim();
    if (raw === '') return null;
    const n = parseInt(raw, 10);
    return Number.isNaN(n) ? null : n;
  }

  async function doInsert() {
    const key = parseKey();
    if (key === null) {
      showError('Enter an integer key first.');
      return;
    }
    const res = await fetch('/api/rbtree/insert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key }),
    });
    const data = await res.json();
    if (data.error) {
      showError(data.error);
      return;
    }
    showError('');
    keyInput.value = '';
    renderState(data);
  }

  async function doDelete() {
    const key = parseKey();
    if (key === null) {
      showError('Enter an integer key first.');
      return;
    }
    const res = await fetch('/api/rbtree/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key }),
    });
    const data = await res.json();
    if (data.error) {
      showError(data.error);
      return;
    }
    showError('');
    keyInput.value = '';
    renderState(data);
  }

  async function doReset() {
    showError('');
    const res = await fetch('/api/rbtree/reset', { method: 'POST' });
    renderState(await res.json());
  }

  async function doBulkLoad() {
    const text = bulkInput.value.trim();
    if (!text) {
      showError('Paste an array of integers first.');
      return;
    }
    const res = await fetch('/api/rbtree/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (data.error) {
      showError(data.error);
      return;
    }
    showError('');
    renderState(data);
  }

  insertBtn.addEventListener('click', doInsert);
  deleteBtn.addEventListener('click', doDelete);
  resetBtn.addEventListener('click', doReset);
  bulkBtn.addEventListener('click', doBulkLoad);
  keyInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doInsert();
  });

  refreshFromServer();
})();
