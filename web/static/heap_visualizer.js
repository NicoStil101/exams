(function () {
  const keyInput = document.getElementById('heap-key');
  const insertBtn = document.getElementById('heap-insert-btn');
  const deleteBtn = document.getElementById('heap-delete-btn');
  const resetBtn = document.getElementById('heap-reset-btn');
  const errorEl = document.getElementById('heap-error');
  const keysEl = document.getElementById('heap-keys');
  const diagramEl = document.getElementById('heap-diagram');
  const traceEl = document.getElementById('heap-trace');

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
    keysEl.textContent = state.keys && state.keys.length ? 'Array: [' + state.keys.join(', ') + ']' : 'Heap is empty.';
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
    const res = await fetch('/api/heap/state');
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
    const res = await fetch('/api/heap/insert', {
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
    const res = await fetch('/api/heap/delete', {
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
    const res = await fetch('/api/heap/reset', { method: 'POST' });
    renderState(await res.json());
  }

  insertBtn.addEventListener('click', doInsert);
  deleteBtn.addEventListener('click', doDelete);
  resetBtn.addEventListener('click', doReset);
  keyInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doInsert();
  });

  refreshFromServer();
})();
